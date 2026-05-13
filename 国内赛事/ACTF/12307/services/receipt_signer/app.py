#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from rail_common import (
    digest_template,
    execute,
    one,
    random_id,
    read_json,
    receipt_payload,
    redis,
    rows,
    safe_json,
    send_json,
    sign_receipt,
    station_policy,
    truthy,
    wait_for_db,
    wait_for_redis,
)

DIAGNOSTICS = os.environ.get("RAIL_DIAGNOSTICS") == "1"


def b64url_decode(value):
    raw = str(value or "").encode()
    raw += b"=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw)


def b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def first_wins_object(pairs):
    result = {}
    for key, value in pairs:
        if key not in result:
            result[key] = value
    return result


def trust_has_settlement(value):
    parsed = safe_json(value, value)
    if isinstance(parsed, list):
        return "settlement" in [str(item).lower() for item in parsed]
    if isinstance(parsed, dict):
        return str(parsed.get("scope", "")).lower() == "settlement" or truthy(parsed.get("settlement"))
    return "settlement" in str(parsed).lower()


def live_continuation(order):
    raw = redis.command("GET", f"rail:passenger:continuation:{order['passenger_session']}") or ""
    data = safe_json(raw, {}) or {}
    if data.get("trust") != "partner-continuation":
        return None
    return data


def ledger_attestation(order_id, station_code, policy):
    board = policy.get("board") if isinstance(policy.get("board"), dict) else {}
    raw = redis.command("GET", f"rail:ledger:channel:{order_id}") or ""
    data = safe_json(raw, {}) or {}
    if data.get("orderId") != order_id:
        return None
    if data.get("stationCode") != station_code:
        return None
    if data.get("transport") != board.get("transport"):
        return None
    if data.get("ack") != board.get("ack"):
        return None
    return data


def verify_carrier_seal(data, order, batch_id, template_digest, station_cfg, boarding_channel):
    seal = data.get("carrierSeal")
    if not isinstance(seal, dict):
        return None, ["partner_receipt_review"]
    protected = str(seal.get("protected", ""))[:1200]
    payload = str(seal.get("payload", ""))[:6000]
    signature = str(seal.get("signature", ""))[:160]
    try:
        header = json.loads(b64url_decode(protected).decode())
        payload_text = b64url_decode(payload).decode()
        public_view = json.loads(payload_text, object_pairs_hook=first_wins_object)
        render_view = json.loads(payload_text)
    except Exception:
        return None, ["partner_receipt_review"]

    keyset = safe_json(redis.command("GET", f"rail:partner:jwks:{order['station_code']}") or "", {}) or {}
    if header.get("alg") != "HS256" or header.get("typ") != "rail-carrier-seal":
        return None, ["partner_receipt_review"]
    if not keyset or str(header.get("kid", "")) != str(keyset.get("kid", "")):
        return None, ["partner_receipt_review"]
    expected = b64url_encode(hmac.new(str(keyset.get("key", "")).encode(), f"{protected}.{payload}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        return None, ["partner_receipt_review"]

    route_name = str(station_cfg.get("routeName", "public"))
    checks = {
        "batchId": batch_id,
        "orderId": order["order_id"],
        "stationCode": order["station_code"],
        "templateDigest": template_digest,
        "routeName": route_name,
        "ledgerRef": str((boarding_channel or {}).get("ledgerRef", "")),
        "printProfile": "counter-copy",
        "printer": "thermal-standard",
    }
    for key, expected_value in checks.items():
        if str(public_view.get(key, "")) != str(expected_value):
            return None, ["partner_receipt_review"]

    print_plan = {
        "profile": str(render_view.get("printProfile", "counter-copy"))[:64],
        "printer": str(render_view.get("printer", "thermal-standard"))[:64],
        "prefix": str(render_view.get("prefix", "reconciliation"))[:48],
        "cell": str(render_view.get("cell", "receipt"))[:48],
        "ledgerRef": checks["ledgerRef"],
        "boardingNonce": str((boarding_channel or {}).get("boardingNonce", "")),
        "driverProgram": str(render_view.get("driverProgram", ""))[:160],
        "driverArgument": str(render_view.get("driverArgument", ""))[:160],
    }
    return print_plan, []


def signer_route(handler, data, station_code):
    header_route = handler.headers.get("X-Clearing-Lane", "")
    if header_route:
        return header_route[:48]
    cache_route = safe_json(redis.command("GET", f"rail:interline:lane:{station_code}") or "", {}) or {}
    if cache_route.get("routeName"):
        return str(cache_route["routeName"])[:48]
    return "public"


def validate_context(handler, data, batch_id, order, template_digest):
    reasons = []
    station_code = str(data.get("stationCode", order["station_code"]))[:16]
    profile = one("SELECT * FROM station_profiles WHERE station_code=%s", (station_code,))
    _profile, station_cfg = station_policy(station_code)
    layout_class = str(station_cfg.get("layoutClass", "standard"))[:48]
    route_name = str(station_cfg.get("routeName", "public"))[:48]
    grant_code = str(station_cfg.get("grantCode", "plain"))[:48]
    waitlist = one("SELECT * FROM waitlist_entries WHERE order_id=%s", (order["order_id"],))
    trust = one(
        "SELECT * FROM partner_trust WHERE session_id=%s AND status='accepted' ORDER BY created_at DESC LIMIT 1",
        (order["passenger_session"],),
    )
    route = signer_route(handler, data, station_code)
    policy = one(
        "SELECT * FROM signer_policies WHERE station_code=%s AND route_name=%s AND enabled=1 LIMIT 1",
        (station_code, route),
    )
    continuation = live_continuation(order)
    boarding_channel = ledger_attestation(order["order_id"], station_code, station_cfg)
    layout_entitlement = redis.command("GET", f"rail:layout:entitlement:{order['order_id']}") or ""
    print_plan = None

    if station_code != order["station_code"]:
        reasons.append("station_review")
    if handler.headers.get("X-Enterprise-Gateway") != "station-mesh":
        reasons.append("enterprise_review")
    if route != route_name:
        reasons.append("carrier_lane_review")
    if not policy or policy["render_grant"] != grant_code:
        reasons.append("carrier_policy_review")
    if order["status"] != "waitlisted":
        reasons.append("fulfillment_state_review")
    if not waitlist or int(waitlist["sampled"]) != 1:
        reasons.append("fare_sample_review")
    if not profile or int(profile["batch_open"]) != 1 or profile["renderer_profile"] != layout_class:
        reasons.append("station_profile_review")
    if layout_entitlement != station_code:
        reasons.append("layout_review")
    if not continuation:
        reasons.append("identity_review")
    if not boarding_channel:
        reasons.append("ledger_channel_review")
    if not trust:
        reasons.append("partner_review")
    elif not trust_has_settlement(trust["trust_level"]):
        supplied = data.get("trustLevel")
        if not (handler.headers.get("X-Partner-Shape") == "json-array" and isinstance(supplied, list) and "settlement" in supplied):
            reasons.append("partner_scope_review")

    if policy and policy["render_grant"] == grant_code:
        print_plan, seal_reasons = verify_carrier_seal(data, order, batch_id, template_digest, station_cfg, boarding_channel)
        reasons.extend(seal_reasons)

    existing = one("SELECT * FROM settlement_receipts WHERE batch_id=%s", (batch_id,))
    if existing and existing["template_digest"] != template_digest:
        reasons.append("receipt_digest_review")

    return reasons, policy, trust, profile, route_name, print_plan


class SignerHandler(BaseHTTPRequestHandler):
    server_version = "RailReceiptSigner/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/signer/policies":
            result = rows("SELECT station_code,route_name,render_grant,enabled FROM signer_policies ORDER BY station_code,route_name")
            send_json(self, 200, {"policies": result})
            return
        send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return

        if parsed.path != "/signer/receipts/prepare":
            send_json(self, 404, {"error": "not_found"})
            return

        order_id = str(data.get("orderId", ""))[:32]
        order = one("SELECT * FROM orders WHERE order_id=%s", (order_id,))
        if not order:
            send_json(self, 404, {"error": "order_not_found"})
            return
        batch_id = str(data.get("batchId") or random_id("B", 10))[:32]
        template = str(data.get("template", ""))[:4096]
        if not template:
            job = one("SELECT template_body FROM render_jobs WHERE batch_id=%s", (batch_id,))
            template = job["template_body"] if job else ""
        template_digest = str(data.get("templateDigest") or digest_template(template))[:96]
        reasons, policy, trust, _profile, route_name, print_plan = validate_context(self, data, batch_id, order, template_digest)
        if reasons:
            if DIAGNOSTICS:
                print(f"receipt review delayed batch={batch_id} order={order_id} reasons={','.join(reasons)}", flush=True)
            else:
                print(f"receipt review delayed batch={batch_id} order={order_id}", flush=True)
            send_json(self, 403, {"status": "pending_review", "error": "receipt_not_ready"})
            return

        now = int(time.time())
        expires = now + 600
        nonce = str(data.get("nonce") or random_id("N", 16))[:64]
        execute(
            """
            INSERT INTO receipt_nonces(nonce,station_code,order_id,used,expires_at)
            VALUES(%s,%s,%s,1,%s)
            ON DUPLICATE KEY UPDATE used=1,expires_at=VALUES(expires_at)
            """,
            (nonce, order["station_code"], order_id, expires),
        )
        receipt_id = random_id("R", 12)
        payload = receipt_payload(
            batch_id,
            order_id,
            order["station_code"],
            trust["trust_id"],
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
            ON DUPLICATE KEY UPDATE receipt_id=VALUES(receipt_id),trust_id=VALUES(trust_id),template_digest=VALUES(template_digest),
                nonce=VALUES(nonce),policy_id=VALUES(policy_id),render_grant=VALUES(render_grant),
                signature=VALUES(signature),status='accepted',expires_at=VALUES(expires_at)
            """,
            (
                receipt_id,
                batch_id,
                order_id,
                order["station_code"],
                trust["trust_id"],
                template_digest,
                nonce,
                policy["policy_id"],
                policy["render_grant"],
                signature,
                now,
                expires,
            ),
        )
        execute("UPDATE render_jobs SET receipt_id=%s,updated_at=%s WHERE batch_id=%s", (receipt_id, now, batch_id))
        redis.command("SET", f"rail:receipt:seal:{receipt_id}", json.dumps({
            "receiptId": receipt_id,
            "batchId": batch_id,
            "orderId": order_id,
            "stationCode": order["station_code"],
            "templateDigest": template_digest,
            "lane": route_name,
            "print": print_plan or {},
            "issuedAt": now,
        }, separators=(",", ":")), "EX", "660")
        send_json(self, 201, {
            "status": "signed",
            "receiptId": receipt_id,
            "batchId": batch_id,
            "templateDigest": template_digest,
            "signature": signature,
            "expiresAt": expires,
        })


def main():
    wait_for_db()
    wait_for_redis()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5006"))
    server = ThreadingHTTPServer((host, port), SignerHandler)
    print(f"receipt signer on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
