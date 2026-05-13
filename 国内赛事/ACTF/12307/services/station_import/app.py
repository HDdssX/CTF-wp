#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rail_common import (
    claim_proof,
    execute,
    one,
    random_id,
    read_json,
    redis,
    rows,
    safe_json,
    send_json,
    station_policy,
    truthy,
    wait_for_db,
    wait_for_redis,
)


def feed_headers(text):
    parsed = {}
    for raw in str(text or "").replace("\r\n", "\n").split("\n"):
        if ":" not in raw:
            continue
        name, value = raw.split(":", 1)
        parsed[name.strip().lower()] = value.strip()
    return parsed


def compile_notice_feed(station_code):
    _profile, policy = station_policy(station_code)
    notice = policy.get("notice") if isinstance(policy.get("notice"), dict) else {}
    board = policy.get("board") if isinstance(policy.get("board"), dict) else {}
    lane_header = str(notice.get("laneHeader", "")).lower()
    lane_value = str(notice.get("laneValue", "")).lower()
    stream_header = str(notice.get("streamHeader", "")).lower()
    stream_value = str(notice.get("streamValue", "")).lower()
    hints = rows(
        """
        SELECT proxy_hint FROM station_notices
        WHERE station_code=%s ORDER BY created_at DESC LIMIT 6
        """,
        (station_code,),
    )
    feed = "\r\n".join(str(row["proxy_hint"]) for row in hints)
    headers = feed_headers(feed)
    lane_match = lane_header and headers.get(lane_header) and headers.get(lane_header, "").lower() == lane_value
    stream_match = stream_header and headers.get(stream_header) and headers.get(stream_header, "").lower() == stream_value
    if lane_match:
        redis.command("SET", f"rail:interline:lane:{station_code}", json.dumps({
            "routeName": policy.get("routeName", "public"),
            "issuedAt": int(time.time()),
        }, separators=(",", ":")), "EX", "240")
        if stream_match:
            redis.command("SET", f"rail:board:profile:{station_code}", json.dumps({
                "streamValue": board.get("streamValue", notice.get("streamValue", "")),
                "topic": board.get("topic", "seat-consist"),
                "transport": board.get("transport", "boarding-monitor"),
                "ack": board.get("ack", "carriage-confirmed"),
                "issuedAt": int(time.time()),
            }, separators=(",", ":")), "EX", "240")
        key_id_header = str(notice.get("keyIdHeader", "X-Desk-Key-Id")).lower()
        key_header = str(notice.get("keyHeader", "X-Desk-Key")).lower()
        key_id = headers.get(key_id_header, "")
        registry_hint = headers.get(key_header, "")
        policy_row = one(
            """
            SELECT policy_id,secret_key,route_name FROM signer_policies
            WHERE station_code=%s AND route_name=%s AND policy_id=%s AND enabled=1
            LIMIT 1
            """,
            (station_code, str(policy.get("routeName", "public")), key_id[:32]),
        ) if key_id else None
        if policy_row and registry_hint == policy_row["route_name"]:
            redis.command("SET", f"rail:partner:jwks:{station_code}", json.dumps({
                "kid": policy_row["policy_id"],
                "key": policy_row["secret_key"],
                "routeName": policy_row["route_name"],
                "issuedAt": int(time.time()),
            }, separators=(",", ":")), "EX", "240")
    return {"status": "accepted", "key": "station-feed"}


def claim_artifact(order_id, station_code):
    return one(
        """
        SELECT a.ticket_no,a.claim_salt,a.claim_digest,a.train_id
        FROM station_claim_artifacts a
        WHERE a.order_id=%s AND a.station_code=%s AND a.expires_at>%s
        """,
        (order_id, station_code, int(time.time())),
    )


def claim_document(rule):
    line_items = rule.get("lineItems")
    if isinstance(line_items, dict):
        return line_items
    if isinstance(line_items, list):
        for item in line_items:
            if isinstance(item, dict) and item.get("role") == "settlement-layout":
                return item
    return {}


def apply_adjustment_rules(order_id, station_code):
    artifact = claim_artifact(order_id, station_code)
    if not artifact:
        return {"status": "accepted", "key": "desk-ledger"}
    expected_proof = claim_proof(
        order_id,
        artifact["train_id"],
        station_code,
        artifact["ticket_no"],
        artifact["claim_salt"],
        artifact["claim_digest"],
    )
    _profile, policy = station_policy(station_code)
    claim = policy.get("claim") if isinstance(policy.get("claim"), dict) else {}
    layout_policy = policy.get("layout") if isinstance(policy.get("layout"), dict) else {}
    layout_name = str(policy.get("layoutClass", "standard"))[:48]
    route_name = str(policy.get("routeName", "public"))[:48]
    grant_code = str(policy.get("grantCode", "plain"))[:64]
    expected_channel = str(claim.get("channel", "fare-desk"))
    expected_reason = str(claim.get("reason", ""))
    expected_device = str(layout_policy.get("device", ""))
    expected_cell = str(layout_policy.get("cell", "receipt"))[:48]
    candidates = rows(
        """
        SELECT id,memo,claim_proof FROM ticket_adjustments
        WHERE ticket_no=%s AND claim_proof=%s
        ORDER BY id DESC LIMIT 8
        """,
        (artifact["ticket_no"], expected_proof),
    )
    applied = 0
    for item in candidates:
        if one("SELECT id FROM station_rule_applications WHERE adjustment_id=%s", (item["id"],)):
            continue
        rule = safe_json(item["memo"], {}) or {}
        if not isinstance(rule, dict):
            continue
        if str(rule.get("stationCode", station_code))[:16] != station_code:
            continue
        if str(rule.get("channel", "")) != expected_channel:
            continue
        document = claim_document(rule)
        if str(document.get("reason", "")) != expected_reason:
            continue
        if str(document.get("layout", ""))[:48] != layout_name:
            continue
        device_ref = str(document.get("device", ""))[:64]
        if device_ref != expected_device:
            continue
        execute(
            """
            UPDATE waitlist_entries
            SET sampled=1,sample_origin=%s,updated_at=%s
            WHERE order_id=%s AND station_code=%s
            """,
            ("station-rule-compiler", int(time.time()), order_id, station_code),
        )
        execute(
            """
            UPDATE station_profiles
            SET batch_open=1,renderer_profile=%s,signer_route=%s,updated_at=%s
            WHERE station_code=%s
            """,
            (layout_name, route_name, int(time.time()), station_code),
        )

        if truthy(document.get("enabled", True)):
            execute(
                """
                INSERT INTO tariff_exception_claims(order_id,station_code,layout_name,cell_name,entitlement_code,device_ref,claim_state,updated_at)
                VALUES(%s,%s,%s,%s,%s,%s,'compiled',%s)
                ON DUPLICATE KEY UPDATE layout_name=VALUES(layout_name),entitlement_code=VALUES(entitlement_code),
                    device_ref=VALUES(device_ref),claim_state='compiled',updated_at=VALUES(updated_at)
                """,
                (
                    order_id,
                    station_code,
                    layout_name,
                    expected_cell,
                    grant_code,
                    device_ref,
                    int(time.time()),
                ),
            )

        execute(
            """
            INSERT INTO station_rule_applications(adjustment_id,order_id,station_code,rule_state,applied_at)
            VALUES(%s,%s,%s,'applied',%s)
            """,
            (item["id"], order_id, station_code, int(time.time())),
        )
        applied += 1
    return {"status": "accepted", "key": "desk-ledger", "applied": applied}


def activate_layout_claim(order_id, station_code):
    claims = rows(
        """
        SELECT order_id,station_code,layout_name,cell_name,entitlement_code,device_ref
        FROM tariff_exception_claims
        WHERE order_id=%s AND station_code=%s AND claim_state IN ('compiled','entitled')
        ORDER BY updated_at DESC LIMIT 4
        """,
        (order_id, station_code),
    )
    applied = 0
    for claim in claims:
        execute(
            """
            INSERT INTO bureau_layout_cells(station_code,layout_name,cell_name,input_class,device_ref,enabled,updated_at)
            VALUES(%s,%s,%s,%s,%s,1,%s)
            ON DUPLICATE KEY UPDATE input_class=VALUES(input_class),device_ref=VALUES(device_ref),
                enabled=1,updated_at=VALUES(updated_at)
            """,
            (
                claim["station_code"],
                claim["layout_name"],
                claim["cell_name"],
                "service-device",
                claim["device_ref"],
                int(time.time()),
            ),
        )
        execute(
            "UPDATE tariff_exception_claims SET claim_state='entitled',updated_at=%s WHERE order_id=%s AND station_code=%s AND cell_name=%s",
            (int(time.time()), order_id, station_code, claim["cell_name"]),
        )
        applied += 1
    if applied:
        redis.command("SET", f"rail:layout:entitlement:{order_id}", station_code, "EX", "180")
    return {"status": "accepted", "key": "layout-clearing", "applied": applied}


def cache_probe(target, payload, adapter, station_hint):
    parsed = urlparse(target)
    q = parse_qs(parsed.query)
    order_id = (q.get("orderId") or [""])[0][:32]
    station_code = (q.get("stationCode") or [station_hint or "BJP"])[0][:16]
    batch_id = (q.get("batchId") or [""])[0][:32]
    session_id = (q.get("sessionId") or [""])[0][:64]
    path = parsed.path.strip("/")
    adapter = str(adapter or "")[:64]

    if adapter == "fulfillment-monitor" and order_id:
        redis.command("SET", f"rail:fulfillment:epoch:{order_id}", "boarding", "EX", "8")
        return {"status": "accepted", "key": "fulfillment-window"}

    if adapter == "fare-cache-warm" and order_id:
        redis.command("SET", f"rail:fare:sample-cache:{order_id}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "fare-sample"}

    if adapter == "station-desk-ledger" and order_id:
        return apply_adjustment_rules(order_id, station_code)

    if adapter == "enterprise-clearing" and order_id:
        return activate_layout_claim(order_id, station_code)

    if adapter == "station-profile-preview":
        lower = payload.lower()
        redis.command("SET", f"rail:station:profile-observed:{station_code}", lower[:160], "EX", "240")
        return {"status": "accepted", "key": "profile-observed"}

    if adapter == "receipt-staging" and batch_id:
        redis.command("SET", f"rail:receipt:staging:{batch_id}", payload[:1200], "EX", "240")
        return {"status": "accepted", "key": "receipt-staging"}

    if adapter == "partner-review" and session_id:
        redis.command("SET", f"rail:partner:review:{session_id}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "partner-review"}

    if adapter == "station-partner-feed":
        return compile_notice_feed(station_code)

    if adapter == "refund-window-review":
        redis.command("SET", f"rail:refund:review:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "refund-review"}

    if adapter == "seat-change-roster":
        redis.command("SET", f"rail:seat-change:roster:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "seat-change"}

    if adapter == "incident-roster-feed":
        redis.command("SET", f"rail:incident:lane:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "incident-roster"}

    if adapter == "baggage-transfer-bay":
        redis.command("SET", f"rail:baggage:handoff:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "baggage-handoff"}

    if adapter == "invoice-dispute-review":
        redis.command("SET", f"rail:invoice:dispute:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "invoice-dispute"}

    if adapter == "voucher-clearance-preview":
        redis.command("SET", f"rail:voucher:preview:{station_code}", payload[:800], "EX", "240")
        return {"status": "accepted", "key": "voucher-preview"}

    return {"status": "accepted", "key": "queued"}


class ImportHandler(BaseHTTPRequestHandler):
    server_version = "StationImport/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return
        if parsed.path != "/station/import/probe":
            send_json(self, 404, {"error": "not_found"})
            return

        target = str(data.get("target", "rail-cache://redis/partner/metadata?stationCode=BJP"))[:255]
        payload = str(data.get("payload", data.get("body", "")))[:1600]
        station_code = str(data.get("stationCode", "BJP"))[:16]
        adapter = str(data.get("adapter", "station-health"))[:64]
        import_id = random_id("I", 10)
        result = cache_probe(target, payload, adapter, station_code)
        execute(
            """
            INSERT INTO import_batches(import_id,station_code,adapter,target_uri,status,cached_reply,created_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                import_id,
                station_code,
                adapter,
                target,
                result["status"],
                json.dumps(result, separators=(",", ":")),
                int(time.time()),
            ),
        )
        send_json(self, 200, {"importId": import_id, "status": result.get("status", "accepted")})


def main():
    wait_for_db()
    wait_for_redis()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5008"))
    server = ThreadingHTTPServer((host, port), ImportHandler)
    print(f"station import adapter on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
