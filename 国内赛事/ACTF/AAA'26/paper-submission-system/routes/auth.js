const bcrypt = require('bcryptjs');
const { collections } = require('../db');
const { tokenPayload, setAuthCookie } = require('../lib/auth');
const { render } = require('../lib/helpers');

function registerAuthRoutes(app) {
  app.get('/register', (request, reply) => render(request, reply, 'register.ejs'));

  app.post('/register', async (request, reply) => {
    const { users } = collections();
    const username = String(request.body.username || '').trim();
    const email = String(request.body.email || '').trim().toLowerCase();
    const password = String(request.body.password || '');

    if (!/^[a-zA-Z0-9_-]{3,32}$/.test(username) || !email || password.length < 6) {
      return render(request, reply, 'register.ejs', {
        error: 'Choose a valid username, email, and a password of at least 6 characters.'
      });
    }

    try {
      const passwordHash = await bcrypt.hash(password, 10);
      await users.insertOne({
        username,
        email,
        passwordHash,
        role: 'user',
        affiliation: 'Independent Author, Destination TBD',
        createdAt: new Date()
      });
      return reply.redirect('/login?registered=1');
    } catch {
      return render(request, reply, 'register.ejs', { error: 'That username or email is already registered.' });
    }
  });

  app.get('/login', (request, reply) => render(request, reply, 'login.ejs', {
    message: request.query.registered ? 'Registration complete. Sign in to submit to AAA26 Big-1.' : ''
  }));

  app.post('/login', async (request, reply) => {
    const { users } = collections();
    const username = String(request.body.username || '').trim();
    const password = String(request.body.password || '');
    const user = await users.findOne({ username });

    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      return render(request, reply, 'login.ejs', { error: 'Invalid credentials.' });
    }

    setAuthCookie(reply, await app.jwt.sign(tokenPayload(user)));
    return reply.redirect('/');
  });

  app.get('/logout', async (request, reply) => {
    reply.clearCookie('token', { path: '/' });
    return reply.redirect('/');
  });
}

module.exports = registerAuthRoutes;
