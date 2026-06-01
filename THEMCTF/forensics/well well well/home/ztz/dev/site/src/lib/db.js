import { drizzle } from "drizzle-orm/d1";
import * as schema from "./src/db/schema.js";

const db = drizzle(process.env.DB, { schema });

export default db;