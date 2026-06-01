const { collections } = require('../db');
const { prepareCameraReady } = require('../lib/cameraReady');
const {
  asObjectId,
  parseAuthors,
  parseTopics,
  render,
  paperWithOwner,
  decoratePaperRows
} = require('../lib/helpers');
const {
  saveSubmissionParts,
  submitPaperForReview,
  paperOwnerId
} = require('../lib/papers');

function registerPaperRoutes(app, auth) {
  app.get('/papers', { preHandler: auth.authenticate }, async (request, reply) => {
    const { papers } = collections();
    const ownerId = asObjectId(request.user.id);
    const rows = ownerId ? await papers.find({ ownerId }).sort({ createdAt: -1 }).toArray() : [];
    return render(request, reply, 'papers/list.ejs', { papers: await decoratePaperRows(rows) });
  });

  app.get('/papers/new', { preHandler: auth.authenticate }, (request, reply) => render(request, reply, 'papers/new.ejs'));

  app.post('/papers/new', { preHandler: auth.authenticate }, async (request, reply) => {
    const { papers } = collections();
    let parsed;

    try {
      parsed = await saveSubmissionParts(request);
    } catch (error) {
      return render(request, reply, 'papers/new.ejs', { error: error.message });
    }

    const title = String(parsed.fields.title || '').trim();
    const abstract = String(parsed.fields.abstract || '').trim();
    const authors = parseAuthors(parsed.fields.authors);

    if (!title || !abstract || !authors.length) {
      return render(request, reply, 'papers/new.ejs', { error: 'Title, abstract, authors, and PDF are required.' });
    }

    const result = await papers.insertOne({
      ownerId: paperOwnerId(request.user),
      title,
      abstract,
      authors,
      topics: parseTopics(parsed.fields.topics),
      pdfPath: parsed.pdfPath,
      status: 'Registered',
      createdAt: new Date()
    });

    return reply.redirect(`/papers/${result.insertedId}/view?registered=1`);
  });

  app.get('/papers/:id/view', { preHandler: auth.authenticate }, async (request, reply) => {
    const { reviews, users } = collections();
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');

    const isOwner = paper.ownerId.toString() === request.user.id;
    const isAdmin = request.user.role === 'admin';
    const isReviewer = request.user.role === 'reviewer';
    if (!isOwner && !isAdmin && !isReviewer) return reply.code(403).send('Forbidden');

    const paperReviews = await reviews.find({ paperId: paper._id }).toArray();
    const reviewerIds = paperReviews.map((review) => review.reviewerId);
    const reviewerRows = reviewerIds.length ? await users.find({ _id: { $in: reviewerIds } }).toArray() : [];
    const reviewers = new Map(reviewerRows.map((reviewer) => [reviewer._id.toString(), reviewer.username]));
    const decoratedReviews = paperReviews.map((review) => ({
      ...review,
      reviewerName: reviewers.get(review.reviewerId.toString()) || 'Reviewer'
    }));

    return render(request, reply, 'papers/view.ejs', {
      paper: {
        ...paper,
        publicId: paper._id.toString().slice(-8).toUpperCase()
      },
      reviews: decoratedReviews,
      canSubmitForReview: isOwner && paper.status === 'Registered',
      canPrepareCameraReady: isOwner && paper.status === 'Accepted',
      message: request.query.registered ? 'Paper registered. Submit it for review when the PDF is ready for the PC.' : ''
    });
  });

  app.post('/papers/:id/submit', { preHandler: auth.authenticate }, async (request, reply) => {
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');

    const submitted = await submitPaperForReview(paper, request.user);
    if (!submitted) return reply.code(403).send('Forbidden');

    return reply.redirect(`/papers/${paper._id}/view`);
  });

  app.get('/papers/:id/camera-ready', { preHandler: auth.authenticate }, async (request, reply) => {
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');
    if (paper.ownerId.toString() !== request.user.id || paper.status !== 'Accepted') return reply.code(403).send('Forbidden');
    return render(request, reply, 'papers/cameraReady.ejs', { paper });
  });

  app.post('/papers/:id/camera-ready', { preHandler: auth.authenticate }, async (request, reply) => {
    const { papers } = collections();
    const paper = await paperWithOwner(request.params.id);
    if (!paper) return reply.code(404).send('Not found');
    if (paper.ownerId.toString() !== request.user.id || paper.status !== 'Accepted') return reply.code(403).send('Forbidden');

    try {
      const cameraReady = await prepareCameraReady(request);
      await papers.updateOne(
        { _id: paper._id },
        { $set: { cameraReady, updatedAt: new Date() } }
      );
      return reply.redirect(`/papers/${paper._id}/view`);
    } catch (error) {
      return render(request, reply, 'papers/cameraReady.ejs', { paper, error: error.message });
    }
  });
}

module.exports = registerPaperRoutes;
