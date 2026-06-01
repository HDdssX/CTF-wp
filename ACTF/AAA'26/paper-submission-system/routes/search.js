const { collections } = require('../db');
const { filterAuthorPapers } = require('../lib/filters');
const {
  asObjectId,
  decoratePaperRows,
  render
} = require('../lib/helpers');

function registerSearchRoutes(app, auth) {
  app.get('/search', { preHandler: auth.authenticate }, async (request, reply) => {
    const { papers } = collections();
    const ownerId = asObjectId(request.user.id);
    const rows = ownerId ? await papers.find({ ownerId }).sort({ createdAt: -1 }).toArray() : [];
    const decorated = await decoratePaperRows(rows);

    try {
      return render(request, reply, 'search.ejs', { papers: filterAuthorPapers(decorated, request.query) });
    } catch {
      return render(request, reply, 'search.ejs', {
        papers: [],
        error: 'Please use numeric search values within the displayed ranges.'
      });
    }
  });
}

module.exports = registerSearchRoutes;
