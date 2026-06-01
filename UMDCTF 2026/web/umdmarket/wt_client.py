import argparse
import asyncio
import ssl
import struct
import sys
from typing import Optional

sys.path.insert(0, r"F:\CTF\CTF-wp\UMDCTF 2026\web\umdmarket\vendor")

from aioquic.asyncio.client import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import FrameType, H3_ALPN, H3Connection, H3Stream
from aioquic.h3.events import (
    DatagramReceived,
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration


HOST = "umdmarket.challs.umdctf.io"
PORT = 4443
AUTHORITY = f"{HOST}:{PORT}"
PATH = "/wt"
ORIGIN = f"https://{HOST}"
CERT_HASH_HEX = "ac02c9f7e1558563180ed412dedb9e793fd9b3ab36d64beb7e178283a68a4c9f"


def u8(x: int) -> bytes:
    return bytes([x & 0xFF])


def u16(x: int) -> bytes:
    return struct.pack("<H", x)


def u32(x: int) -> bytes:
    return struct.pack("<I", x)


def read_u16(data: bytes, off: int) -> tuple[int, int]:
    return struct.unpack_from("<H", data, off)[0], off + 2


def read_u32(data: bytes, off: int) -> tuple[int, int]:
    return struct.unpack_from("<I", data, off)[0], off + 4


def read_u64(data: bytes, off: int) -> tuple[int, int]:
    return struct.unpack_from("<Q", data, off)[0], off + 8


def enc_str8(s: str) -> bytes:
    b = s.encode()
    if len(b) > 255:
        raise ValueError("string too long for string8")
    return u8(len(b)) + b


def enc(parts: list[bytes]) -> bytes:
    return b"".join(parts)


def parse_err(code: int) -> str:
    return {
        1: "ERR_INVALID_REQUEST",
        2: "ERR_NOT_AUTHENTICATED",
        3: "ERR_COOLDOWN",
        4: "ERR_STALE",
        5: "ERR_INSUFFICIENT_FUNDS",
        6: "ERR_INSUFFICIENT_POSITION",
        7: "ERR_INVALID_QTY",
        8: "ERR_MARKET_WARMUP",
        9: "ERR_TICKER_NOT_FOUND",
        10: "ERR_INVALID_CREDENTIALS",
        11: "ERR_USERNAME_TAKEN",
        12: "ERR_WEAK_PASSWORD",
        13: "ERR_ALREADY_LOGGED_IN",
        14: "ERR_INVALID_QUOTE",
        15: "ERR_RESEND_UNAVAILABLE",
        16: "ERR_TICKER_RESOLVED",
    }.get(code, f"ERR_{code}")


def parse_cert_hash(hex_s: str) -> bytes:
    return bytes.fromhex(hex_s)


class WTClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h3 = H3Connection(self._quic, enable_webtransport=True)
        self.session_stream_id: Optional[int] = None
        self._session_waiter: Optional[asyncio.Future[None]] = None
        self._stream_waiters: dict[int, asyncio.Future[bytes]] = {}
        self._stream_bufs: dict[int, bytearray] = {}
        self._datagram_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._headers_log: list[tuple[int, list[tuple[bytes, bytes]]]] = []

    async def open_session(self) -> None:
        if self.session_stream_id is not None:
            return
        loop = asyncio.get_running_loop()
        self._session_waiter = loop.create_future()
        stream_id = self._quic.get_next_available_stream_id()
        self.session_stream_id = stream_id
        headers = [
            (b":method", b"CONNECT"),
            (b":scheme", b"https"),
            (b":authority", AUTHORITY.encode()),
            (b":path", PATH.encode()),
            (b":protocol", b"webtransport"),
            (b"origin", ORIGIN.encode()),
        ]
        self.h3.send_headers(stream_id=stream_id, headers=headers)
        self.transmit()
        await self._session_waiter

    async def request(self, payload: bytes) -> bytes:
        if self.session_stream_id is None:
            raise RuntimeError("session not open")
        loop = asyncio.get_running_loop()
        stream_id = self.h3.create_webtransport_stream(self.session_stream_id)
        # aioquic does not mark locally-created WT bidirectional streams as
        # WebTransport streams, so incoming bytes get parsed as plain H3 frames.
        # Mirror the state that would normally be learned from the stream preface.
        stream = self.h3._stream.setdefault(stream_id, H3Stream(stream_id))  # type: ignore[attr-defined]
        stream.frame_type = FrameType.WEBTRANSPORT_STREAM
        stream.session_id = self.session_stream_id
        fut: asyncio.Future[bytes] = loop.create_future()
        self._stream_waiters[stream_id] = fut
        self._stream_bufs[stream_id] = bytearray()
        self._quic.send_stream_data(stream_id, payload, end_stream=True)
        self.transmit()
        return await fut

    async def recv_datagram(self, timeout: Optional[float] = None) -> bytes:
        if timeout is None:
            return await self._datagram_queue.get()
        return await asyncio.wait_for(self._datagram_queue.get(), timeout)

    def quic_event_received(self, event) -> None:
        for http_event in self.h3.handle_event(event):
            if isinstance(http_event, HeadersReceived):
                self._headers_log.append((http_event.stream_id, http_event.headers))
                if (
                    self.session_stream_id is not None
                    and http_event.stream_id == self.session_stream_id
                    and self._session_waiter is not None
                    and not self._session_waiter.done()
                ):
                    headers = dict(http_event.headers)
                    status = headers.get(b":status", b"")
                    if status == b"200":
                        self._session_waiter.set_result(None)
                    else:
                        self._session_waiter.set_exception(
                            RuntimeError(f"session open failed: {http_event.headers!r}")
                        )
            elif isinstance(http_event, WebTransportStreamDataReceived):
                buf = self._stream_bufs.setdefault(http_event.stream_id, bytearray())
                buf.extend(http_event.data)
                if http_event.stream_ended:
                    fut = self._stream_waiters.pop(http_event.stream_id, None)
                    data = bytes(self._stream_bufs.pop(http_event.stream_id, bytearray()))
                    if fut is not None and not fut.done():
                        fut.set_result(data)
            elif isinstance(http_event, DatagramReceived):
                if (
                    self.session_stream_id is not None
                    and http_event.stream_id == self.session_stream_id
                ):
                    self._datagram_queue.put_nowait(http_event.data)


class MarketClient:
    def __init__(self, proto: WTClientProtocol):
        self.proto = proto

    def _check(self, data: bytes) -> None:
        code = data[0]
        if code != 0:
            raise RuntimeError(parse_err(code))

    async def register(self, username: str, password: str) -> int:
        resp = await self.proto.request(enc([u8(0x20), enc_str8(username), enc_str8(password)]))
        self._check(resp)
        bal, _ = read_u64(resp, 1)
        return bal

    async def login(self, username: str, password: str) -> int:
        resp = await self.proto.request(enc([u8(0x21), enc_str8(username), enc_str8(password)]))
        self._check(resp)
        bal, _ = read_u64(resp, 1)
        return bal

    async def subscribe(self, ticker_id: int) -> None:
        resp = await self.proto.request(enc([u8(0x22), u16(ticker_id)]))
        self._check(resp)

    async def unsubscribe(self, ticker_id: int) -> None:
        resp = await self.proto.request(enc([u8(0x23), u16(ticker_id)]))
        self._check(resp)

    async def fetch_tickers(self) -> list[dict]:
        resp = await self.proto.request(u8(0x24))
        self._check(resp)
        off = 1
        count, off = read_u16(resp, off)
        out = []
        for _ in range(count):
            ticker_id, off = read_u16(resp, off)
            name_len = resp[off]
            off += 1
            name = resp[off:off + name_len].decode()
            off += name_len
            desc_len, off = read_u16(resp, off)
            desc = resp[off:off + desc_len].decode()
            off += desc_len
            out.append({"id": ticker_id, "name": name, "description": desc})
        return out

    async def fetch_history(self, ticker_id: int, minutes: int) -> list[tuple[int, int]]:
        resp = await self.proto.request(enc([u8(0x25), u16(ticker_id), u16(minutes)]))
        self._check(resp)
        off = 1
        count, off = read_u16(resp, off)
        rows = []
        for _ in range(count):
            ts, off = read_u64(resp, off)
            price, off = read_u16(resp, off)
            rows.append((ts, price))
        return rows

    async def resend(self, seq: int, ticker_id: int) -> dict:
        resp = await self.proto.request(enc([u8(0x26), u16(seq), u16(ticker_id)]))
        self._check(resp)
        off = 1
        seq, off = read_u16(resp, off)
        ticker_id, off = read_u16(resp, off)
        yes_price, off = read_u16(resp, off)
        hmac = resp[off:off + 8]
        return {"seq": seq, "ticker_id": ticker_id, "yes_price": yes_price, "hmac": hmac}

    async def trade(self, quote: dict, side: int, qty: int) -> tuple[int, int]:
        resp = await self.proto.request(
            enc(
                [
                    u8(0x30),
                    u16(quote["seq"]),
                    u16(quote["ticker_id"]),
                    u16(quote["yes_price"]),
                    quote["hmac"],
                    u8(side),
                    u32(qty),
                ]
            )
        )
        self._check(resp)
        fill, off = read_u16(resp, 1)
        bal, _ = read_u64(resp, off)
        return fill, bal

    async def portfolio(self) -> dict:
        resp = await self.proto.request(u8(0x40))
        self._check(resp)
        off = 1
        bal, off = read_u64(resp, off)
        count, off = read_u16(resp, off)
        positions = []
        for _ in range(count):
            ticker_id, off = read_u16(resp, off)
            yes_qty, off = read_u32(resp, off)
            no_qty, off = read_u32(resp, off)
            positions.append({"ticker_id": ticker_id, "yes_qty": yes_qty, "no_qty": no_qty})
        return {"balance": bal, "positions": positions}

    async def buy_flag(self) -> str:
        resp = await self.proto.request(u8(0x50))
        self._check(resp)
        n, _ = read_u16(resp, 1)
        return resp[3:3 + n].decode()


async def make_client() -> tuple[WTClientProtocol, MarketClient]:
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
        verify_mode=ssl.CERT_NONE,
    )
    configuration.server_name = HOST

    cert_hash = parse_cert_hash(CERT_HASH_HEX)

    async with connect(
        HOST,
        PORT,
        configuration=configuration,
        create_protocol=WTClientProtocol,
    ) as proto:
        proto = proto  # type: ignore[assignment]
        await proto.open_session()
        print(f"session stream: {proto.session_stream_id}")
        # Keep the connection alive for the caller within this context.
        return proto, MarketClient(proto)


async def run_probe(args: argparse.Namespace) -> None:
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
        verify_mode=ssl.CERT_NONE,
    )
    configuration.server_name = HOST
    _ = parse_cert_hash(CERT_HASH_HEX)

    async with connect(
        HOST,
        PORT,
        configuration=configuration,
        create_protocol=WTClientProtocol,
    ) as proto:
        proto = proto  # type: ignore[assignment]
        await proto.open_session()
        client = MarketClient(proto)
        if args.register:
            bal = await client.register(args.username, args.password)
            print(f"registered balance={bal}")
        if args.login:
            bal = await client.login(args.username, args.password)
            print(f"login balance={bal}")
        if args.tickers:
            tickers = await client.fetch_tickers()
            for item in tickers:
                print(item)
        if args.portfolio:
            print(await client.portfolio())
        if args.wait_quotes:
            tickers = await client.fetch_tickers()
            for item in tickers[: args.subscribe_first]:
                await client.subscribe(item["id"])
                print(f"subscribed {item['id']} {item['name']}")
            for _ in range(args.wait_quotes):
                d = await proto.recv_datagram(timeout=10)
                if not d:
                    continue
                if d[0] == 1 and len(d) >= 15:
                    seq = struct.unpack_from("<H", d, 1)[0]
                    ticker_id = struct.unpack_from("<H", d, 3)[0]
                    yes_price = struct.unpack_from("<H", d, 5)[0]
                    hmac = d[7:15].hex()
                    print({"type": "quote", "seq": seq, "ticker_id": ticker_id, "yes_price": yes_price, "hmac": hmac})
                elif d[0] == 2 and len(d) >= 4:
                    ticker_id = struct.unpack_from("<H", d, 1)[0]
                    outcome = d[3]
                    print({"type": "resolution", "ticker_id": ticker_id, "outcome": outcome})
                else:
                    print({"type": "unknown", "hex": d.hex()})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--username", default="probe_user")
    p.add_argument("--password", default="Probe!Passw0rd")
    p.add_argument("--register", action="store_true")
    p.add_argument("--login", action="store_true")
    p.add_argument("--tickers", action="store_true")
    p.add_argument("--portfolio", action="store_true")
    p.add_argument("--wait-quotes", type=int, default=0)
    p.add_argument("--subscribe-first", type=int, default=3)
    return p


if __name__ == "__main__":
    asyncio.run(run_probe(build_parser().parse_args()))
