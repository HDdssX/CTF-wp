#!/usr/bin/env node
"use strict";

const http = require("http");
const net = require("net");

const HOST = process.env.NODE_HOST || "127.0.0.1";
const PORT = Number(process.env.NODE_PORT || 5010);
const WORKFLOWS = [
  { method: "GET", path: "/api/mobile/workspace", port: 5000, target: "/api/workspace" },
  { method: "GET", path: "/api/mobile/search", port: 5000, target: "/api/trains" },
  { method: "GET", path: "/api/mobile/session", port: 5002, target: "/api/session/me" },
  { method: "POST", path: "/api/mobile/identity/continue", port: 5002, target: "/passenger/identity/continue" },
  { method: "POST", path: "/api/mobile/orders", port: 5000, target: "/api/orders" },
  { method: "GET", path: "/api/mobile/waitlist/channels", port: 5001, target: "/api/waitlist/channels" },
  { method: "POST", path: "/api/mobile/waitlist/pulse", port: 5001, target: "/api/waitlist/pulse" },
  { method: "GET", path: "/api/mobile/coach/board", port: 5001, target: "/api/coach/board" },
  { method: "GET", path: "/api/mobile/notices", port: 5003, target: "/api/station-office/notices" },
  { method: "GET", path: "/api/desk/notices", port: 5003, target: "/api/station-office/notices" },
  { method: "POST", path: "/api/desk/notices", port: 5003, target: "/api/station-office/notices" },
  { method: "GET", path: "/api/desk/tickets/search", port: 5003, target: "/api/station-office/tickets/search" },
  { method: "POST", path: "/api/desk/tickets/adjust", port: 5003, target: "/api/station-office/tickets/adjust" },
  { method: "POST", path: "/api/desk/fares/reprice", port: 5003, target: "/api/station-office/fares/reprice" },
  { method: "POST", path: "/api/desk/imports/health", port: 5003, target: "/api/station-office/health/import" },
  { method: "GET", path: "/api/desk/reconciliation/metadata", port: 5003, target: "/api/station-office/reconciliation/metadata" },
  { method: "POST", path: "/api/desk/reconciliation/metadata", port: 5003, target: "/api/station-office/reconciliation/metadata" },
  { method: "GET", path: "/api/corporate/invoices", port: 5005, target: "/api/enterprise/invoices" },
  { method: "POST", path: "/api/corporate/receipts/prepare", port: 5005, target: "/api/enterprise/receipts/prepare" },
  { method: "POST", path: "/api/corporate/imports/relay", port: 5005, target: "/api/enterprise/import/relay" },
  { method: "POST", path: "/api/corporate/settlement/schedule", port: 5007, target: "/api/settlement/schedule" },
  { method: "POST", path: "/api/corporate/reconciliation", port: 5004, target: "/api/fare-samples/reconciliation" },
  { method: "GET", pathPrefix: "/api/corporate/reconciliation/", port: 5004, targetPrefix: "/api/fare-samples/reconciliation/" },
];

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

function sendJson(res, status, payload, headers = {}) {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": body.length,
    ...headers,
  });
  res.end(body);
}

function routeFor(method, pathname) {
  for (const route of WORKFLOWS) {
    if (route.method !== method) continue;
    if (route.path && route.path === pathname) return route;
    if (route.pathPrefix && pathname.startsWith(route.pathPrefix)) return route;
  }
  return null;
}

function targetPath(route, reqUrl) {
  const url = new URL(reqUrl, "http://rail.local");
  if (route.pathPrefix) {
    const suffix = url.pathname.slice(route.pathPrefix.length);
    return `${route.targetPrefix}${suffix}${url.search || ""}`;
  }
  return `${route.target}${url.search || ""}`;
}

function proxy(port, target, method, body, reqHeaders, extraHeaders = {}) {
  return new Promise((resolve, reject) => {
    const headers = {
      "Content-Length": body.length,
      "Content-Type": reqHeaders["content-type"] || "application/json",
      "Cookie": reqHeaders.cookie || "",
      "Host": reqHeaders.host || "rail.local",
      "X-Forwarded-For": reqHeaders["x-forwarded-for"] || "",
      "X-Forwarded-Proto": reqHeaders["x-forwarded-proto"] || "http",
      ...extraHeaders,
    };
    const upstream = http.request({ host: "127.0.0.1", port, path: target, method, headers }, resp => {
      const chunks = [];
      resp.on("data", chunk => chunks.push(chunk));
      resp.on("end", () => resolve({
        status: resp.statusCode || 502,
        headers: resp.headers,
        body: Buffer.concat(chunks),
      }));
    });
    upstream.on("error", reject);
    upstream.end(body);
  });
}

function relayResponse(res, upstream) {
  const headers = {
    "Content-Type": upstream.headers["content-type"] || "application/json",
    "Content-Length": upstream.body.length,
  };
  if (upstream.headers["set-cookie"]) headers["Set-Cookie"] = upstream.headers["set-cookie"];
  if (upstream.headers["cache-control"]) headers["Cache-Control"] = upstream.headers["cache-control"];
  res.writeHead(upstream.status, headers);
  res.end(upstream.body);
}

async function holdFlow(req, res, body) {
  const check = await proxy(5002, "/session/check", "GET", Buffer.alloc(0), req.headers);
  let seatHoldClass = "";
  if (check.status === 204 && check.headers["x-session-continuation"] === "complete") {
    seatHoldClass = "quota-sync";
  } else if (check.status === 401 && check.headers["x-session-continuation"] === "pending") {
    const continued = await proxy(5002, "/_rail/session/check", "GET", Buffer.alloc(0), req.headers, {
      "X-Session-Bridge": "continue",
    });
    if (continued.status === 204) seatHoldClass = "quota-sync";
  }

  const held = await proxy(5000, "/orders/hold", "POST", body, req.headers, {
    "X-Seat-Hold-Class": seatHoldClass,
  });
  if (held.status !== 409) {
    relayResponse(res, held);
    return;
  }
  const channel = await proxy(5001, "/ticket/waitlist/channel", "GET", Buffer.alloc(0), req.headers, {
    "X-Ticket-Flow": "waitlist-channel",
  });
  relayResponse(res, channel);
}

async function decoyWorkflow(req, res, pathname, method, body) {
  const payload = body.length ? body : Buffer.from("{}");
  async function record(adapter, stationCode, target, response) {
    const importBody = Buffer.from(JSON.stringify({
      stationCode,
      adapter,
      target,
      payload: payload.toString("utf8").slice(0, 1200),
    }));
    try {
      await proxy(5008, "/station/import/probe", "POST", importBody, req.headers, {
        "X-Enterprise-Gateway": "station-mesh",
      });
    } catch {
      // The public workflow is eventually consistent; local import failures are surfaced in desk reconciliation.
    }
    sendJson(res, response.status, response.payload);
  }
  if (pathname === "/api/mobile/refunds/quote" && method === "POST") {
    await record("refund-window-review", "HGH", "rail-mesh://refunds/quote", {
      status: 200,
      payload: { quote: { state: "counter_review", refundRatio: 0.8, expiresIn: 120 } },
    });
    return true;
  }
  if (pathname === "/api/mobile/orders/change" && method === "POST") {
    await record("seat-change-roster", "BJP", "rail-mesh://seat-plan/change", {
      status: 202,
      payload: { change: { state: "seat_plan_review", windowSeconds: 180 } },
    });
    return true;
  }
  if (pathname === "/api/desk/incidents/feed" && method === "POST") {
    await record("incident-roster-feed", "IZQ", "rail-mesh://incidents/roster", {
      status: 202,
      payload: { feed: { state: "queued", lane: "incident-roster" } },
    });
    return true;
  }
  if (pathname === "/api/desk/baggage/handoff" && method === "POST") {
    await record("baggage-transfer-bay", "NKH", "rail-mesh://baggage/handoff", {
      status: 202,
      payload: { handoff: { state: "matched", bay: "B2" } },
    });
    return true;
  }
  if (pathname === "/api/corporate/invoices/dispute" && method === "POST") {
    await record("invoice-dispute-review", "HGH", "rail-mesh://invoices/dispute", {
      status: 202,
      payload: { dispute: { state: "audit_hold", reason: "carrier-window" } },
    });
    return true;
  }
  if (pathname === "/api/corporate/vouchers/meal" && method === "GET") {
    await record("voucher-clearance-preview", "SHH", "rail-mesh://vouchers/meal", {
      status: 200,
      payload: { vouchers: [{ stationCode: "SHH", state: "review" }] },
    });
    return true;
  }
  return false;
}

async function handleRequest(req, res) {
  const url = new URL(req.url, "http://rail.local");
  if (req.method === "GET" && !url.pathname.startsWith("/api/")) {
    sendJson(res, 404, { error: "not_found" });
    return;
  }
  const body = await readBody(req);
  if (req.method === "POST" && url.pathname === "/api/mobile/orders/hold") {
    await holdFlow(req, res, body);
    return;
  }
  if (await decoyWorkflow(req, res, url.pathname, req.method, body)) {
    return;
  }
  const route = routeFor(req.method, url.pathname);
  if (!route) {
    sendJson(res, 404, { error: "not_found" });
    return;
  }
  const upstream = await proxy(route.port, targetPath(route, req.url), req.method, body, req.headers);
  relayResponse(res, upstream);
}

function handleUpgrade(req, socket, head) {
  const url = new URL(req.url, "http://rail.local");
  if (url.pathname !== "/api/connect/boarding") {
    socket.end("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n");
    return;
  }
  const cookies = parseCookies(req.headers.cookie || "");
  const backend = net.createConnection({ host: "127.0.0.1", port: 5001 });
  backend.on("connect", () => {
    const headers = [
      `GET /api/coach/board${url.search || ""} HTTP/1.1`,
      `Host: ${req.headers.host || "rail.local"}`,
      `Upgrade: ${req.headers.upgrade || "websocket"}`,
      `Connection: ${req.headers.connection || "Upgrade"}`,
      `Sec-WebSocket-Version: ${req.headers["sec-websocket-version"] || ""}`,
      `Sec-WebSocket-Key: ${req.headers["sec-websocket-key"] || ""}`,
      `Cookie: ${req.headers.cookie || ""}`,
      `X-Waitlist-Session: ${cookies.waitlist_session || ""}`,
      "",
      "",
    ].join("\r\n");
    backend.write(headers);
    if (head && head.length) backend.write(head);
    socket.pipe(backend).pipe(socket);
  });
  backend.on("error", () => {
    socket.end("HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n");
  });
}

const server = http.createServer((req, res) => {
  handleRequest(req, res).catch(err => {
    console.error(err);
    sendJson(res, 500, { error: "gateway_review" });
  });
});

server.on("upgrade", handleUpgrade);

server.listen(PORT, HOST, () => {
  console.log(`edge gateway on ${HOST}:${PORT}`);
});
