#!/usr/bin/env python3
import hashlib
import hmac
import json
import os
import random
import socket
import string
import time
from http.server import BaseHTTPRequestHandler

import pymysql


REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "railapp")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "railpass")
MYSQL_DB = os.environ.get("MYSQL_DB", "rail")


class RedisError(RuntimeError):
    pass


class Redis:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.host = host
        self.port = port

    def command(self, *args):
        payload = self._encode(args)
        with socket.create_connection((self.host, self.port), timeout=3) as sock:
            sock.sendall(payload)
            reader = sock.makefile("rb")
            return self._parse(reader)

    def _encode(self, args):
        out = [f"*{len(args)}\r\n".encode()]
        for arg in args:
            data = arg if isinstance(arg, bytes) else str(arg).encode()
            out.append(f"${len(data)}\r\n".encode())
            out.append(data + b"\r\n")
        return b"".join(out)

    def _line(self, reader):
        line = reader.readline()
        if not line:
            raise RedisError("redis closed")
        return line[:-2]

    def _parse(self, reader):
        prefix = reader.read(1)
        if prefix == b"+":
            return self._line(reader).decode()
        if prefix == b"-":
            raise RedisError(self._line(reader).decode())
        if prefix == b":":
            return int(self._line(reader))
        if prefix == b"$":
            size = int(self._line(reader))
            if size == -1:
                return None
            data = reader.read(size)
            reader.read(2)
            return data.decode(errors="replace")
        if prefix == b"*":
            count = int(self._line(reader))
            if count == -1:
                return None
            return [self._parse(reader) for _ in range(count)]
        raise RedisError(f"bad redis prefix {prefix!r}")


redis = Redis()


def wait_for_redis():
    for _ in range(100):
        try:
            if redis.command("PING") == "PONG":
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("redis did not become ready")


def db():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        autocommit=True,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def wait_for_db():
    for _ in range(100):
        try:
            with db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("mysql did not become ready")


def one(sql, params=None):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def rows(sql, params=None):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())


def execute(sql, params=None):
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount


def execute_many(sql, seq):
    with db() as conn:
        with conn.cursor() as cur:
            return cur.executemany(sql, seq)


def read_json(handler: BaseHTTPRequestHandler):
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if not length:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode())
    except json.JSONDecodeError as exc:
        raise ValueError("invalid json") from exc
    if not isinstance(data, dict):
        raise ValueError("json object required")
    return data


def send_json(handler: BaseHTTPRequestHandler, status, payload, headers=None):
    body = json.dumps(payload, separators=(",", ":"), default=str).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    for key, value in (headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def send_html(handler: BaseHTTPRequestHandler, status, body):
    data = body.encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def parse_cookie(header):
    cookies = {}
    for part in (header or "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def random_id(prefix, length=10):
    alphabet = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choice(alphabet) for _ in range(length))


def digest_template(template):
    return hashlib.sha256(template.encode()).hexdigest()


def claim_digest(order_id, train_id, station_code, ticket_no, claim_salt):
    parts = [
        str(order_id),
        str(train_id),
        str(station_code),
        str(ticket_no),
        str(claim_salt),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def claim_proof(order_id, train_id, station_code, ticket_no, claim_salt, digest_value=None):
    digest_value = digest_value or claim_digest(order_id, train_id, station_code, ticket_no, claim_salt)
    return f"CP-{claim_salt}-{str(digest_value)[:12]}"


def receipt_payload(batch_id, order_id, station_code, trust_id, template_digest, nonce, policy_id, render_grant, expires_at):
    return "|".join([
        str(batch_id),
        str(order_id),
        str(station_code),
        str(trust_id),
        str(template_digest),
        str(nonce),
        str(policy_id),
        str(render_grant),
        str(expires_at),
    ])


def sign_receipt(secret, payload):
    return hmac.new(str(secret).encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_receipt(row, policy):
    payload = receipt_payload(
        row["batch_id"],
        row["order_id"],
        row["station_code"],
        row["trust_id"],
        row["template_digest"],
        row["nonce"],
        row["policy_id"],
        row["render_grant"],
        int(row["expires_at"]),
    )
    expected = sign_receipt(policy["secret_key"], payload)
    return hmac.compare_digest(expected, row["signature"])


def truthy(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "sampled", "boarding", "receipt-closeout"}


def safe_json(value, fallback=None):
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def station_policy(station_code):
    row = one("SELECT * FROM station_profiles WHERE station_code=%s", (station_code,))
    if not row:
        return None, {}
    policy = safe_json(row.get("policy_hint"), {}) or {}
    policy.setdefault("layoutClass", row.get("renderer_profile", "standard"))
    policy.setdefault("routeName", row.get("signer_route", "public"))
    policy.setdefault("grantCode", "plain")
    policy.setdefault("notice", {})
    policy.setdefault("board", {})
    policy.setdefault("claim", {})
    policy.setdefault("layout", {})
    return row, policy
