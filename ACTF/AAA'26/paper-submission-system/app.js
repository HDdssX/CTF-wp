const path = require('path');
const fastifyFactory = require('fastify');
const formbody = require('@fastify/formbody');
const multipart = require('@fastify/multipart');
const fastifyStatic = require('@fastify/static');
const view = require('@fastify/view');
const cookie = require('@fastify/cookie');
const jwt = require('@fastify/jwt');
const ejs = require('ejs');

const config = require('./lib/config');
const { connectDatabase, closeDatabase } = require('./db');
const { createAuth, resolveJwtSecret } = require('./lib/auth');
const { seedDatabase } = require('./lib/seed');
const { ensureDirectories } = require('./lib/helpers');
const { registerRoutes } = require('./routes');

const app = fastifyFactory({ logger: false });
const auth = createAuth(app);

async function registerPlugins() {
  await app.register(formbody);
  await app.register(cookie);
  await app.register(jwt, { secret: resolveJwtSecret, sign: { expiresIn: '24h' } });
  await app.register(multipart, { limits: { fileSize: 8 * 1024 * 1024, files: 1 } });
  await app.register(fastifyStatic, { root: config.publicDir, prefix: '/public/' });
  await app.register(view, { engine: { ejs }, root: path.join(config.rootDir, 'views') });
}

async function main() {
  ensureDirectories();
  await connectDatabase();
  await seedDatabase();
  await registerPlugins();
  registerRoutes(app, auth);
  await app.listen({ port: config.port, host: config.host });
  console.log(`[AAA26] Fastify listening on http://${config.host}:${config.port}`);
}

main().catch(async (error) => {
  console.error(error);
  await closeDatabase();
  process.exit(1);
});
