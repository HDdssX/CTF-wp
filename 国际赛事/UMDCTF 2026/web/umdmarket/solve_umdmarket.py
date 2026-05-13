import argparse
import asyncio
import ssl
from collections import deque

from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration

import wt_client


TARGET_TICKER = 8  # HL3_2100
COOLDOWN_SECONDS = 5.25
TARGET_BALANCE = 10_000_000


async def wait_for_quote(proto: wt_client.WTClientProtocol, ticker_id: int) -> tuple[int, int]:
    while True:
        d = await proto.recv_datagram(timeout=30)
        if d and d[0] == 1 and int.from_bytes(d[3:5], "little") == ticker_id:
            return int.from_bytes(d[1:3], "little"), int.from_bytes(d[5:7], "little")


async def fill_buffer(
    proto: wt_client.WTClientProtocol,
    ticker_id: int,
    buf: deque[tuple[int, int]],
    count: int,
) -> None:
    while count > 0:
        seq, price = await wait_for_quote(proto, ticker_id)
        buf.append((seq, price))
        count -= 1


async def gather_for(
    proto: wt_client.WTClientProtocol,
    ticker_id: int,
    buf: deque[tuple[int, int]],
    seconds: float,
) -> None:
    end = asyncio.get_running_loop().time() + seconds
    while True:
        remain = end - asyncio.get_running_loop().time()
        if remain <= 0:
            return
        try:
            d = await proto.recv_datagram(timeout=min(1.0, remain))
        except TimeoutError:
            continue
        if d and d[0] == 1 and int.from_bytes(d[3:5], "little") == ticker_id:
            buf.append((int.from_bytes(d[1:3], "little"), int.from_bytes(d[5:7], "little")))


async def best_resend(
    client: wt_client.MarketClient,
    candidates: list[tuple[int, int]],
    ticker_id: int,
    *,
    ascending: bool,
) -> dict:
    ordered = sorted(candidates, key=lambda x: (x[1], x[0]), reverse=not ascending)
    for seq, _ in ordered:
        try:
            return await client.resend(seq, ticker_id)
        except RuntimeError as exc:
            if "ERR_TICKER_NOT_FOUND" in str(exc) or "ERR_RESEND_UNAVAILABLE" in str(exc):
                continue
            raise
    raise RuntimeError("no resend candidate available")


async def solve(username: str, password: str) -> None:
    cfg = QuicConfiguration(
        is_client=True,
        alpn_protocols=wt_client.H3_ALPN,
        max_datagram_frame_size=65536,
        verify_mode=ssl.CERT_NONE,
    )
    cfg.server_name = wt_client.HOST

    async with connect(
        wt_client.HOST,
        wt_client.PORT,
        configuration=cfg,
        create_protocol=wt_client.WTClientProtocol,
    ) as proto:
        await proto.open_session()
        client = wt_client.MarketClient(proto)

        try:
            balance = await client.login(username, password)
            print(f"login {username} balance={balance}")
        except RuntimeError as exc:
            if "ERR_INVALID_CREDENTIALS" not in str(exc):
                raise
            balance = await client.register(username, password)
            print(f"registered {username} balance={balance}")

        await client.subscribe(TARGET_TICKER)
        history: deque[tuple[int, int]] = deque(maxlen=400)
        await fill_buffer(proto, TARGET_TICKER, history, 60)

        while balance < TARGET_BALANCE:
            await asyncio.sleep(COOLDOWN_SECONDS)
            await gather_for(proto, TARGET_TICKER, history, 0.75)

            buy_quote = await best_resend(client, list(history), TARGET_TICKER, ascending=True)
            qty = balance // buy_quote["yes_price"]
            if qty <= 0:
                raise RuntimeError("quantity became zero")

            print(
                f"buy seq={buy_quote['seq']} price={buy_quote['yes_price']} qty={qty} "
                f"buffer_min={min(p for _, p in history)} buffer_max={max(p for _, p in history)}"
            )
            fill_price, balance = await client.trade(buy_quote, 0, qty)
            print(f"bought fill={fill_price} balance={balance}")

            await asyncio.sleep(COOLDOWN_SECONDS)
            await gather_for(proto, TARGET_TICKER, history, 1.25)

            portfolio = await client.portfolio()
            yes_qty = next(
                (p["yes_qty"] for p in portfolio["positions"] if p["ticker_id"] == TARGET_TICKER),
                0,
            )
            if yes_qty <= 0:
                raise RuntimeError("no YES position to sell")

            sell_quote = await best_resend(client, list(history), TARGET_TICKER, ascending=False)
            print(
                f"sell seq={sell_quote['seq']} price={sell_quote['yes_price']} qty={yes_qty} "
                f"buffer_min={min(p for _, p in history)} buffer_max={max(p for _, p in history)}"
            )
            fill_price, balance = await client.trade(sell_quote, 2, yes_qty)
            print(f"sold fill={fill_price} balance={balance}")

        flag = await client.buy_flag()
        print(f"FLAG: {flag}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    asyncio.run(solve(args.username, args.password))
