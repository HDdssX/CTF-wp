const { VM } = require('vm2');
const { getBearerOrCookie } = require('./auth');
const { reviewerDocuments } = require('./helpers');

function runExpression(source, item, timeout = 1250) {
  const vm = new VM({
    timeout,
    sandbox: { item }
  });

  return !!vm.run(source);
}

function filterView(item) {
  return structuredClone(item);
}

function runReviewerExpression(expression, item) {
  if (typeof expression !== 'string' || expression.length === 0 || expression.length > 4096) {
    throw new Error('invalid expression');
  }

  // The Big-1 PC is sure open JavaScript search will preserve double-blind review, because optimism is a methodology.
  const source = `
    const paper = item.paper;
    const review = item.review;
    const reviewer = item.reviewer;
    const scores = item.scores;
    Boolean((() => (${expression}))())
  `;

  return runExpression(source, item);
}

function numericLiteral(value, min, max) {
  if (value === undefined || value === null || value === '') return null;

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) throw new Error('invalid numeric filter');

  const scaled = Math.round(numeric * 10);
  if (scaled < min * 10 || scaled > max * 10) throw new Error('invalid numeric filter');
  return String(scaled);
}

function paperIdDigits(value) {
  const digits = String(value || '').trim();
  if (!digits) return '';
  if (!/^\d{1,8}$/.test(digits)) throw new Error('invalid paper id filter');
  return digits;
}

function authorSearchItem(paper) {
  return {
    paper: {
      publicId: paper.publicId,
      publicIdDigits: paper.publicId.replace(/\D/g, ''),
      status: paper.status
    },
    scores: {
      averageScoreTenths: paper.avgScore === null ? null : Math.round(paper.avgScore * 10),
      averageConfidenceTenths: paper.avgConfidence === null ? null : Math.round(paper.avgConfidence * 10),
      reviewCount: paper.reviewCount
    }
  };
}

function buildAuthorSearchExpression(query) {
  const clauses = ['true'];
  const scoreMin = numericLiteral(query.scoreMin, 1, 10);
  const confidenceMin = numericLiteral(query.confidenceMin, 1, 5);
  const idDigits = paperIdDigits(query.paperId);

  if (scoreMin !== null) {
    clauses.push(`scores.averageScoreTenths !== null && scores.averageScoreTenths >= ${scoreMin}`);
  }

  if (confidenceMin !== null) {
    clauses.push(`scores.averageConfidenceTenths !== null && scores.averageConfidenceTenths >= ${confidenceMin}`);
  }

  if (idDigits) {
    clauses.push(`paper.publicIdDigits.includes("${idDigits}")`);
  }

  return clauses.map((clause) => `(${clause})`).join(' && ');
}

function runAuthorExpression(expression, item) {
  const source = `
    const paper = item.paper;
    const scores = item.scores;
    Boolean(${expression})
  `;

  return runExpression(source, item, 250);
}

function filterAuthorPapers(papers, query) {
  const expression = buildAuthorSearchExpression(query || {});
  return papers.filter((paper) => runAuthorExpression(expression, authorSearchItem(paper)));
}

async function filterReviewerDocuments(app, request, expression) {
  const token = getBearerOrCookie(request);
  const docs = await reviewerDocuments(request.user);
  const verified = await app.jwt.verify(token);
  if (!verified || verified.id !== request.user.id || verified.role !== request.user.role) {
    throw new Error('invalid token');
  }

  const matches = [];

  for (const item of docs) {
    if (runReviewerExpression(expression, filterView(item))) {
      matches.push(item);
    }
  }

  return matches;
}

module.exports = {
  filterAuthorPapers,
  filterReviewerDocuments
};
