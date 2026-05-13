#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rail_common import (
    digest_template,
    execute,
    one,
    random_id,
    read_json,
    receipt_payload,
    redis,
    send_json,
    sign_receipt,
    wait_for_db,
    wait_for_redis,
)


BASE_FARES = {
    "G1021": 553,
    "G7137": 117,
    "G8829": 154,
    "G4015": 75,
    "G7608": 214,
}

REPORT_TEMPLATES = {
    "fare-preview": "Fare sample {{orderId}} {{status}} {{data.carrier}}",
    "invoice-audit": "Invoice audit {{orderId}} {{trainId}} {{status}}",
    "carrier-closeout": "Reconciliation {{orderId}} {{status}} {{reconciliation.receipt}}",
}


def create_plain_receipt(batch_id, order, template_digest):
    existing = one("SELECT receipt_id FROM settlement_receipts WHERE batch_id=%s", (batch_id,))
    if existing:
        return existing["receipt_id"]
    policy = one(
        "SELECT * FROM signer_policies WHERE station_code=%s AND route_name='public' AND enabled=1 LIMIT 1",
        (order["station_code"],),
    )
    if not policy:
        return None
    nonce = random_id("N", 16)
    now = int(time.time())
    expires = now + 900
    execute(
        "INSERT INTO receipt_nonces(nonce,station_code,order_id,used,expires_at) VALUES(%s,%s,%s,1,%s)",
        (nonce, order["station_code"], order["order_id"], expires),
    )
    receipt_id = random_id("R", 12)
    payload = receipt_payload(
        batch_id,
        order["order_id"],
        order["station_code"],
        "public-fare-sample",
        template_digest,
        nonce,
        policy["policy_id"],
        policy["render_grant"],
        expires,
    )
    signature = sign_receipt(policy["secret_key"], payload)
    execute(
        """
        INSERT INTO settlement_receipts(receipt_id,batch_id,order_id,station_code,trust_id,template_digest,nonce,policy_id,
            render_grant,signature,status,created_at,expires_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'accepted',%s,%s)
        """,
        (
            receipt_id,
            batch_id,
            order["order_id"],
            order["station_code"],
            "public-fare-sample",
            template_digest,
            nonce,
            policy["policy_id"],
            policy["render_grant"],
            signature,
            now,
            expires,
        ),
    )
    return receipt_id


class FareHandler(BaseHTTPRequestHandler):
    server_version = "FareSampler/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/fare-samples/quote":
            q = parse_qs(parsed.query)
            train_id = q.get("trainId", ["G1021"])[0]
            seat_class = q.get("seatClass", ["second"])[0]
            base = BASE_FARES.get(train_id, 180)
            multiplier = {"business": 2.7, "first": 1.45, "second": 1.0}.get(seat_class, 1.0)
            send_json(self, 200, {
                "trainId": train_id,
                "seatClass": seat_class,
                "fare": round(base * multiplier, 2),
                "sampledAt": int(time.time()),
            })
            return

        if parsed.path.startswith("/api/fare-samples/reconciliation/"):
            batch_id = parsed.path.rsplit("/", 1)[-1]
            report = one(
                "SELECT batch_id,ready,reasons,body,finished_at FROM render_results WHERE batch_id=%s",
                (batch_id,),
            )
            if report:
                report = {
                    "batchId": report["batch_id"],
                    "ready": bool(report["ready"]),
                    "reasons": json.loads(report["reasons"]),
                    "body": report["body"],
                    "finishedAt": int(report["finished_at"]),
                }
            send_json(self, 200, {"batchId": batch_id, "report": report})
            return

        send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return

        if parsed.path == "/api/fare-samples/reconciliation":
            self.create_batch(data)
            return

        send_json(self, 404, {"error": "not_found"})

    def create_batch(self, data):
        order_id = str(data.get("orderId", ""))[:32]
        order = one("SELECT * FROM orders WHERE order_id=%s", (order_id,))
        if not order:
            send_json(self, 404, {"error": "order_not_found"})
            return

        station_code = str(data.get("stationCode", order["station_code"]))[:16]
        batch_id = str(data.get("batchId") or random_id("B", 10))[:32]
        report_type = str(data.get("reportType", "fare-preview"))[:48]
        template = REPORT_TEMPLATES.get(report_type, REPORT_TEMPLATES["fare-preview"])
        template_digest = digest_template(template)
        now = int(time.time())
        receipt_id = None
        if not data.get("defer"):
            receipt_id = create_plain_receipt(batch_id, order, template_digest)
        execute(
            """
            INSERT INTO render_jobs(batch_id,receipt_id,order_id,station_code,template_digest,template_body,data_json,status,created_at,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s)
            ON DUPLICATE KEY UPDATE receipt_id=COALESCE(VALUES(receipt_id),receipt_id),template_digest=VALUES(template_digest),
                template_body=VALUES(template_body),data_json=VALUES(data_json),status='pending',updated_at=VALUES(updated_at)
            """,
            (
                batch_id,
                receipt_id,
                order_id,
                station_code,
                template_digest,
                template,
                json.dumps(data.get("data") if isinstance(data.get("data"), dict) else {}, separators=(",", ":")),
                now,
                now,
            ),
        )
        if not data.get("defer"):
            redis.command("LPUSH", "rail:scheduler:jobs", json.dumps({"batchId": batch_id, "origin": "fare-sampler"}))
        send_json(self, 202, {
            "batchId": batch_id,
            "status": "pending" if data.get("defer") else "queued",
            "orderId": order_id,
            "templateDigest": template_digest,
        })


def main():
    wait_for_db()
    wait_for_redis()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5004"))
    server = ThreadingHTTPServer((host, port), FareHandler)
    print(f"fare sampler on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
