const config = require('./config');

const rank = { user: 1, reviewer: 2, admin: 3 };

function tokenPayload(user) {
  return {
    id: user._id.toString(),
    username: user.username,
    role: user.role || 'user'
  };
}

function setAuthCookie(reply, token) {
  reply.setCookie('token', token, {
    path: '/',
    httpOnly: true,
    sameSite: 'lax',
    maxAge: 24 * 60 * 60
  });
}

function getBearerOrCookie(request) {
  const auth = request.headers.authorization || '';
  if (auth.startsWith('Bearer ')) return auth.slice(7);
  return request.cookies && request.cookies.token;
}

function resolveJwtSecret(_request, payloadOrCallback, callback) {
  const done = typeof callback === 'function' ? callback : payloadOrCallback;
  if (typeof done === 'function') {
    done(null, config.jwtSecret);
    return;
  }

  return config.jwtSecret;
}

function wantsJson(request) {
  return request.url.startsWith('/api/') || String(request.headers.accept || '').includes('application/json');
}

function createAuth(app) {
  async function optionalAuth(request, reply) {
    const token = getBearerOrCookie(request);
    if (!token) return;

    try {
      request.user = await app.jwt.verify(token);
    } catch {
      reply.clearCookie('token', { path: '/' });
    }
  }

  async function authenticate(request, reply) {
    const token = getBearerOrCookie(request);
    if (!token) {
      if (wantsJson(request)) return reply.code(401).send({ error: 'authentication required' });
      return reply.redirect('/login');
    }

    try {
      request.user = await app.jwt.verify(token);
    } catch {
      if (wantsJson(request)) return reply.code(401).send({ error: 'invalid token' });
      reply.clearCookie('token', { path: '/' });
      return reply.redirect('/login');
    }
  }

  function requireRole(role) {
    return async function roleGuard(request, reply) {
      await authenticate(request, reply);
      if (reply.sent) return;

      const current = request.user && request.user.role;
      if ((rank[current] || 0) < rank[role]) {
        if (wantsJson(request)) return reply.code(403).send({ error: 'forbidden' });
        return reply.code(403).send('Forbidden');
      }
    };
  }

  return { optionalAuth, authenticate, requireRole };
}

module.exports = {
  createAuth,
  tokenPayload,
  setAuthCookie,
  getBearerOrCookie,
  resolveJwtSecret
};
