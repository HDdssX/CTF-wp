#!/usr/bin/env python3
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from rail_common import one, random_id, read_json, redis, safe_json, send_json, wait_for_db, wait_for_redis


SPOOL_HOME = os.environ.get("SPOOL_HOME", "/run/rail-spool")


def bridge_key():
    try:
        with open(os.path.join(SPOOL_HOME, "bridge.key"), "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def ticket_payload(ticket):
    return json.dumps(
        {key: value for key, value in ticket.items() if key != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    )


def sign_ticket(ticket):
    key = bridge_key()
    if not key:
        return ""
    return hmac.new(key.encode(), ticket_payload(ticket).encode(), hashlib.sha256).hexdigest()


def spool_device(route, context):
    print_plan = context.get("printPlan") if isinstance(context.get("printPlan"), dict) else {}
    ticket = {
        "ticketId": random_id("P", 12),
        "deviceRef": route["device_ref"],
        "stationCode": route["station_code"],
        "driverProfile": route.get("driver_profile", ""),
        "codec": route.get("codec", ""),
        "driverProgram": str(print_plan.get("driverProgram", ""))[:160],
        "driverArgument": str(print_plan.get("driverArgument", ""))[:160],
        "context": {
            "batchId": context.get("batchId"),
            "orderId": context.get("orderId"),
            "stationCode": context.get("stationCode"),
        },
        "issuedAt": int(time.time()),
    }
    ticket["signature"] = sign_ticket(ticket)
    if not ticket["signature"]:
        return "[layout-pending]"
    result_key = f"rail:spool:result:{ticket['ticketId']}"
    redis.command("LPUSH", "rail:spool:requests", json.dumps(ticket, separators=(",", ":")))
    result = redis.command("BRPOP", result_key, 3)
    if not result:
        return "[layout-pending]"
    data = safe_json(result[1], {}) or {}
    if data.get("status") != "ready":
        return "[layout-pending]"
    return str(data.get("value", ""))[:4000]


def collect_device(device_ref, station_code, context):
    route = one(
        "SELECT * FROM depot_device_routes WHERE device_ref=%s AND station_code=%s AND enabled=1",
        (device_ref, station_code),
    )
    if not route:
        return ""
    if route["codec"] == "literal":
        return "review pending"
    if route["codec"] != "settlement-filter":
        return ""
    return spool_device(route, context)


class LayoutHandler(BaseHTTPRequestHandler):
    server_version = "DepotLayout/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/depot/layout/preview":
            send_json(self, 404, {"error": "not_found"})
            return
        if self.headers.get("X-Layout-Bridge") != "bureau":
            send_json(self, 403, {"error": "review_required"})
            return
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return
        context = data.get("context") if isinstance(data.get("context"), dict) else {}
        device_ref = str(data.get("deviceRef", ""))[:64]
        station_code = str(context.get("stationCode", ""))[:16]
        send_json(self, 200, {"value": collect_device(device_ref, station_code, context)})


def main():
    wait_for_db()
    wait_for_redis()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5009"))
    server = ThreadingHTTPServer((host, port), LayoutHandler)
    print(f"depot layout bridge on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
