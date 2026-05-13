#!/usr/bin/env python3
import hashlib
import hmac
import json
import os
import select
import signal
import time

from rail_common import redis, safe_json, wait_for_redis


SPOOL_HOME = os.environ.get("SPOOL_HOME", "/run/rail-spool")


def read_text(name):
    try:
        with open(os.path.join(SPOOL_HOME, name), "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def bridge_key():
    return read_text("bridge.key").strip()


def device_map():
    return safe_json(read_text("device-map.json"), {}) or {}


def ticket_payload(ticket):
    return json.dumps(
        {key: value for key, value in ticket.items() if key != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    )


def verify_ticket(ticket):
    key = bridge_key()
    if not key:
        return False
    signature = str(ticket.get("signature", ""))
    expected = hmac.new(key.encode(), ticket_payload(ticket).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def run_driver(program, argument):
    if not program.startswith(os.path.join("/", "usr", "bin", "")):
        return ""
    if not argument.startswith(os.path.join("/", "")):
        return ""
    read_fd, write_fd = os.pipe()
    file_actions = [
        (os.POSIX_SPAWN_CLOSE, read_fd),
        (os.POSIX_SPAWN_DUP2, write_fd, 1),
        (os.POSIX_SPAWN_DUP2, write_fd, 2),
        (os.POSIX_SPAWN_CLOSE, write_fd),
    ]
    pid = os.posix_spawn(program, [program, argument], os.environ, file_actions=file_actions)
    os.close(write_fd)
    chunks = []
    deadline = time.time() + 2
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([read_fd], [], [], 0.05)
            if ready:
                chunk = os.read(read_fd, 4096)
                if not chunk:
                    break
                chunks.append(chunk)
                if sum(len(item) for item in chunks) > 4096:
                    break
            done, _status = os.waitpid(pid, os.WNOHANG)
            if done:
                break
        else:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
    finally:
        os.close(read_fd)
    return b"".join(chunks).decode(errors="replace")[:4000]


def publish(ticket_id, status, value=""):
    key = f"rail:spool:result:{ticket_id}"
    redis.command("LPUSH", key, json.dumps({"status": status, "value": value}, separators=(",", ":")))
    redis.command("EXPIRE", key, 20)


def handle(raw):
    ticket = safe_json(raw, {}) or {}
    ticket_id = str(ticket.get("ticketId", ""))[:32]
    if not ticket_id:
        return
    if not verify_ticket(ticket):
        publish(ticket_id, "review")
        return
    profile = str(ticket.get("driverProfile", ""))
    route = device_map().get(profile)
    if not isinstance(route, dict):
        publish(ticket_id, "review")
        return
    if str(ticket.get("codec", "")) != str(route.get("codec", "")):
        publish(ticket_id, "review")
        return
    program = str(ticket.get("driverProgram", ""))
    argument = str(ticket.get("driverArgument", ""))
    accepted = route.get("acceptedPrograms")
    if not isinstance(accepted, list) or program not in [str(item) for item in accepted]:
        publish(ticket_id, "review")
        return
    value = run_driver(program, argument)
    publish(ticket_id, "ready", value)


def main():
    wait_for_redis()
    print("rail print channel ready", flush=True)
    while True:
        try:
            item = redis.command("BRPOP", "rail:spool:requests", 1)
            if item:
                handle(item[1])
        except Exception as exc:
            print(f"rail print channel review: {exc}", flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
