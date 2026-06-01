require("dotenv").config();

const express = require("express");
const pino = require("pino");
const _ = require("lodash");
const chalk = require("chalk");
const axios = require("axios");

const db = require("./db/index.js");
const schema = require("./db/schema.js");

const app = express();
const logger = pino({ level: process.env.LOG_LEVEL || "info" });

app.use(express.json());

const PORT = process.env.PORT || 3000;
const services = {
  users: process.env.USERS_SERVICE_URL || "http://localhost:3001",
  orders: process.env.ORDERS_SERVICE_URL || "http://localhost:3002",
  inventory: process.env.INVENTORY_SERVICE_URL || "http://localhost:3003",
};

function logToDb(level, message, meta = null) {
  try {
    db.insert(schema.logs).values({
      level,
      message,
      meta: meta ? JSON.stringify(meta) : null,
    }).run();
  } catch {}
}

app.get("/", (req, res) => {
  res.json({
    service: "api-gateway",
    version: "1.0.0",
    status: "running",
    timestamp: new Date().toISOString(),
    endpoints: [
      "/health",
      "/users",
      "/orders",
      "/inventory",
      "/logs",
      "/proxy",
    ],
  });
});

app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    database: "connected",
  });
});

app.get("/users", async (req, res) => {
  try {
    const allUsers = db.select().from(schema.users).all();
    logToDb("info", "Fetched all users", { count: allUsers.length });
    res.json({ users: allUsers, total: allUsers.length });
  } catch (error) {
    logger.error({ err: error }, "Failed to fetch users");
    logToDb("error", "Failed to fetch users", { error: error.message });
    res.status(503).json({ error: "Service unavailable", details: error.message });
  }
});

app.post("/users", async (req, res) => {
  try {
    const { email, name } = req.body;
    if (!email || !name) {
      return res.status(400).json({ error: "email and name are required" });
    }
    const result = db.insert(schema.users).values({ email, name }).returning().get();
    logToDb("info", "Created new user", { userId: result.id, email });
    res.status(201).json(result);
  } catch (error) {
    logger.error({ err: error }, "Failed to create user");
    logToDb("error", "Failed to create user", { error: error.message });
    res.status(500).json({ error: "Failed to create user", details: error.message });
  }
});

app.get("/orders", async (req, res) => {
  try {
    const allOrders = db.select().from(schema.orders).all();
    logToDb("info", "Fetched all orders", { count: allOrders.length });
    res.json({ orders: allOrders, total: allOrders.length });
  } catch (error) {
    logger.error({ err: error }, "Failed to fetch orders");
    logToDb("error", "Failed to fetch orders", { error: error.message });
    res.status(503).json({ error: "Service unavailable", details: error.message });
  }
});

app.post("/orders", async (req, res) => {
  try {
    const { userId, product, amount } = req.body;
    if (!userId || !product || amount === undefined) {
      return res.status(400).json({ error: "userId, product, and amount are required" });
    }
    const result = db.insert(schema.orders).values({
      userId,
      product,
      amount,
      status: "pending",
    }).returning().get();
    logToDb("info", "Created new order", { orderId: result.id, userId, product });
    res.status(201).json(result);
  } catch (error) {
    logger.error({ err: error }, "Failed to create order");
    logToDb("error", "Failed to create order", { error: error.message });
    res.status(500).json({ error: "Failed to create order", details: error.message });
  }
});

app.patch("/orders/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;
    if (!status) {
      return res.status(400).json({ error: "status is required" });
    }
    const result = db.update(schema.orders)
      .set({ status })
      .where(require("drizzle-orm").eq(schema.orders.id, parseInt(id)))
      .returning()
      .get();
    logToDb("info", "Updated order status", { orderId: id, status });
    res.json(result);
  } catch (error) {
    logger.error({ err: error }, "Failed to update order");
    res.status(500).json({ error: "Failed to update order", details: error.message });
  }
});

app.get("/inventory", async (req, res) => {
  try {
    const allItems = db.select().from(schema.inventory).all();
    logToDb("info", "Fetched all inventory", { count: allItems.length });
    res.json({ inventory: allItems, total: allItems.length });
  } catch (error) {
    logger.error({ err: error }, "Failed to fetch inventory");
    logToDb("error", "Failed to fetch inventory", { error: error.message });
    res.status(503).json({ error: "Service unavailable", details: error.message });
  }
});

app.post("/inventory", async (req, res) => {
  try {
    const { sku, name, quantity, price } = req.body;
    if (!sku || !name || quantity === undefined || price === undefined) {
      return res.status(400).json({ error: "sku, name, quantity, and price are required" });
    }
    const result = db.insert(schema.inventory).values({ sku, name, quantity, price }).returning().get();
    logToDb("info", "Created inventory item", { itemId: result.id, sku });
    res.status(201).json(result);
  } catch (error) {
    logger.error({ err: error }, "Failed to create inventory item");
    logToDb("error", "Failed to create inventory item", { error: error.message });
    res.status(500).json({ error: "Failed to create inventory item", details: error.message });
  }
});

app.get("/logs", (req, res) => {
  try {
    const { level, limit = 50 } = req.query;
    let query = db.select().from(schema.logs).orderBy(require("drizzle-orm").desc(schema.logs.createdAt)).limit(parseInt(limit));
    if (level) {
      query = query.where(require("drizzle-orm").eq(schema.logs.level, level));
    }
    const allLogs = query.all();
    res.json({ logs: allLogs, total: allLogs.length });
  } catch (error) {
    logger.error({ err: error }, "Failed to fetch logs");
    res.status(500).json({ error: "Failed to fetch logs", details: error.message });
  }
});

app.post("/proxy", async (req, res) => {
  const { target, method = "GET", path = "/", data = null } = req.body;

  if (!target) {
    return res.status(400).json({ error: "target is required" });
  }

  const url = _.trimEnd(target, "/") + path;

  try {
    let response;
    if (method.toUpperCase() === "POST") {
      response = await axios.post(url, data);
    } else {
      response = await axios.get(url);
    }
    logToDb("info", "Proxy request successful", { target: url, method, status: response.status });
    res.json({ success: true, status: response.status, data: response.data });
  } catch (error) {
    logger.error({ err: error }, "Proxy request failed");
    logToDb("error", "Proxy request failed", { target: url, error: error.message });
    res.status(502).json({ error: "Bad gateway", details: error.message });
  }
});

app.listen(PORT, () => {
  console.log(chalk.green(`API Gateway running on port ${PORT}`));
  console.log(chalk.blue(`Logging level: ${logger.level}`));
  console.log(chalk.yellow(`Environment: ${process.env.NODE_ENV || "development"}`));
  logToDb("info", "API Gateway started", { port: PORT });
});

module.exports = app;
