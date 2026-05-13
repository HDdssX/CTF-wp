const { ObjectId, collections } = require('../db');
const { tokenPayload, setAuthCookie } = require('../lib/auth');
const { filterReviewerDocuments } = require('../lib/filters');
const {
  readReviewerProfile,
  saveReviewerProfile,
  submitReviewerProfile,
  syncReviewerServiceSlot,
  reviewerProfileView
} = require('../lib/profileImport');
const {
  render,
  paperWithOwner,
  reviewerDocuments
} = require('../lib/helpers');
const { assignBacklogToReviewer } = require('../lib/papers');

function inviteEmail(value) {
  const email = String(value || '').trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new Error('invalid email');
  return email;
}

function inviteCode(value) {
  const code = String(value || '').trim().toLowerCase();
  if (!/^[0-9a-f]{36}$/.test(code)) throw new Error('invalid code');
  return code;
}

async function enableReviewer(app, reply, userId) {
  const { users } = collections();
  const id = new ObjectId(userId);

  await users.updateOne(
    { _id: id, role: { $ne: 'admin' } },
    { $set: { role: 'reviewer', reviewerSince: new Date() } }
  );
  await assignBacklogToReviewer(id);

  const updated = await users.findOne({ _id: id });
  setAuthCookie(reply, await app.jwt.sign(tokenPayload(updated)));
  return updated;
}

async function renderReviewerProfile(request, reply, data = {}) {
  const viewData = await reviewerProfileView(request.user.id);
  return render(request, reply, 'reviewer/profile.ejs', { ...viewData, ...data });
}

function registerReviewerRoutes(app, auth) {
  app.get('/reviewer/claim', { preHandler: auth.authenticate }, (request, reply) => render(request, reply, 'reviewer/claim.ejs'));

  app.post('/reviewer/claim', { preHandler: auth.authenticate }, async (request, reply) => {
    const { reviewerInvites } = collections();
    const body = request.body || {};
    let email;
    let code;

    try {
      email = inviteEmail(body.email);
      code = inviteCode(body.code);
    } catch {
      return render(request, reply, 'reviewer/claim.ejs', { error: 'No matching reviewer invitation was found.' });
    }

    const invite = await reviewerInvites.findOne({
      email,
      code,
      used: false
    });

    if (!invite) {
      return render(request, reply, 'reviewer/claim.ejs', { error: 'No matching reviewer invitation was found.' });
    }

    const userId = new ObjectId(request.user.id);
    await reviewerInvites.updateOne({ _id: invite._id }, { $set: { used: true, usedBy: userId, usedAt: new Date() } });
    await enableReviewer(app, reply, userId);
    return reply.redirect('/reviewer/assignments?claimed=1');
  });

  app.get('/reviewer/profile', { preHandler: auth.authenticate }, (request, reply) => {
    return renderReviewerProfile(request, reply);
  });

  app.post('/reviewer/profile', { preHandler: auth.authenticate }, async (request, reply) => {
    try {
      const profile = await readReviewerProfile(request);
      const result = await saveReviewerProfile(request.user.id, profile);
      return renderReviewerProfile(request, reply, {
        message: result.serviceRecord
          ? 'Reviewer profile saved. Service record queued for committee sync.'
          : 'Reviewer profile saved.'
      });
    } catch {
      return renderReviewerProfile(request, reply, {
        error: 'Reviewer profile could not be imported.'
      });
    }
  });

  app.post('/reviewer/profile/submit', { preHandler: auth.authenticate }, async (request, reply) => {
    const result = await submitReviewerProfile(request.user.id);
    return renderReviewerProfile(request, reply, result.ok ? { message: result.message } : { error: result.message });
  });

  app.post('/reviewer/profile/service-sync', { preHandler: auth.authenticate }, async (request, reply) => {
    const result = await syncReviewerServiceSlot(request.user.id);
    return renderReviewerProfile(request, reply, { message: result.message });
  });

  app.get('/reviewer/assignments', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const docs = await reviewerDocuments(request.user);
    return render(request, reply, 'reviewer/assignments.ejs', {
      docs,
      message: request.query.claimed || request.query.profile ? 'Reviewer console enabled. Assignments have been synchronized.' : ''
    });
  });

  app.get('/reviewer/papers/:id/review', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const { reviews } = collections();
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');
    const review = await reviews.findOne({ paperId: paper._id, reviewerId: new ObjectId(request.user.id) });
    return render(request, reply, 'reviewer/review.ejs', { paper, review });
  });

  app.post('/reviewer/papers/:id/review', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const { reviews } = collections();
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');

    const score = Math.max(1, Math.min(10, Number(request.body.score || 1)));
    const confidence = Math.max(1, Math.min(5, Number(request.body.confidence || 1)));
    const recommendation = String(request.body.recommendation || 'Reject').slice(0, 40);
    const comments = String(request.body.comments || '').slice(0, 4000);

    await reviews.updateOne(
      { paperId: paper._id, reviewerId: new ObjectId(request.user.id) },
      {
        $set: {
          paperId: paper._id,
          reviewerId: new ObjectId(request.user.id),
          score,
          confidence,
          recommendation,
          comments,
          updatedAt: new Date()
        },
        $setOnInsert: { createdAt: new Date() }
      },
      { upsert: true }
    );

    return reply.redirect('/reviewer/assignments');
  });

  app.get('/reviewer/search', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const docs = await reviewerDocuments(request.user);
    return render(request, reply, 'reviewer/search.ejs', {
      expression: 'scores.averageScore === null || scores.averageScore < 7',
      docs,
      filtered: false
    });
  });

  app.post('/reviewer/search', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const expression = String(request.body.expression || '');
    try {
      const docs = await filterReviewerDocuments(app, request, expression);
      return render(request, reply, 'reviewer/search.ejs', { expression, docs, filtered: true });
    } catch {
      return render(request, reply, 'reviewer/search.ejs', {
        expression,
        docs: [],
        filtered: true,
        error: 'Filter rejected.'
      });
    }
  });

  app.post('/api/reviewer/filter', { preHandler: auth.requireRole('reviewer') }, async (request, reply) => {
    const expression = String((request.body && request.body.expression) || '');
    try {
      const docs = await filterReviewerDocuments(app, request, expression);
      return reply.send({
        ok: true,
        count: docs.length,
        results: docs.map((doc) => ({
          paper: doc.paper,
          review: doc.review,
          reviewer: doc.reviewer,
          scores: doc.scores
        }))
      });
    } catch {
      return reply.code(200).send({ ok: false, count: 0, results: [] });
    }
  });
}

module.exports = registerReviewerRoutes;
