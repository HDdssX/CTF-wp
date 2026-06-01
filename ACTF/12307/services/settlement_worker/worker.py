#!/usr/bin/env python3
import http.client
import json
import os
import re
import time

from rail_common import (
    execute,
    one,
    redis,
    rows,
    safe_json,
    station_policy,
    truthy,
    verify_receipt,
    wait_for_db,
    wait_for_redis,
)


VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


def trust_has_settlement(value):
    parsed = safe_json(value, value)
    if isinstance(parsed, list):
        return "settlement" in [str(item).lower() for item in parsed]
    if isinstance(parsed, dict):
        return str(parsed.get("scope", "")).lower() == "settlement" or truthy(parsed.get("settlement"))
    return "settlement" in str(parsed).lower()


def live_continuation(order):
    if not order:
        return None
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


def minted_receipt(receipt):
    if not receipt:
        return None
    _profile, policy = station_policy(receipt["station_code"])
    raw = redis.command("GET", f"rail:receipt:seal:{receipt['receipt_id']}") or ""
    data = safe_json(raw, {}) or {}
    if data.get("receiptId") != receipt["receipt_id"]:
        return None
    if data.get("batchId") != receipt["batch_id"]:
        return None
    if data.get("templateDigest") != receipt["template_digest"]:
        return None
    if data.get("lane") != policy.get("routeName"):
        return None
    return data


def load_context(batch_id):
    job = one("SELECT * FROM render_jobs WHERE batch_id=%s", (batch_id,))
    if not job:
        return None
    receipt = one("SELECT * FROM settlement_receipts WHERE batch_id=%s AND receipt_id=%s", (batch_id, job["receipt_id"]))
    order = one("SELECT * FROM orders WHERE order_id=%s", (job["order_id"],))
    waitlist = one("SELECT * FROM waitlist_entries WHERE order_id=%s", (job["order_id"],))
    profile = one("SELECT * FROM station_profiles WHERE station_code=%s", (job["station_code"],))
    _profile, station_cfg = station_policy(job["station_code"])
    policy = one("SELECT * FROM signer_policies WHERE policy_id=%s", (receipt["policy_id"],)) if receipt else None
    trust = one("SELECT * FROM partner_trust WHERE trust_id=%s", (receipt["trust_id"],)) if receipt else None
    return {
        "job": job,
        "receipt": receipt,
        "order": order,
        "waitlist": waitlist,
        "profile": profile,
        "policy": policy,
        "trust": trust,
        "continuation": live_continuation(order),
        "ledger": ledger_attestation(job["order_id"], job["station_code"], station_cfg),
        "mint": minted_receipt(receipt),
        "epoch": redis.command("GET", f"rail:fulfillment:epoch:{job['order_id']}") or "",
        "layout": redis.command("GET", f"rail:layout:entitlement:{job['order_id']}") or "",
    }


def validate(ctx):
    reasons = []
    job = ctx["job"]
    receipt = ctx["receipt"]
    order = ctx["order"]
    waitlist = ctx["waitlist"]
    profile = ctx["profile"]
    _profile, station_cfg = station_policy(job["station_code"])
    layout_class = str(station_cfg.get("layoutClass", "standard"))[:48]
    grant_code = str(station_cfg.get("grantCode", "plain"))[:48]
    policy = ctx["policy"]
    trust = ctx["trust"]
    continuation = ctx["continuation"]
    ledger_channel = ctx["ledger"]
    mint = ctx["mint"]
    now = int(time.time())

    if not receipt or receipt["status"] != "accepted":
        reasons.append("receipt_review")
        return reasons
    if not policy or not verify_receipt(receipt, policy):
        reasons.append("receipt_signature_review")
    if receipt["template_digest"] != job["template_digest"]:
        reasons.append("template_digest_review")
    if int(receipt["expires_at"]) < now:
        reasons.append("receipt_expiry_review")
    if not order or order["order_id"] != receipt["order_id"]:
        reasons.append("order_review")
    if receipt["render_grant"] == grant_code:
        if not order or order["status"] != "waitlisted":
            reasons.append("fulfillment_state_review")
        if not waitlist or int(waitlist["sampled"]) != 1:
            reasons.append("fare_sample_review")
        if ctx["epoch"] != "boarding":
            reasons.append("fulfillment_epoch_review")
        if not profile or int(profile["batch_open"]) != 1 or profile["renderer_profile"] != layout_class:
            reasons.append("station_profile_review")
        if ctx["layout"] != job["station_code"]:
            reasons.append("layout_review")
        if not trust or trust["status"] != "accepted":
            reasons.append("partner_review")
        if not continuation:
            reasons.append("identity_review")
        if not ledger_channel:
            reasons.append("ledger_channel_review")
        if not mint:
            reasons.append("receipt_seal_review")
    return reasons


def layout_rows(station_code, layout_name):
    return {
        row["cell_name"]: row
        for row in rows(
        """
        SELECT cell_name,input_class,device_ref,enabled
        FROM bureau_layout_cells
        WHERE station_code=%s AND layout_name=%s
        """,
        (station_code, layout_name),
        )
    }


def bridge_preview(device_ref, context, print_plan):
    body = json.dumps({
        "deviceRef": str(device_ref)[:64],
        "context": {
            "batchId": context.get("batchId"),
            "orderId": context.get("orderId"),
            "stationCode": context.get("stationCode"),
            "printPlan": {
                "driverProgram": str(print_plan.get("driverProgram", ""))[:160],
                "driverArgument": str(print_plan.get("driverArgument", ""))[:160],
            },
        },
    }, separators=(",", ":")).encode()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", int(os.environ.get("LAYOUT_PORT", "5009")), timeout=3)
        conn.request("POST", "/depot/layout/preview", body=body, headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Layout-Bridge": "bureau",
        })
        resp = conn.getresponse()
        payload = resp.read()
        if resp.status != 200:
            return "[layout-error]"
        data = safe_json(payload.decode(errors="replace"), {}) or {}
        return str(data.get("value", ""))[:4000]
    except Exception as exc:
        return f"[layout-error:{exc.__class__.__name__}]"


def render(template, context, layouts, layout_enabled, station_cfg, print_plan):
    layout_policy = station_cfg.get("layout") if isinstance(station_cfg.get("layout"), dict) else {}
    prefix = str(print_plan.get("prefix") or layout_policy.get("prefix", "reconciliation"))
    selected_cell = str(print_plan.get("cell") or layout_policy.get("cell", "receipt"))
    selected_printer = str(print_plan.get("printer", "thermal-standard"))
    selected_profile = str(print_plan.get("profile", "counter-copy"))

    def resolve_cell(cell_name):
        cfg = layouts.get(cell_name)
        if not cfg or int(cfg.get("enabled", 0)) != 1:
            return ""
        if cell_name != selected_cell:
            return ""
        if not layout_enabled:
            return "[layout-pending]"
        input_class = str(cfg.get("input_class", "literal"))
        device_ref = str(cfg.get("device_ref", ""))
        if input_class in {"literal", "fixed"}:
            return device_ref
        if input_class == "json-field":
            value = context.get("data", {})
            for part in device_ref.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return ""
            return str(value)
        if input_class == "service-device":
            if selected_profile != "clearing-batch" or selected_printer != "line-printer":
                return "[layout-pending]"
            return bridge_preview(device_ref, context, print_plan)
        return ""

    def replace_var(match):
        key = match.group(1)
        if key.startswith(prefix + "."):
            return resolve_cell(key.split(".", 1)[1])
        value = context
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return ""
        return str(value)

    return VAR_RE.sub(replace_var, template)


def handle_job(row):
    try:
        queued = json.loads(row)
    except json.JSONDecodeError:
        return
    batch_id = str(queued.get("batchId", ""))[:32]
    ctx = load_context(batch_id)
    if not ctx:
        return
    time.sleep(0.25)
    reasons = validate(ctx)
    job = ctx["job"]
    receipt = ctx["receipt"] or {"render_grant": "plain"}
    order = ctx["order"] or {}
    profile = ctx["profile"] or {"renderer_profile": "standard"}
    _profile, station_cfg = station_policy(job["station_code"])
    print_plan = ctx["mint"].get("print") if isinstance(ctx.get("mint"), dict) and isinstance(ctx["mint"].get("print"), dict) else {}
    layout_enabled = (
        not reasons
        and receipt["render_grant"] == station_cfg.get("grantCode")
        and print_plan.get("profile") == "clearing-batch"
        and print_plan.get("printer") == "line-printer"
    )
    layouts = layout_rows(job["station_code"], profile.get("renderer_profile", "standard"))
    context = {
        "batchId": batch_id,
        "orderId": job["order_id"],
        "stationCode": job["station_code"],
        "status": order.get("status", "missing"),
        "passenger": order.get("passenger_name", ""),
        "trainId": order.get("train_id", ""),
        "seatClass": order.get("seat_class", ""),
        "data": safe_json(job.get("data_json"), {}) or {},
    }
    body = render(job["template_body"], context, layouts, layout_enabled, station_cfg, print_plan)
    ready = 1 if not reasons else 0
    public_reasons = [] if ready else ["review_required"]
    execute(
        """
        INSERT INTO render_results(batch_id,ready,reasons,body,finished_at)
        VALUES(%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE ready=VALUES(ready),reasons=VALUES(reasons),body=VALUES(body),finished_at=VALUES(finished_at)
        """,
        (batch_id, ready, json.dumps(public_reasons, separators=(",", ":")), body, int(time.time())),
    )
    execute("UPDATE render_jobs SET status=%s,updated_at=%s WHERE batch_id=%s", ("rendered" if ready else "blocked", int(time.time()), batch_id))


def main():
    wait_for_db()
    wait_for_redis()
    print("settlement worker ready", flush=True)
    while True:
        try:
            item = redis.command("BRPOP", "rail:settlement:jobs", 1)
            if item:
                handle_job(item[1])
        except Exception as exc:
            print(f"settlement worker error: {exc}", flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
