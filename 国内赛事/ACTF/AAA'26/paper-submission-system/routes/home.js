const { collections } = require('../db');
const {
  asObjectId,
  decoratePaperRows,
  render
} = require('../lib/helpers');

function registerHomeRoutes(app, auth) {
  app.get('/', { preHandler: auth.optionalAuth }, async (request, reply) => {
    if (!request.user) return render(request, reply, 'index.ejs');

    const { papers, reviews, assignments } = collections();
    const ownerId = asObjectId(request.user.id);
    const [myPapers, reviewCount, assignmentCount] = await Promise.all([
      ownerId ? papers.find({ ownerId }).sort({ createdAt: -1 }).limit(5).toArray() : [],
      reviews.countDocuments({ reviewerId: ownerId }),
      assignments.countDocuments({ reviewerId: ownerId })
    ]);

    return render(request, reply, 'dashboard.ejs', {
      papers: await decoratePaperRows(myPapers),
      reviewCount,
      assignmentCount
    });
  });

  app.get('/program', { preHandler: auth.optionalAuth }, async (request, reply) => {
    const { papers } = collections();
    const rows = await papers.find({
      status: 'Accepted',
      'cameraReady.preparedAt': { $exists: true }
    }).sort({ title: 1 }).toArray();

    return render(request, reply, 'program.ejs', {
      papers: await decoratePaperRows(rows)
    });
  });
}

module.exports = registerHomeRoutes;
