const config = require('../lib/config');
const { collections } = require('../db');
const {
  asObjectId,
  decoratePaperRows,
  render,
  paperWithOwner
} = require('../lib/helpers');

function registerAdminRoutes(app, auth) {
  app.get('/admin/papers', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { papers } = collections();
    const rows = await papers.find({}).sort({ createdAt: -1 }).toArray();
    return render(request, reply, 'admin/list.ejs', { papers: await decoratePaperRows(rows) });
  });

  app.get('/admin/papers/:id/status', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');
    return render(request, reply, 'admin/editStatus.ejs', { paper, statuses: config.decisionStatuses });
  });

  app.post('/admin/papers/:id/status', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { papers } = collections();
    const paperId = asObjectId(request.params.id);
    const status = config.decisionStatuses.includes(request.body.status) ? request.body.status : 'Rejected';
    if (paperId) {
      await papers.updateOne({ _id: paperId }, { $set: { status, decidedAt: new Date(), decidedBy: request.user.username } });
    }
    return reply.redirect('/admin/papers');
  });

  app.get('/admin/users', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { users } = collections();
    const rows = await users.find({}).sort({ role: 1, username: 1 }).toArray();
    return render(request, reply, 'admin/users.ejs', { users: rows });
  });

  app.post('/admin/users/:id/role', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { users } = collections();
    const userId = asObjectId(request.params.id);
    const role = ['user', 'reviewer', 'admin'].includes(request.body.role) ? request.body.role : 'user';
    if (userId) await users.updateOne({ _id: userId }, { $set: { role } });
    return reply.redirect('/admin/users');
  });

  app.get('/admin/reviewer-invites', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { reviewerInvites } = collections();
    const invites = await reviewerInvites.find({}).sort({ createdAt: -1 }).toArray();
    return render(request, reply, 'admin/invites.ejs', { invites });
  });

  app.get('/admin/service-desk', { preHandler: auth.requireRole('admin') }, async (request, reply) => {
    const { reviewerServiceSyncs } = collections();
    const syncs = await reviewerServiceSyncs.find({}).sort({ createdAt: -1 }).limit(100).toArray();
    return render(request, reply, 'admin/serviceDesk.ejs', { syncs });
  });
}

module.exports = registerAdminRoutes;
