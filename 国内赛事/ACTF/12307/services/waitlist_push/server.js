#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const http = require("http");
const net = require("net");

const REDIS_HOST = process.env.REDIS_HOST || "127.0.0.1";
const REDIS_PORT = Number(process.env.REDIS_PORT || 6379);
const HOST = process.env.NODE_HOST || "127.0.0.1";
const PORT = Number(process.env.NODE_PORT || 5001);

function encodeCommand(args) {
  const chunks = [Buffer.from(`*${args.length}\r\n`)];
  for (const arg of args) {
    const data = Buffer.from(String(arg));
    chunks.push(Buffer.from(`$${data.length}\r\n`));
    chunks.push(data);
    chunks.push(Buffer.from("\r\n"));
  }
  return Buffer.concat(chunks);
}

function findLine(buffer, offset) {
  for (let i = offset; i + 1 < buffer.length; i += 1) {
    if (buffer[i] === 13 && buffer[i + 1] === 10) return i;
  }
  return -1;
}

function parseResp(buffer, offset = 0) {
  if (offset >= buffer.length) return null;
  const prefix = String.fromCharCode(buffer[offset]);
  const lineEnd = findLine(buffer, offset + 1);
  if (lineEnd === -1) return null;
  const line = buffer.subarray(offset + 1, lineEnd).toString();
  const next = lineEnd + 2;

  if (prefix === "+") return { value: line, offset: next };
  if (prefix === "-") throw new Error(line);
  if (prefix === ":") return { value: Number(line), offset: next };
  if (prefix === "$") {
    const size = Number(line);
    if (size === -1) return { value: null, offset: next };
    if (buffer.length < next + size + 2) return null;
    const value = buffer.subarray(next, next + size).toString();
    return { value, offset: next + size + 2 };
  }
  if (prefix === "*") {
    const count = Number(line);
    if (count === -1) return { value: null, offset: next };
    const values = [];
    let cursor = next;
    for (let i = 0; i < count; i += 1) {
      const item = parseResp(buffer, cursor);
      if (!item) return null;
      values.push(item.value);
      cursor = item.offset;
    }
    return { value: values, offset: cursor };
  }
  throw new Error(`bad redis prefix ${prefix}`);
}

function redisCommand(...args) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: REDIS_HOST, port: REDIS_PORT });
    let buffer = Buffer.alloc(0);
    const timer = setTimeout(() => {
      socket.destroy();
      reject(new Error("redis timeout"));
    }, 2000);

    socket.on("connect", () => socket.write(encodeCommand(args)));
    socket.on("data", chunk => {
      buffer = Buffer.concat([buffer, chunk]);
      try {
        const parsed = parseResp(buffer);
        if (!parsed) return;
        clearTimeout(timer);
        socket.end();
        resolve(parsed.value);
      } catch (err) {
        clearTimeout(timer);
        socket.destroy();
        reject(err);
      }
    });
    socket.on("error", err => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

function parseCookies(header) {
  const cookies = {};
  for (const part of String(header || "").split(";")) {
    const idx = part.indexOf("=");
    if (idx === -1) continue;
    cookies[part.slice(0, idx).trim()] = part.slice(idx + 1).trim();
  }
  return cookies;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    req.on("data", chunk => {
      total += chunk.length;
      if (total > 65536) {
        reject(new Error("request too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString();
      if (!raw) {
        resolve({});
        return;
      }
      try {
        const data = JSON.parse(raw);
        resolve(data && typeof data === "object" ? data : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, payload, headers = {}) {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": body.length,
    ...headers,
  });
  res.end(body);
}

async function validChannel(req) {
  const cookies = parseCookies(req.headers.cookie || "");
  const ticket = req.headers["x-waitlist-session"] || cookies.waitlist_session || "";
  if (!ticket) return "";
  const value = await redisCommand("GET", `rail:waitlist:session:${ticket}`);
  return value === "quota-sync" ? ticket : "";
}

async function openWaitlistChannel(req, res) {
  if (req.headers["x-ticket-flow"] !== "waitlist-channel") {
    sendJson(res, 404, { error: "not_found" });
    return;
  }

  const ticket = crypto.randomBytes(18).toString("base64url");
  await redisCommand("SET", `rail:waitlist:session:${ticket}`, "quota-sync", "EX", "120");
  await redisCommand("LPUSH", "rail:waitlist:channels", JSON.stringify({
    channel: ticket.slice(0, 8),
    issuedAt: Date.now(),
    purpose: "seat-hold-contention",
  }));
  await redisCommand("LTRIM", "rail:waitlist:channels", "0", "39");

  sendJson(res, 200, { status: "waitlist_channel_ready", expiresIn: 120 }, {
    "Set-Cookie": `waitlist_session=${ticket}; Path=/; HttpOnly; SameSite=Lax`,
    "Cache-Control": "no-store",
  });
}

async function pulse(req, res) {
  const ticket = await validChannel(req);
  if (!ticket) {
    sendJson(res, 401, { error: "waitlist_channel_required" });
    return;
  }
  let data;
  try {
    data = await readBody(req);
  } catch {
    sendJson(res, 400, { error: "invalid_json" });
    return;
  }
  const orderId = String(data.orderId || "").slice(0, 32);
  if (!/^O[A-Z0-9]{10}$/.test(orderId)) {
    sendJson(res, 400, { error: "invalid_order" });
    return;
  }

  await redisCommand("SET", `rail:fulfillment:epoch:${orderId}`, "boarding", "EX", "7");
  await redisCommand("SET", `rail:waitlist:observed:${orderId}`, JSON.stringify({
    orderId,
    channel: ticket.slice(0, 8),
    pulseAt: Date.now(),
  }), "EX", "120");
  sendJson(res, 202, { status: "observed", orderId, windowSeconds: 7 });
}

async function channels(req, res) {
  const rows = await redisCommand("LRANGE", "rail:waitlist:channels", "0", "9");
  sendJson(res, 200, { channel: "seat-hold-contention", recent: rows || [] });
}

async function boardStatus(req, res) {
  const url = new URL(req.url, "http://rail.local");
  const stationCode = String(url.searchParams.get("stationCode") || "HGH").slice(0, 16);
  const profile = await boardProfile(stationCode);
  sendJson(res, 200, {
    board: "boarding-monitor",
    stationCode,
    stream: profile ? "available" : "standard",
  });
}

function parseSnapshot(raw) {
  try {
    return JSON.parse(raw || "{}");
  } catch {
    return {};
  }
}

async function boardProfile(stationCode) {
  const raw = await redisCommand("GET", `rail:board:profile:${stationCode}`);
  if (!raw) return null;
  try {
    const profile = JSON.parse(raw);
    return profile && profile.topic && profile.transport && profile.ack ? profile : null;
  } catch {
    return null;
  }
}

function wsAccept(key) {
  return crypto
    .createHash("sha1")
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest("base64");
}

function encodeWs(payload) {
  const data = Buffer.from(JSON.stringify(payload));
  if (data.length < 126) {
    return Buffer.concat([Buffer.from([0x81, data.length]), data]);
  }
  return Buffer.concat([Buffer.from([0x81, 126, data.length >> 8, data.length & 255]), data]);
}

function decodeWs(buffer) {
  const messages = [];
  let cursor = 0;
  while (cursor + 2 <= buffer.length) {
    const first = buffer[cursor];
    const second = buffer[cursor + 1];
    const opcode = first & 0x0f;
    const masked = Boolean(second & 0x80);
    let length = second & 0x7f;
    let header = 2;
    if (length === 126) {
      if (cursor + 4 > buffer.length) break;
      length = buffer.readUInt16BE(cursor + 2);
      header = 4;
    } else if (length === 127) {
      return { messages, rest: Buffer.alloc(0), close: true };
    }
    const maskOffset = cursor + header;
    const payloadOffset = maskOffset + (masked ? 4 : 0);
    if (cursor + header + (masked ? 4 : 0) + length > buffer.length) break;
    if (opcode === 8) return { messages, rest: Buffer.alloc(0), close: true };
    if (!masked) return { messages, rest: Buffer.alloc(0), close: true };
    if (opcode === 1) {
      const payload = Buffer.from(buffer.subarray(payloadOffset, payloadOffset + length));
      const mask = buffer.subarray(maskOffset, maskOffset + 4);
      for (let i = 0; i < payload.length; i += 1) payload[i] ^= mask[i % 4];
      messages.push(payload.toString("utf8"));
    }
    cursor = payloadOffset + length;
  }
  return { messages, rest: buffer.subarray(cursor), close: false };
}

function sendWs(socket, payload) {
  socket.write(encodeWs(payload));
}

async function handleBoardMessage(message, socket, ticket, state, profile) {
  let data;
  try {
    data = JSON.parse(message);
  } catch {
    sendWs(socket, { event: "review", reason: "format" });
    return;
  }
  const type = String(data.type || "");

  if (type === "boarding.ping") {
    sendWs(socket, { event: "boarding.pong", t: Date.now() });
    return;
  }

  if (type === "boarding.hello") {
    const presented = String(data.channel || "");
    if (presented !== ticket && presented !== ticket.slice(0, 8)) {
      sendWs(socket, { event: "review", reason: "channel" });
      return;
    }
    state.hello = true;
    sendWs(socket, { event: "boarding.ready", channel: ticket.slice(0, 8) });
    return;
  }

  if (type === "boarding.bind") {
    if (!state.hello || String(data.topic || "") !== profile.topic) {
      sendWs(socket, { event: "review", reason: "sequence" });
      return;
    }
    const trainId = String(data.trainId || "").slice(0, 16);
    const seatClass = String(data.seatClass || "").slice(0, 24);
    if (!/^G[0-9]{4}$/.test(trainId) || !/^[a-z-]{3,24}$/.test(seatClass)) {
      sendWs(socket, { event: "review", reason: "topic" });
      return;
    }
    state.subscription = { trainId, seatClass };
    sendWs(socket, { event: "boarding.bound", topic: profile.topic, trainId, seatClass });
    return;
  }

  if (type === "boarding.confirm") {
    if (!state.hello || !state.subscription) {
      sendWs(socket, { event: "review", reason: "sequence" });
      return;
    }
    const orderId = String(data.orderId || "").slice(0, 32);
    const stationCode = String(data.stationCode || "").slice(0, 16);
    const inventoryEpoch = String(data.epoch || "").slice(0, 40);
    if (!/^O[A-Z0-9]{10}$/.test(orderId)) {
      sendWs(socket, { event: "review", reason: "order" });
      return;
    }
    const snapshot = parseSnapshot(await redisCommand("GET", `rail:order:snapshot:${orderId}`));
    if (
      snapshot.orderId !== orderId ||
      snapshot.status !== "waitlisted" ||
      snapshot.stationCode !== stationCode ||
      snapshot.trainId !== state.subscription.trainId ||
      snapshot.seatClass !== state.subscription.seatClass
    ) {
      sendWs(socket, { event: "review", reason: "snapshot" });
      return;
    }

    const boardingNonce = crypto.randomBytes(18).toString("base64url");
    const ledgerRef = crypto.createHash("sha256").update(`${orderId}:${stationCode}:${boardingNonce}`).digest("hex").slice(0, 24);
    const attestation = {
      orderId,
      stationCode,
      channel: ticket.slice(0, 8),
      ledgerRef,
      boardingNonce,
      transport: profile.transport,
      ack: profile.ack,
      trainId: state.subscription.trainId,
      seatClass: state.subscription.seatClass,
      inventoryEpoch,
      observedAt: Date.now(),
    };
    await redisCommand("SET", `rail:ledger:channel:${orderId}`, JSON.stringify(attestation), "EX", "90");
    await redisCommand("LPUSH", "rail:ledger:channel-log", JSON.stringify({
      orderId,
      stationCode,
      channel: attestation.channel,
      observedAt: attestation.observedAt,
    }));
    await redisCommand("LTRIM", "rail:ledger:channel-log", "0", "24");
    sendWs(socket, { event: "boarding.confirmed", orderId, stationCode, ledgerRef: attestation.ledgerRef, expiresIn: 90 });
    return;
  }

  sendWs(socket, { event: "review", reason: "message" });
}

async function handleUpgrade(req, socket) {
  const url = new URL(req.url, "http://rail.local");
  if (url.pathname !== "/api/coach/board") {
    socket.end("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n");
    return;
  }
  const stationCode = String(url.searchParams.get("stationCode") || "HGH").slice(0, 16);
  const profile = await boardProfile(stationCode);
  if (!profile) {
    socket.end("HTTP/1.1 426 Upgrade Required\r\nContent-Length: 0\r\n\r\n");
    return;
  }

  const ticket = await validChannel(req);
  if (!ticket) {
    socket.end("HTTP/1.1 401 Unauthorized\r\nContent-Length: 0\r\n\r\n");
    return;
  }

  const wsKey = req.headers["sec-websocket-key"];
  const upgrade = String(req.headers.upgrade || "").toLowerCase();
  const connection = String(req.headers.connection || "").toLowerCase();
  if (!wsKey || req.headers["sec-websocket-version"] !== "13" || upgrade !== "websocket" || !connection.includes("upgrade")) {
    socket.end("HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n");
    return;
  }

  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
    "Connection: Upgrade\r\n" +
    "Upgrade: websocket\r\n" +
    `Sec-WebSocket-Accept: ${wsAccept(wsKey)}\r\n` +
    "\r\n"
  );

  socket.setTimeout(120000);
  sendWs(socket, { event: "boarding.hello_required", channel: ticket.slice(0, 8), topic: profile.topic });
  let buffer = Buffer.alloc(0);
  const state = { hello: false, subscription: null };
  socket.on("data", chunk => {
    buffer = Buffer.concat([buffer, chunk]);
    const parsed = decodeWs(buffer);
    buffer = parsed.rest;
    if (parsed.close) {
      socket.end();
      return;
    }
    for (const message of parsed.messages) {
      handleBoardMessage(message, socket, ticket, state, profile).catch(err => {
        console.error(err);
        sendWs(socket, { event: "review", reason: "backend" });
      });
    }
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://rail.local");
  (async () => {
    if (req.method === "GET" && url.pathname === "/ticket/waitlist/channel") {
      await openWaitlistChannel(req, res);
      return;
    }
    if (req.method === "GET" && url.pathname === "/api/waitlist/channels") {
      await channels(req, res);
      return;
    }
    if (req.method === "GET" && url.pathname === "/api/coach/board") {
      await boardStatus(req, res);
      return;
    }
    if (req.method === "POST" && url.pathname === "/api/waitlist/pulse") {
      await pulse(req, res);
      return;
    }
    sendJson(res, 404, { error: "not_found" });
  })().catch(err => {
    console.error(err);
    sendJson(res, 500, { error: "waitlist_backend_error" });
  });
});

server.on("upgrade", (req, socket) => {
  handleUpgrade(req, socket).catch(err => {
    console.error(err);
    socket.end("HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n");
  });
});

server.listen(PORT, HOST, () => {
  console.log(`waitlist push backend on ${HOST}:${PORT}`);
});
