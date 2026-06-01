#!/usr/bin/env python3
import html
import http.client
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pymysql

from rail_common import (
    claim_digest,
    claim_proof,
    execute,
    one,
    random_id,
    read_json,
    redis,
    rows,
    send_html,
    send_json,
    wait_for_db,
    wait_for_redis,
)


def publish_profile(station_code):
    row = one(
        """
        SELECT station_code,station_name,batch_open,renderer_profile,notice_profile,signer_route,policy_hint,updated_at
        FROM station_profiles WHERE station_code=%s
        """,
        (station_code,),
    )
    if not row:
        return None
    profile = {
        "stationCode": row["station_code"],
        "stationName": row["station_name"],
        "batchOpen": bool(row["batch_open"]),
        "rendererProfile": row["renderer_profile"],
        "noticeProfile": row["notice_profile"],
        "signerRoute": row["signer_route"],
        "updatedAt": int(row["updated_at"]),
    }
    redis.command("SET", f"rail:station:profile-cache:{station_code}", json.dumps(profile, separators=(",", ":")), "EX", 240)
    return profile


def notice_fragment(station_code, hint):
    if "\r" not in hint and "\n" not in hint:
        return
    redis.command("SET", f"rail:notice:feed-dirty:{station_code}", "1", "EX", 240)


def fare_scope_expression(scope):
    fields = {
        "ticket": "ticket_no",
        "passenger": "passenger",
        "train": "train_id",
        "station": "station_code",
        "state": "status",
    }
    if isinstance(scope, str):
        return fields.get(scope, "ticket_no")
    if not isinstance(scope, dict):
        return "ticket_no"
    if scope.get("mode") == "legacy-rank":
        return str(scope.get("expr", "ticket_no"))[:240]
    key = str(scope.get("key", "ticket"))[:32]
    direction = "DESC" if scope.get("desc") else "ASC"
    if key in fields:
        return f"{fields[key]} {direction}"
    return "ticket_no"


class StationHandler(BaseHTTPRequestHandler):
    server_version = "StationOffice/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/station-office/", "/station-office"}:
            self.page()
            return

        if parsed.path == "/api/station-office/notices":
            self.list_notices()
            return

        if parsed.path == "/api/station-office/tickets/search":
            self.search_tickets(parsed)
            return

        if parsed.path == "/api/station-office/reconciliation/metadata":
            profile = publish_profile(parse_qs(parsed.query).get("stationCode", ["BJP"])[0][:16])
            send_json(self, 200, {"station": profile, "generatedAt": int(time.time())})
            return

        send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return

        if parsed.path == "/api/station-office/notices":
            self.create_notice(data)
            return

        if parsed.path == "/api/station-office/tickets/adjust":
            self.adjust_ticket(data)
            return

        if parsed.path == "/api/station-office/fares/reprice":
            self.reprice_fare(data)
            return

        if parsed.path == "/api/station-office/health/import":
            self.health_import(data)
            return

        if parsed.path == "/api/station-office/reconciliation/metadata":
            profile = publish_profile(str(data.get("stationCode", "BJP"))[:16])
            send_json(self, 202, {"station": profile})
            return

        send_json(self, 404, {"error": "not_found"})

    def page(self):
        notices = rows("SELECT title,body FROM station_notices ORDER BY created_at DESC LIMIT 8")
        items = "".join(
            f"<li><strong>{html.escape(row['title'])}</strong><span>{html.escape(row['body'])}</span></li>"
            for row in notices
        )
        send_html(self, 200, (
            "<!doctype html><meta charset='utf-8'><title>Station Office</title>"
            "<style>body{font-family:system-ui;margin:32px;color:#1f2937}li{margin:12px 0}span{display:block;color:#64748b}</style>"
            "<h1>Station Office</h1><ul>" + (items or "<li>No posted notices</li>") + "</ul>"
        ))

    def list_notices(self):
        notices = []
        for row in rows("SELECT slug,title,body,created_at FROM station_notices ORDER BY created_at DESC LIMIT 12"):
            notices.append({
                "slug": row["slug"],
                "title": row["title"],
                "body": row["body"],
                "createdAt": int(row["created_at"]),
            })
        send_json(self, 200, {"notices": notices})

    def create_notice(self, data):
        station_code = str(data.get("stationCode", "BJP"))[:16]
        title = str(data.get("title", "Station notice"))[:160]
        body = str(data.get("body", ""))[:1600]
        hint = str(data.get("proxyHint", ""))
        slug = random_id("N", 8)
        execute(
            """
            INSERT INTO station_notices(slug,station_code,title,body,proxy_hint,created_at)
            VALUES(%s,%s,%s,%s,%s,%s)
            """,
            (slug, station_code, title, body, hint, int(time.time())),
        )
        notice_fragment(station_code, hint)
        send_json(self, 201, {"notice": {"slug": slug, "title": title, "body": body}})

    def search_tickets(self, parsed):
        q = parse_qs(parsed.query).get("q", [""])[0][:240]
        requested = parse_qs(parsed.query).get("sort", ["ticket_no"])[0]
        order_by = requested if requested in {"ticket_no", "passenger", "train_id", "station_code", "status"} else "ticket_no"
        sql = (
            "SELECT ticket_no,passenger,train_id,station_code,status FROM ticket_index "
            "WHERE ticket_no LIKE %s OR passenger LIKE %s "
            f"ORDER BY {order_by} LIMIT 20"
        )
        try:
            result = rows(sql, (f"%{q}%", f"%{q}%"))
        except pymysql.MySQLError as exc:
            send_json(self, 400, {"error": "search_failed"})
            return
        send_json(self, 200, {"tickets": [{
            "ticketNo": row["ticket_no"],
            "passenger": row["passenger"],
            "trainId": row["train_id"],
            "stationCode": row["station_code"],
            "status": row["status"],
        } for row in result]})

    def reprice_fare(self, data):
        station_code = str(data.get("stationCode", "BJP"))[:16]
        scope = fare_scope_expression(data.get("tariffScope", "ticket"))
        try:
            amount = abs(int(data.get("amount", 0) or 0)) % 900
        except (TypeError, ValueError):
            amount = 0
        sql = (
            "SELECT ticket_no,station_code,status FROM ticket_index "
            "WHERE station_code IN (%s,'BJP') "
            f"ORDER BY {scope} LIMIT 1"
        )
        try:
            row = one(sql, (station_code,))
        except pymysql.MySQLError:
            send_json(self, 202, {
                "quote": {"status": "manual_review", "bucket": "fare-review", "amount": amount},
            })
            return
        bucket = "north-window" if row and str(row.get("ticket_no", "")).startswith("T-BJP-") else "local-window"
        send_json(self, 200, {
            "quote": {
                "status": "priced",
                "stationCode": station_code,
                "bucket": bucket,
                "amount": amount,
                "expiresIn": 90,
            }
        })

    def adjust_ticket(self, data):
        ticket_no = str(data.get("ticketNo", ""))[:240]
        memo = str(data.get("memo", ""))[:1800]
        submitted_proof = str(data.get("claimProof", ""))[:96]
        ticket = one("SELECT ticket_no FROM ticket_index WHERE ticket_no=%s", (ticket_no,))
        if not ticket:
            send_json(self, 404, {"error": "ticket_not_found"})
            return
        artifact = one(
            """
            SELECT order_id,station_code,train_id,claim_salt,claim_digest FROM station_claim_artifacts
            WHERE ticket_no=%s AND expires_at>%s
            ORDER BY issued_at DESC LIMIT 1
            """,
            (ticket_no, int(time.time())),
        )
        if not artifact:
            send_json(self, 409, {"error": "binding_review"})
            return
        expected_digest = claim_digest(
            artifact["order_id"],
            artifact["train_id"],
            artifact["station_code"],
            ticket_no,
            artifact["claim_salt"],
        )
        expected_proof = claim_proof(
            artifact["order_id"],
            artifact["train_id"],
            artifact["station_code"],
            ticket_no,
            artifact["claim_salt"],
            artifact["claim_digest"],
        )
        if artifact["claim_digest"] != expected_digest or submitted_proof != expected_proof:
            send_json(self, 409, {"error": "binding_review"})
            return
        try:
            delta = int(data.get("delta", 0))
        except (TypeError, ValueError):
            delta = 0
        created_at = int(time.time())
        try:
            execute(
                """
                INSERT INTO ticket_adjustments(ticket_no,claim_proof,memo,delta,created_at)
                VALUES(%s,%s,%s,%s,%s)
                """,
                (ticket_no, submitted_proof, memo, delta, created_at),
            )
        except pymysql.MySQLError as exc:
            send_json(self, 400, {"error": "adjustment_failed"})
            return
        profile = publish_profile(artifact["station_code"])
        send_json(self, 202, {"status": "adjustment_recorded", "station": profile})

    def health_import(self, data):
        body = json.dumps(data, separators=(",", ":"))
        try:
            conn = http.client.HTTPConnection("127.0.0.1", int(os.environ.get("IMPORT_PORT", "5008")), timeout=3)
            conn.request("POST", "/station/import/probe", body=body, headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            payload = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except OSError as exc:
            send_json(self, 502, {"error": "import_adapter_unavailable", "detail": str(exc)[:120]})


def main():
    wait_for_db()
    wait_for_redis()
    publish_profile("BJP")
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5003"))
    server = ThreadingHTTPServer((host, port), StationHandler)
    print(f"station portal on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
