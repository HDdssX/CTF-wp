import dotenv from 'dotenv';
import express, { Request, Response, NextFunction } from 'express';
import cookieParser from 'cookie-parser';
import { MongoClient, Db, Collection } from 'mongodb';
import crypto from 'crypto';
import path from 'path';
import puppeteer from 'puppeteer';

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT) || 3000;

const mongoUri = process.env.MONGO_URI || process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/easy_login';
const dbName = process.env.MONGO_DB_NAME || 'easy_login';
const FLAG = process.env.FLAG || 'flag{dummy_flag_for_testing}';
const APP_INTERNAL_URL = process.env.APP_INTERNAL_URL || `http://127.0.0.1:${PORT}`;
const ADMIN_PASSWORD = crypto.randomBytes(16).toString('hex');

interface UserDoc {
  username: string;
  password: string;
}

interface SessionDoc {
  sid: string;
  username: string;
  createdAt: Date;
}

interface AuthedRequest extends Request {
  user?: { username: string } | null;
  collections?: {
    users: Collection<UserDoc> | null;
    sessions: Collection<SessionDoc> | null;
  };
}

let db: Db | null = null;
let usersCollection: Collection<UserDoc> | null = null;
let sessionsCollection: Collection<SessionDoc> | null = null;

const publicDir = path.join(__dirname, '../public');

async function runXssVisit(targetUrl: string): Promise<void> {
  if (typeof targetUrl !== 'string' || !/^https?:\/\//i.test(targetUrl)) {
    throw new Error('invalid target url');
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    await page.goto(APP_INTERNAL_URL + '/', {
      waitUntil: 'networkidle2',
      timeout: 15000
    });

    await page.type('#username', 'admin', { delay: 30 });
    await page.type('#password', ADMIN_PASSWORD, { delay: 30 });

    await Promise.all([
      page.click('#loginForm button[type="submit"]'),
      page.waitForResponse(
        (res) => res.url().endsWith('/login') && res.request().method() === 'POST',
        { timeout: 10000 }
      ).catch(() => undefined)
    ]);

    await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 15000 });

    await new Promise((resolve) => setTimeout(resolve, 5000));
  } finally {
    await browser.close();
  }
}

async function createSessionForUser(user: UserDoc): Promise<string> {
  if (!sessionsCollection) {
    throw new Error('sessions collection not initialized');
  }

  const sid = crypto.randomBytes(16).toString('hex');

  await sessionsCollection.insertOne({
    sid,
    username: user.username,
    createdAt: new Date()
  });

  return sid;
}

app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(publicDir));

async function initMongo(): Promise<void> {
  const client = new MongoClient(mongoUri);
  await client.connect();
  db = client.db(dbName);
  usersCollection = db.collection<UserDoc>('users');
  sessionsCollection = db.collection<SessionDoc>('sessions');

  let adminUser = await usersCollection.findOne({ username: 'admin' });
  if (!adminUser) {
    await usersCollection.insertOne({
      username: 'admin',
      password: ADMIN_PASSWORD
    });
  } else {
    await usersCollection.updateOne(
      { username: 'admin' },
      { $set: { password: ADMIN_PASSWORD } }
    );
  }

  adminUser = await usersCollection.findOne({ username: 'admin' });
  console.log(`[init] Admin password set to: ${ADMIN_PASSWORD}`);
}

async function sessionMiddleware(req: AuthedRequest, res: Response, next: NextFunction): Promise<void> {
  const sid = req.cookies?.sid as string | undefined;
  if (!sid || !sessionsCollection || !usersCollection) {
    req.user = null;
    return next();
  }

  try {
    const session = await sessionsCollection.findOne({ sid });
    if (!session) {
      req.user = null;
      return next();
    }

    const user = await usersCollection.findOne({ username: session.username });
    if (!user) {
      req.user = null;
      return next();
    }

    req.user = { username: user.username };
    return next();
  } catch (err) {
    console.error('Error in session middleware:', err);
    req.user = null;
    return next();
  }
}

app.use((req: AuthedRequest, _res: Response, next: NextFunction) => {
  req.collections = {
    users: usersCollection,
    sessions: sessionsCollection
  };
  next();
});

app.use(sessionMiddleware as any);

app.get('/', (_req: AuthedRequest, res: Response) => {
  res.sendFile(path.join(publicDir, 'index.html'));
});

app.post('/login', async (req: AuthedRequest, res: Response) => {
  const { username, password } = req.body as { username?: unknown; password?: unknown };
  
  if (typeof username !== 'string' || typeof password !== 'string') {
    return res.status(400).json({ error: 'username and password must be strings' });
  }

  if (!username || !password) {
    return res.status(400).json({ error: 'username and password required' });
  }

  if (!usersCollection) {
    return res.status(500).json({ error: 'Database not initialized yet' });
  }
  
  try {
    let user = await usersCollection.findOne({ username });

    if (!user) {
      if (username === 'admin') {
        return res.status(403).json({ error: 'admin user not available' });
      }
      await usersCollection.insertOne({ username, password });
      user = await usersCollection.findOne({ username });
    }

    if (!user || user.password !== password) {
      return res.status(401).json({ error: 'invalid credentials' });
    }

    const sid = await createSessionForUser(user);

    res.cookie('sid', sid, {
      httpOnly: false,
      sameSite: 'lax'
    });

    return res.json({
      ok: true,
      sid,
      username: user.username
    });
  } catch (err) {
    console.error('Error in /login:', err);
    return res.status(500).json({ error: 'internal error' });
  }
});

app.post('/logout', async (req: AuthedRequest, res: Response) => {
  res.clearCookie('sid');
  res.json({ ok: true });
});

app.get('/me', (req: AuthedRequest, res: Response) => {
  if (!req.user) {
    return res.json({ loggedIn: false });
  }
  res.json({
    loggedIn: true,
    username: req.user.username
  });
});

app.get('/admin', (req: AuthedRequest, res: Response) => {
  if (!req.user || req.user.username !== 'admin') {
    return res.status(403).json({ error: 'admin only' });
  }

  res.json({ flag: FLAG });
});
app.post('/visit', async (req: Request, res: Response) => {
  const { url } = req.body as { url?: unknown };

  if (typeof url !== 'string') {
    return res.status(400).json({ error: 'url must be a string' });
  }

  try {
    await runXssVisit(url);
    return res.json({ ok: true });
  } catch (err: any) {
    console.error('XSS bot error:', err);
    return res.status(500).json({ error: 'bot failed', detail: String(err) });
  }
});

initMongo()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server listening on port ${PORT}`);
    });
  })
  .catch((err: unknown) => {
    console.error('Failed to initialize MongoDB:', err);
    process.exit(1);
  });
