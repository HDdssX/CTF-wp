const Database = require("better-sqlite3");
const { drizzle } = require("drizzle-orm/better-sqlite3");
const schema = require("./schema.js");

const sqlite = new Database("api-gateway.db");
const db = drizzle(sqlite, { schema });

module.exports = db;