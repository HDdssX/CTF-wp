#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from rail_common import (
    claim_digest,
    execute,
    one,
    parse_cookie,
    random_id,
    read_json,
    redis,
    rows,
    safe_json,
    send_json,
    wait_for_db,
    wait_for_redis,
)


TRAINS = [
    {
        "id": "G1021",
        "origin": "Beijing South",
        "destination": "Shanghai Hongqiao",
        "depart": "07:18",
        "arrive": "12:02",
        "duration": "4h44m",
        "gate": "A12",
        "price": 553,
        "stationCode": "BJP",
        "capacity": {"business": 6, "first": 14, "second": 86},
    },
    {
        "id": "G7137",
        "origin": "Nanjing South",
        "destination": "Hangzhou East",
        "depart": "08:06",
        "arrive": "09:41",
        "duration": "1h35m",
        "gate": "B08",
        "price": 117,
        "stationCode": "NKH",
        "capacity": {"business": 4, "first": 10, "second": 60},
    },
    {
        "id": "G8829",
        "origin": "Chengdu East",
        "destination": "Chongqing North",
        "depart": "09:23",
        "arrive": "10:42",
        "duration": "1h19m",
        "gate": "C03",
        "price": 154,
        "stationCode": "ICW",
        "capacity": {"business": 3, "first": 8, "second": 52},
    },
    {
        "id": "G4015",
        "origin": "Guangzhou South",
        "destination": "Shenzhen North",
        "depart": "10:10",
        "arrive": "10:46",
        "duration": "36m",
        "gate": "D19",
        "price": 75,
        "stationCode": "IZQ",
        "capacity": {"business": 2, "first": 12, "second": 72},
    },
    {
        "id": "G7608",
        "origin": "Hangzhou East",
        "destination": "Hefei South",
        "depart": "16:24",
        "arrive": "18:37",
        "duration": "2h13m",
        "gate": "B21",
        "price": 214,
        "stationCode": "HGH",
        "capacity": {"business": 2, "first": 9, "second": 56},
        "initial": {"business": 0, "first": 4, "second": 18},
    },
]


def seed_inventory():
    wait_for_redis()
    wait_for_db()
    for train in TRAINS:
        initial = train.get("initial", {})
        for seat_class, count in train["capacity"].items():
            redis.command("SETNX", f"rail:seat:{train['id']}:{seat_class}", initial.get(seat_class, count))


def train_snapshot():
    trains = []
    for train in TRAINS:
        seats = {}
        waitlist = {}
        for seat_class in train["capacity"]:
            remaining = redis.command("GET", f"rail:seat:{train['id']}:{seat_class}")
            queued = redis.command("LLEN", f"rail:wait:{train['id']}:{seat_class}")
            seats[seat_class] = int(remaining or 0)
            waitlist[seat_class] = int(queued or 0)
        item = dict(train)
        item.pop("capacity", None)
        item.pop("initial", None)
        item["seats"] = seats
        item["waitlist"] = waitlist
        trains.append(item)
    return trains


def session_to_mysql(session_id, fallback_name):
    if not session_id or session_id == "guest":
        return
    raw = redis.command("GET", f"rail:sso:session:{session_id}")
    if not raw:
        return
    data = safe_json(raw, {}) or {}
    trust_level = data.get("trustLevel", ["mobile"])
    partner_id = str(data.get("partnerId", "mobile-partner"))[:64]
    passenger = str(data.get("passenger", fallback_name))[:96]
    now = int(time.time())
    execute(
        """
        INSERT INTO passengers(session_id,passenger_name,trust_state,partner_id,trust_level,issued_at,completed_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE passenger_name=VALUES(passenger_name),trust_state=VALUES(trust_state),
            partner_id=VALUES(partner_id),trust_level=VALUES(trust_level),completed_at=VALUES(completed_at)
        """,
        (
            session_id,
            passenger,
            str(data.get("state", "pending"))[:32],
            partner_id,
            json.dumps(trust_level, separators=(",", ":")),
            int(data.get("issuedAt", now) // 1000 if int(data.get("issuedAt", now)) > 9999999999 else data.get("issuedAt", now)),
            now if data.get("state") == "complete" else None,
        ),
    )
    continuation = redis.command("GET", f"rail:passenger:continuation:{session_id}")
    if continuation:
        trusted = safe_json(continuation, {}) or {}
        execute(
            """
            INSERT INTO partner_trust(trust_id,session_id,partner_id,station_code,trust_level,status,created_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE trust_level=VALUES(trust_level),status=VALUES(status)
            """,
            (
                f"TRUST-{session_id[:18]}",
                session_id,
                partner_id,
                str(data.get("stationCode", "BJP"))[:16],
                json.dumps(trusted.get("trustLevel", trust_level), separators=(",", ":")),
                "accepted" if trusted.get("trust") == "partner-continuation" else "pending",
                now,
            ),
        )


def list_orders():
    result = []
    for row in rows(
        """
        SELECT order_id,train_id,passenger_name,station_code,seat_class,status,origin_name,destination_name,depart_time,created_at
        FROM orders ORDER BY created_at DESC LIMIT 24
        """
    ):
        result.append({
            "id": row["order_id"],
            "trainId": row["train_id"],
            "passenger": row["passenger_name"],
            "stationCode": row["station_code"],
            "seatClass": row["seat_class"],
            "status": row["status"],
            "origin": row["origin_name"],
            "destination": row["destination_name"],
            "depart": row["depart_time"],
            "createdAt": int(row["created_at"]),
        })
    return result


def list_notices():
    result = []
    for row in rows("SELECT slug,title,body,created_at FROM station_notices ORDER BY created_at DESC LIMIT 10"):
        result.append({
            "slug": row["slug"],
            "title": row["title"],
            "body": row["body"],
            "createdAt": int(row["created_at"]),
        })
    return result


def session_summary(headers):
    cookies = parse_cookie(headers.get("Cookie", ""))
    session_id = cookies.get("passenger_session", "")
    passenger = one("SELECT passenger_name,trust_state FROM passengers WHERE session_id=%s", (session_id,)) if session_id else None
    return {
        "session": bool(session_id),
        "trusted": bool(passenger and passenger["trust_state"] == "complete"),
        "passenger": passenger["passenger_name"] if passenger else "Passenger",
    }


def enterprise_summary():
    accounts = rows("SELECT account_id,company_name,station_code,status FROM enterprise_accounts ORDER BY updated_at DESC LIMIT 4")
    invoices = []
    for account in accounts:
        invoices.append({
            "invoiceId": f"E-{account['station_code']}-1001",
            "accountId": account["account_id"],
            "companyName": account["company_name"],
            "stationCode": account["station_code"],
            "disputeState": "open" if account["status"] == "active" else "review",
        })
    return {"invoices": invoices}


def issue_claim_artifact(order_id, train_id, station_code, now):
    ticket = one(
        """
        SELECT ticket_no FROM ticket_index
        WHERE train_id=%s AND station_code=%s
        ORDER BY ticket_no LIMIT 1
        """,
        (train_id, station_code),
    )
    if not ticket:
        ticket = one(
            "SELECT ticket_no FROM ticket_index WHERE station_code=%s ORDER BY ticket_no LIMIT 1",
            (station_code,),
        )
    if not ticket:
        return
    claim_salt = random_id("R", 8)
    digest_value = claim_digest(order_id, train_id, station_code, ticket["ticket_no"], claim_salt)
    execute(
        """
        INSERT INTO station_claim_artifacts(order_id,station_code,train_id,ticket_no,claim_salt,claim_digest,issued_at,expires_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE train_id=VALUES(train_id),claim_salt=VALUES(claim_salt),claim_digest=VALUES(claim_digest),
            issued_at=VALUES(issued_at),expires_at=VALUES(expires_at)
        """,
        (
            order_id,
            station_code,
            train_id,
            ticket["ticket_no"],
            claim_salt,
            digest_value,
            now,
            now + 900,
        ),
    )


class RailHandler(BaseHTTPRequestHandler):
    server_version = "RailReserve/2026"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/trains":
            q = parse_qs(parsed.query)
            trains = train_snapshot()
            if "origin" in q:
                needle = q["origin"][0].lower()
                trains = [t for t in trains if needle in t["origin"].lower()]
            send_json(self, 200, {"trains": trains, "serverTime": int(time.time())})
            return

        if parsed.path == "/api/orders":
            send_json(self, 200, {"orders": list_orders()})
            return

        if parsed.path == "/api/passenger/status":
            send_json(self, 200, session_summary(self.headers))
            return

        if parsed.path == "/api/workspace":
            send_json(self, 200, {
                "trains": train_snapshot(),
                "orders": list_orders(),
                "notices": list_notices(),
                "session": session_summary(self.headers),
                "enterprise": enterprise_summary(),
                "serverTime": int(time.time()),
            })
            return

        send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = read_json(self)
        except ValueError as exc:
            send_json(self, 400, {"error": str(exc)})
            return

        if parsed.path == "/api/orders":
            self.create_order(data)
            return

        if parsed.path == "/orders/hold":
            self.create_order_hold(data)
            return

        send_json(self, 404, {"error": "not_found"})

    def create_order(self, data):
        train_id = str(data.get("trainId", ""))
        seat_class = str(data.get("seatClass", "second"))
        passenger = str(data.get("passenger", "Passenger"))[:96]
        train = next((item for item in TRAINS if item["id"] == train_id), None)
        if not train or seat_class not in train["capacity"]:
            send_json(self, 400, {"error": "invalid_train_or_seat"})
            return

        cookies = parse_cookie(self.headers.get("Cookie", ""))
        passenger_session = cookies.get("passenger_session", "guest")
        session_to_mysql(passenger_session, passenger)
        order_id = random_id("O")
        now = int(time.time())

        remaining = redis.command("DECR", f"rail:seat:{train_id}:{seat_class}")
        status = "confirmed"
        queue_position = 0
        if remaining < 0:
            redis.command("INCR", f"rail:seat:{train_id}:{seat_class}")
            status = "waitlisted"
            queue_position = redis.command("RPUSH", f"rail:wait:{train_id}:{seat_class}", order_id)

        execute(
            """
            INSERT INTO orders(order_id,train_id,passenger_session,passenger_name,station_code,seat_class,status,
                origin_name,destination_name,depart_time,created_at,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                order_id,
                train_id,
                passenger_session,
                passenger,
                train["stationCode"],
                seat_class,
                status,
                train["origin"],
                train["destination"],
                train["depart"],
                now,
                now,
            ),
        )
        if status == "waitlisted":
            execute(
                """
                INSERT INTO waitlist_entries(order_id,train_id,station_code,seat_class,status,sampled,sample_origin,queue_position,updated_at)
                VALUES(%s,%s,%s,%s,'pending',0,'mobile-waitlist',%s,%s)
                ON DUPLICATE KEY UPDATE status='pending',queue_position=VALUES(queue_position),updated_at=VALUES(updated_at)
                """,
                (order_id, train_id, train["stationCode"], seat_class, queue_position, now),
            )
            issue_claim_artifact(order_id, train_id, train["stationCode"], now)

        redis.command("SET", f"rail:order:snapshot:{order_id}", json.dumps({
            "orderId": order_id,
            "trainId": train_id,
            "seatClass": seat_class,
            "status": status,
            "stationCode": train["stationCode"],
            "passengerSession": passenger_session,
            "cachedAt": now,
        }, separators=(",", ":")), "EX", 900)
        send_json(self, 201, {"order": {
            "id": order_id,
            "trainId": train_id,
            "origin": train["origin"],
            "destination": train["destination"],
            "depart": train["depart"],
            "seatClass": seat_class,
            "passenger": passenger,
            "stationCode": train["stationCode"],
            "createdAt": now,
            "status": status,
            "queuePosition": queue_position,
        }})

    def create_order_hold(self, data):
        hold_class = self.headers.get("X-Seat-Hold-Class", "")
        train_id = str(data.get("trainId", ""))
        seat_class = str(data.get("seatClass", "second"))
        hold_mode = str(data.get("holdMode", "normal"))
        train = next((item for item in TRAINS if item["id"] == train_id), None)
        if not train or seat_class not in train["capacity"]:
            send_json(self, 400, {"error": "invalid_train_or_seat"})
            return
        if hold_class != "quota-sync":
            send_json(self, 403, {"error": "identity_continuation_required", "trainId": train_id})
            return
        if hold_mode != "waitlist":
            send_json(self, 202, {"holdId": random_id("H"), "status": "queued", "trainId": train_id})
            return

        body = {
            "error": "seat_hold_contention",
            "hint": "waitlist_channel_required",
            "trainId": train_id,
            "seatClass": seat_class,
            "inventoryEpoch": redis.command("INCR", "rail:hold:epoch"),
        }
        send_json(self, 409, body, {"X-Hold-Mode": "waitlist"})


def main():
    seed_inventory()
    host = os.environ.get("PYTHON_HOST", "127.0.0.1")
    port = int(os.environ.get("PYTHON_PORT", "5000"))
    server = ThreadingHTTPServer((host, port), RailHandler)
    print(f"ticketing api on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
