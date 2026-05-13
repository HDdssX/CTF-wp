#!/usr/bin/env python3
import json
import os
import time

from rail_common import execute, wait_for_db


ROOT = os.path.dirname(__file__)
FIXTURE = os.path.join(ROOT, "fixtures", "railway_business.json")


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    wait_for_db()
    data = load_fixture()
    now = int(time.time())

    for row in data.get("stationProfiles", []):
        execute(
            """
            INSERT INTO station_profiles(station_code,station_name,batch_open,renderer_profile,notice_profile,signer_route,policy_hint,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE station_name=VALUES(station_name),policy_hint=VALUES(policy_hint),updated_at=VALUES(updated_at)
            """,
            (
                row["stationCode"],
                row["stationName"],
                int(row.get("batchOpen", 0)),
                row.get("rendererProfile", "standard"),
                row.get("noticeProfile", "standard"),
                row.get("signerRoute", "public"),
                json.dumps(row.get("policy", {}), separators=(",", ":")),
                now,
            ),
        )

    for row in data.get("ticketIndex", []):
        execute(
            """
            INSERT INTO ticket_index(ticket_no,passenger,train_id,station_code,status)
            VALUES(%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE passenger=VALUES(passenger),status=VALUES(status)
            """,
            (row["ticketNo"], row["passenger"], row["trainId"], row["stationCode"], row["status"]),
        )

    for row in data.get("enterpriseAccounts", []):
        execute(
            """
            INSERT INTO enterprise_accounts(account_id,company_name,station_code,route_policy,status,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE company_name=VALUES(company_name),route_policy=VALUES(route_policy),status=VALUES(status),updated_at=VALUES(updated_at)
            """,
            (
                row["accountId"],
                row["companyName"],
                row["stationCode"],
                json.dumps(row.get("routePolicy", {}), separators=(",", ":")),
                row.get("status", "active"),
                now,
            ),
        )

    for row in data.get("signerPolicies", []):
        execute(
            """
            INSERT INTO signer_policies(policy_id,station_code,route_name,secret_key,render_grant,enabled,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE route_name=VALUES(route_name),render_grant=VALUES(render_grant),enabled=VALUES(enabled),updated_at=VALUES(updated_at)
            """,
            (
                row["policyId"],
                row["stationCode"],
                row["routeName"],
                row["secretKey"],
                row["renderGrant"],
                int(row.get("enabled", 1)),
                now,
            ),
        )

    for row in data.get("layoutCells", []):
        execute(
            """
            INSERT INTO bureau_layout_cells(station_code,layout_name,cell_name,input_class,device_ref,enabled,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE input_class=VALUES(input_class),device_ref=VALUES(device_ref),enabled=VALUES(enabled),updated_at=VALUES(updated_at)
            """,
            (
                row["stationCode"],
                row["layoutName"],
                row["cellName"],
                row["inputClass"],
                row["deviceRef"],
                int(row.get("enabled", 1)),
                now,
            ),
        )

    for row in data.get("deviceRoutes", []):
        execute(
            """
            INSERT INTO depot_device_routes(device_ref,station_code,device_class,codec,driver_profile,enabled,updated_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE device_class=VALUES(device_class),codec=VALUES(codec),driver_profile=VALUES(driver_profile),
                enabled=VALUES(enabled),updated_at=VALUES(updated_at)
            """,
            (
                row["deviceRef"],
                row["stationCode"],
                row["deviceClass"],
                row["codec"],
                row.get("driverProfile", ""),
                int(row.get("enabled", 1)),
                now,
            ),
        )


if __name__ == "__main__":
    main()
