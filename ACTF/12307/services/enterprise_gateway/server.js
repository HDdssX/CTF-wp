#!/usr/bin/env node
"use strict";

const http = require("http");
const net = require("net");

const REDIS_HOST = process.env.REDIS_HOST || "127.0.0.1";
const REDIS_PORT = Number(process.env.REDIS_PORT || 6379);
const HOST = process.env.NODE_HOST || "127.0.0.1";
const PORT = Number(process.env.NODE_PORT || 5005);
const SIGNER_PORT = Number(process.env.SIGNER_PORT || 5006);
const IMPORT_PORT = Number(process.env.IMPORT_PORT || 5008);

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

function parseBulk(buffer) {
  const text = buffer.toString();
  if (text.startsWith("$-1")) return "";
  const idx = text.indexOf("\r\n");
  if (!text.startsWith("$") || idx === -1) return "";
  const size = Number(text.slice(1, idx));
  return text.slice(idx + 2, idx + 2 + size);
}

function redisGet(key) {
  return new Promise(resolve => {
    const socket = net.createConnection({ host: REDIS_HOST, port: REDIS_PORT });
    const timer = setTimeout(() => {
      socket.destroy();
      resolve("");
    }, 800);
    socket.on("connect", () => socket.write(encodeCommand(["GET", key])));
    socket.on("data", chunk => {
      clearTimeout(timer);
      socket.end();
      resolve(parseBulk(chunk));
    });
    socket.on("error", () => {
      clearTimeout(timer);
      resolve("");
    });
  });
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    req.on("data", chunk => {
      total += chunk.length;
      if (total > 131072) {
        reject(new Error("request too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function sendJson(res, status, payload) {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": body.length,
  });
  res.end(body);
}

function forward(port, path, body, headers) {
  return new Promise((resolve, reject) => {
    const req = http.request({
      host: "127.0.0.1",
      port,
      path,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": body.length,
        ...headers,
      },
    }, resp => {
      const chunks = [];
      resp.on("data", chunk => chunks.push(chunk));
      resp.on("end", () => resolve({
        status: resp.statusCode || 502,
        headers: resp.headers,
        body: Buffer.concat(chunks),
      }));
    });
    req.on("error", reject);
    req.end(body);
  });
}

function laneFromCache(cachedLane) {
  try {
    const parsed = JSON.parse(cachedLane || "{}");
    return parsed && typeof parsed.routeName === "string" ? parsed.routeName.slice(0, 48) : "";
  } catch {
    return "";
  }
}

async function mergeLayoutClaim(orderId, stationCode) {
  if (!/^O[A-Z0-9]{10}$/.test(orderId)) return;
  const body = Buffer.from(JSON.stringify({
    stationCode,
    adapter: "enterprise-clearing",
    target: `rail-mesh://clearing/layout?orderId=${encodeURIComponent(orderId)}&stationCode=${encodeURIComponent(stationCode)}`,
    payload: "invoice-dispute=merged",
  }));
  try {
    await forward(IMPORT_PORT, "/station/import/probe", body, {
      "X-Enterprise-Gateway": "station-mesh",
    });
  } catch (err) {
    console.warn("layout merge deferred", err.message);
  }
}

const server = http.createServer((req, res) => {
  const path = new URL(req.url, "http://rail.local").pathname;
  (async () => {
    if (req.method === "GET" && path === "/api/enterprise/invoices") {
      sendJson(res, 200, {
        invoices: [
          { invoiceId: "E-BJP-1001", accountId: "ACCT-BJP-01", disputeState: "open", stationCode: "BJP" },
        ],
      });
      return;
    }

    if (req.method === "POST" && path === "/api/enterprise/receipts/prepare") {
      const body = await readBody(req);
      let data = {};
      try { data = JSON.parse(body.toString() || "{}"); } catch { data = {}; }
      const stationCode = String(data.stationCode || "BJP").slice(0, 16);
      const orderId = String(data.orderId || "").slice(0, 32);
      await mergeLayoutClaim(orderId, stationCode);
      const cachedLane = await redisGet(`rail:interline:lane:${stationCode}`);
      const signerLane = laneFromCache(cachedLane);
      const signerHeaders = {
        "X-Enterprise-Gateway": "station-mesh",
        "X-Partner-Shape": Array.isArray(data.trustLevel) ? "json-array" : "scalar",
      };
      if (signerLane) signerHeaders["X-Clearing-Lane"] = signerLane;
      const response = await forward(SIGNER_PORT, "/signer/receipts/prepare", body, signerHeaders);
      res.writeHead(response.status, {
        "Content-Type": response.headers["content-type"] || "application/json",
        "Content-Length": response.body.length,
      });
      res.end(response.body);
      return;
    }

    if (req.method === "POST" && path === "/api/enterprise/import/relay") {
      const body = await readBody(req);
      const response = await forward(IMPORT_PORT, "/station/import/probe", body, {
        "X-Enterprise-Gateway": "station-mesh",
      });
      res.writeHead(response.status, {
        "Content-Type": response.headers["content-type"] || "application/json",
        "Content-Length": response.body.length,
      });
      res.end(response.body);
      return;
    }

    sendJson(res, 404, { error: "not_found" });
  })().catch(err => {
    console.error(err);
    sendJson(res, 500, { error: "enterprise_gateway_error" });
  });
});

server.listen(PORT, HOST, () => {
  console.log(`enterprise gateway on ${HOST}:${PORT}`);
});
