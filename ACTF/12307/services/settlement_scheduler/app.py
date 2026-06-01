#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from rail_common import execute, one, read_json, redis, safe_json, send_json, station_policy, verify_receipt, wait_for_db, wait_for_redis

DIAGNOSTICS = os.environ.get("RAIL_DIAGNOSTICS") == "1"


def minted_receipt(receipt):
    _profile, policy = station_policy(receipt["station_code"])
    raw = redis.command("GET", f"rail:receipt:seal:{receipt['receipt_id']}") or ""
    data = safe_json(raw, {}) or {}
    return (
        data.get("receiptId") == receipt["receipt_id"]
        and data.get("batchId") == receipt["batch_id"]
        and data.get("templateDigest") == receipt["template_digest"]
        and data.get("lane") == policy.get("routeName")
    )


def schedule_batch(batch_id, origin="manual"):
    job = one("SELECT * FROM render_jobs WHERE batch_id=%s", (batch_id,))
    if not job:
        return False, ["batch_review"]
    receipt = one("SELECT * FROM settlement_receipts WHERE batch_id=%s AND status='accepted'", (batch_id,))
    if not receipt:
        return False, ["receipt_review"]
    policy = one("SELECT * FROM signer_policies WHERE policy_id=%s AND enabled=1", (receipt["policy_id"],))
    if not policy or not verify_receipt(receipt, policy):
        return False, ["receipt_signature_review"]
    _profile, station_cfg = station_policy(receipt["station_code"])
    if receipt["render_grant"] == station_cfg.get("grantCode") and not minted_receipt(receipt):
        return False, ["receipt_seal_review"]
    if receipt["template_digest"] != job["template_digest"]:
        return False, ["template_digest_review"]
    if int(receipt["expires_at"]) < int(time.time()):
        return False, ["receipt_expiry_review"]

    execute(
        "UPDATE render_jobs SET receipt_id=%s,status='scheduled',updated_at=%s WHERE batch_id=%s",
        (receipt["receipt_id"], int(time.time()), batch_id),
    )
    redis.command("LPUSH", "rail:settlement:jobs", json.dumps({
        "batchId": batch_id,
        "receiptId": receipt["receipt_id"],
        "origin": origin,
        "queuedAt": int(time.time()),
    }, separators=(",", ":")))
    return True, []


class SchedulerHandler(BaseHTTPRequestHandler):
    server_version = "SettlementScheduler/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return
        if parsed.path != "/api/settlement/schedule":
            send_json(self, 404, {"error": "not_found"})
            return
        batch_id = str(data.get("batchId", ""))[:32]
        ok, reasons = schedule_batch(batch_id, "api")
        if not ok:
            if DIAGNOSTICS:
                print(f"scheduler held batch={batch_id} reasons={','.join(reasons)}", flush=True)
            else:
                print(f"scheduler held batch={batch_id}", flush=True)
        send_json(self, 202 if ok else 409, {
            "batchId": batch_id,
            "scheduled": ok,
            "reasons": [] if ok else ["review_required"],
        })


def loop_once():
    item = redis.command("BRPOP", "rail:scheduler:jobs", 1)
    if not item:
        return
    try:
        data = json.loads(item[1])
    except json.JSONDecodeError:
        return
    schedule_batch(str(data.get("batchId", ""))[:32], str(data.get("origin", "queue"))[:32])


def main():
    wait_for_db()
    wait_for_redis()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5007"))
    server = ThreadingHTTPServer((host, port), SchedulerHandler)
    print(f"settlement scheduler on {host}:{port}", flush=True)
    import threading
    threading.Thread(target=server.serve_forever, daemon=True).start()
    while True:
        try:
            loop_once()
        except Exception as exc:
            print(f"scheduler error: {exc}", flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
