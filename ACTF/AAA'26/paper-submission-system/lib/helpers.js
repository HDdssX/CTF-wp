const fs = require('fs');
const config = require('./config');
const { ObjectId, collections } = require('../db');

function asObjectId(id) {
  try {
    return new ObjectId(id);
  } catch {
    return null;
  }
}

function statusClass(status) {
  if (status === 'Accepted') return 'success';
  if (status === 'Rejected' || status === 'Early Reject') return 'danger';
  if (status === 'Under Review') return 'info text-dark';
  if (status === 'Submitted') return 'primary';
  return 'secondary';
}

function paperPublicId(paper) {
  return paper._id.toString().slice(-8).toUpperCase();
}

function parseAuthors(input) {
  return String(input || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [name, email] = line.split(',').map((part) => part.trim());
      return { name: name || 'Anonymous Author', email: email || '' };
    });
}

function parseTopics(input) {
  return String(input || '')
    .split(',')
    .map((topic) => topic.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function average(values) {
  const nums = values.filter((value) => Number.isFinite(value));
  if (!nums.length) return null;
  return nums.reduce((sum, value) => sum + value, 0) / nums.length;
}

function ensureDirectories() {
  fs.mkdirSync(config.uploadsDir, { recursive: true });
  fs.mkdirSync(config.cameraReadyDir, { recursive: true });
  fs.mkdirSync(config.thumbnailsDir, { recursive: true });
}

function render(request, reply, template, data = {}) {
  return reply.view(template, {
    user: request.user || null,
    conference: config.conference,
    statusClass,
    paperPublicId,
    query: request.query || {},
    ...data
  });
}

async function paperWithOwner(id) {
  const { users, papers } = collections();
  const paperId = asObjectId(id);
  if (!paperId) return null;
  const paper = await papers.findOne({ _id: paperId });
  if (!paper) return null;
  const owner = await users.findOne({ _id: paper.ownerId });
  return { ...paper, owner };
}

async function decoratePaperRows(rawPapers) {
  const { users, reviews } = collections();
  const ownerIds = [...new Set(rawPapers.map((paper) => paper.ownerId && paper.ownerId.toString()).filter(Boolean))]
    .map((id) => new ObjectId(id));
  const paperIds = rawPapers.map((paper) => paper._id);

  const [owners, allReviews] = await Promise.all([
    ownerIds.length ? users.find({ _id: { $in: ownerIds } }).toArray() : [],
    paperIds.length ? reviews.find({ paperId: { $in: paperIds } }).toArray() : []
  ]);

  const ownerById = new Map(owners.map((owner) => [owner._id.toString(), owner]));
  const reviewsByPaper = new Map();
  for (const review of allReviews) {
    const key = review.paperId.toString();
    if (!reviewsByPaper.has(key)) reviewsByPaper.set(key, []);
    reviewsByPaper.get(key).push(review);
  }

  return rawPapers.map((paper) => {
    const ownReviews = reviewsByPaper.get(paper._id.toString()) || [];
    const avgScore = average(ownReviews.map((review) => Number(review.score)));
    const avgConfidence = average(ownReviews.map((review) => Number(review.confidence)));
    return {
      ...paper,
      publicId: paperPublicId(paper),
      owner: ownerById.get(paper.ownerId && paper.ownerId.toString()) || null,
      reviewCount: ownReviews.length,
      avgScore,
      avgConfidence
    };
  });
}

async function reviewerDocuments(user) {
  const { users, papers, reviews, assignments } = collections();
  let assignedPaperIds;

  if (user.role === 'admin') {
    const allPapers = await papers.find({}).project({ _id: 1 }).toArray();
    assignedPaperIds = allPapers.map((paper) => paper._id);
  } else {
    const assigned = await assignments.find({ reviewerId: new ObjectId(user.id) }).toArray();
    assignedPaperIds = assigned.map((row) => row.paperId);
  }

  if (!assignedPaperIds.length) return [];

  const paperRows = await papers.find({ _id: { $in: assignedPaperIds } }).sort({ createdAt: -1 }).toArray();
  const reviewRows = await reviews.find({ paperId: { $in: assignedPaperIds } }).toArray();
  const reviewerIds = [...new Set(reviewRows.map((review) => review.reviewerId.toString()))].map((id) => new ObjectId(id));
  const reviewerRows = reviewerIds.length ? await users.find({ _id: { $in: reviewerIds } }).toArray() : [];
  const reviewerById = new Map(reviewerRows.map((reviewer) => [reviewer._id.toString(), reviewer]));

  return paperRows.map((paper) => {
    const paperReviews = reviewRows.filter((review) => review.paperId.equals(paper._id));
    const ownReview = paperReviews.find((review) => review.reviewerId.toString() === user.id) || paperReviews[0] || null;
    const reviewer = ownReview ? reviewerById.get(ownReview.reviewerId.toString()) : null;
    const avgScore = average(paperReviews.map((review) => Number(review.score)));
    const avgConfidence = average(paperReviews.map((review) => Number(review.confidence)));

    return {
      paper: {
        id: paper._id.toString(),
        publicId: paperPublicId(paper),
        title: paper.title,
        abstract: paper.abstract,
        status: paper.status,
        topics: paper.topics || [],
        createdAt: paper.createdAt
      },
      review: ownReview
        ? {
            score: Number(ownReview.score),
            confidence: Number(ownReview.confidence),
            recommendation: ownReview.recommendation,
            comments: ownReview.comments
          }
        : {
            score: null,
            confidence: null,
            recommendation: 'Unreviewed',
            comments: ''
          },
      reviewer: reviewer
        ? {
            username: reviewer.username,
            role: reviewer.role
          }
        : {
            username: user.username,
            role: user.role
          },
      scores: {
        averageScore: avgScore,
        averageConfidence: avgConfidence,
        reviewCount: paperReviews.length
      }
    };
  });
}

module.exports = {
  asObjectId,
  statusClass,
  paperPublicId,
  parseAuthors,
  parseTopics,
  average,
  ensureDirectories,
  render,
  paperWithOwner,
  decoratePaperRows,
  reviewerDocuments
};
