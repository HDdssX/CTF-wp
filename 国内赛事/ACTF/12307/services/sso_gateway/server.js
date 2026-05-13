#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const http = require("http");
const net = require("net");

const REDIS_HOST = process.env.REDIS_HOST || "127.0.0.1";
const REDIS_PORT = Number(process.env.REDIS_PORT || 6379);
const HOST = process.env.NODE_HOST || "127.0.0.1";
const PORT = Number(process.env.NODE_PORT || 5002);

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

function empty(res, status, headers = {}) {
  res.writeHead(status, {
    "Content-Length": 0,
    ...headers,
  });
  res.end();
}

async function loadSession(req) {
  const cookies = parseCookies(req.headers.cookie || "");
  const sessionId = cookies.passenger_session || "";
  if (!sessionId) return { sessionId: "", data: null };
  const raw = await redisCommand("GET", `rail:sso:session:${sessionId}`);
  if (!raw) return { sessionId, data: null };
  try {
    return { sessionId, data: JSON.parse(raw) };
  } catch {
    return { sessionId, data: null };
  }
}

function textShape(value) {
  if (Array.isArray(value)) return { kind: "array", text: value.map(item => String(item)).join("|") };
  if (value && typeof value === "object") return { kind: "object", text: JSON.stringify(value) };
  return { kind: "scalar", text: String(value || "") };
}

function tagValue(xml, tag) {
  const match = String(xml || "").match(new RegExp(`<${tag}[^>]*>([^<]*)</${tag}>`, "i"));
  return match ? match[1] : "";
}

function partnerContinuation(data) {
  const metadata = textShape(data.partnerMetadata || data.metadata || "");
  const relay = textShape(data.relayState || "");
  const assertion = textShape(data.assertion || "");
  const partnerOk = metadata.text.includes("railway-partner") || metadata.text.includes("PassengerIdentityProvider");
  const audienceOk = tagValue(assertion.text, "Audience") === "12307" || assertion.text.includes("mobile-passenger");
  const nameOk = Boolean(tagValue(assertion.text, "NameID")) || assertion.text.includes("PassengerID");
  const relayOk = relay.text.includes("continue") || relay.text.includes("seat-hold");
  const legacyBridge = (
    metadata.text.includes("compatBinding") &&
    (assertion.text.includes("<Signature>RelayState</Signature>") || relay.kind !== "scalar")
  );
  return partnerOk && nameOk && relayOk && (audienceOk || legacyBridge);
}

async function continueIdentity(req, res) {
  let data;
  try {
    data = await readBody(req);
  } catch {
    sendJson(res, 400, { error: "invalid_json" });
    return;
  }

  const ok = partnerContinuation(data);
  const sessionId = crypto.randomBytes(18).toString("base64url");
  const passenger = String(data.passenger || data.name || "Passenger").slice(0, 64);
  const session = {
    state: ok ? "compat-pending" : "pending",
    trust: ok ? "partner-continuation" : "unverified",
    partnerId: String(data.partnerId || "mobile-partner").slice(0, 64),
    stationCode: String(data.stationCode || "BJP").slice(0, 16),
    trustLevel: Array.isArray(data.trustLevel) ? data.trustLevel : ["mobile", ok ? "partner" : "guest"],
    passenger,
    issuedAt: Date.now(),
  };
  await redisCommand("SET", `rail:sso:session:${sessionId}`, JSON.stringify(session), "EX", "900");

  const headers = {
    "Set-Cookie": `passenger_session=${sessionId}; Path=/; HttpOnly; SameSite=Lax`,
    "Cache-Control": "no-store",
  };
  if (ok) {
    headers["X-Accel-Redirect"] = "/_rail/identity/accepted";
  }
  sendJson(res, ok ? 202 : 401, {
    status: ok ? "continuation_accepted" : "identity_pending",
    passenger,
  }, headers);
}

async function checkSession(req, res) {
  const { data } = await loadSession(req);
  if (!data) {
    empty(res, 403);
    return;
  }
  if (data.state === "complete") {
    empty(res, 204, { "X-Session-Continuation": "complete", "Cache-Control": "no-store" });
    return;
  }
  if (data.state === "compat-pending" && data.trust === "partner-continuation") {
    empty(res, 401, { "X-Session-Continuation": "pending", "Cache-Control": "no-store" });
    return;
  }
  empty(res, 403);
}

async function completeSession(req, res) {
  const { sessionId, data } = await loadSession(req);
  if (!sessionId || !data || data.state !== "compat-pending") {
    empty(res, 403);
    return;
  }
  data.state = "complete";
  data.completedAt = Date.now();
  await redisCommand("SET", `rail:sso:session:${sessionId}`, JSON.stringify(data), "EX", "900");
  await redisCommand("SET", `rail:passenger:continuation:${sessionId}`, JSON.stringify({
    passenger: data.passenger,
    trust: data.trust,
    partnerId: data.partnerId || "mobile-partner",
    stationCode: data.stationCode || "BJP",
    trustLevel: data.trustLevel || ["mobile", "partner"],
    completedAt: data.completedAt,
  }), "EX", "900");
  empty(res, 204, { "X-Session-Continuation": "complete", "Cache-Control": "no-store" });
}

async function sessionView(req, res) {
  const { data } = await loadSession(req);
  if (!data) {
    sendJson(res, 200, { session: false, trusted: false });
    return;
  }
  sendJson(res, 200, {
    session: true,
    trusted: data.state === "complete",
    passenger: data.passenger,
  });
}

const server = http.createServer((req, res) => {
  const path = new URL(req.url, "http://rail.local").pathname;
  (async () => {
    if (req.method === "POST" && path === "/passenger/identity/continue") {
      await continueIdentity(req, res);
      return;
    }
    if (req.method === "GET" && path === "/session/check") {
      await checkSession(req, res);
      return;
    }
    if (req.method === "GET" && path === "/session/continued") {
      await completeSession(req, res);
      return;
    }
    if (req.method === "GET" && path === "/_rail/session/check" && req.headers["x-session-bridge"] === "continue") {
      await completeSession(req, res);
      return;
    }
    if (req.method === "GET" && (path === "/api/session/me" || path === "/session/me")) {
      await sessionView(req, res);
      return;
    }
    sendJson(res, 404, { error: "not_found" });
  })().catch(err => {
    console.error(err);
    sendJson(res, 500, { error: "identity_backend_error" });
  });
});

server.listen(PORT, HOST, () => {
  console.log(`sso gateway on ${HOST}:${PORT}`);
});
