const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { pipeline } = require('stream/promises');
const config = require('./config');
const { collections, ObjectId } = require('../db');

const earlyRejectSentences = [
  'The submission reads like a TODO list that discovered the conference template. The idea may exist, but the experiments did not attend.',
  'Low-quality presentation, incremental novelty, and a graph whose axes appear to be negotiated rather than labeled.',
  'The paper claims strong results but compares only against a baseline named "trust me bro".',
  'Insufficient experiments. The artifact section says "coming soon", which is also my confidence in the result.',
  'Novelty is marginal: this is Big-1, and the contribution is closer to Big-0.1.',
  'The evaluation has one run, one seed, and one very optimistic interpretation of variance.',
  'Related work omits the entire field, possibly because the field rejected this paper last year.',
  'The abstract promises a framework; the body delivers a parameter sweep and a confident paragraph.',
  'The main theorem depends on a lemma titled "obviously", which the committee found brave.',
  'The motivation is compelling, but the method appears to be three bash aliases in a trench coat.',
  'The paper says "we leave deployment to future work" in four different fonts.',
  'The introduction spends two pages explaining why the problem is important and zero paragraphs explaining why this solution is new.',
  'The authors report a 400% improvement over a baseline that appears to be a for loop with low self-esteem.',
  'The strongest empirical result is in the appendix, where it is safely protected from readers.',
  'The methodology is described at a level of detail best summarized as "vibes, but reproducible in principle".',
  'The threat model excludes users, networks, time, and other common sources of inconvenience.',
  'The paper claims end-to-end results, but the end appears to be a carefully cropped screenshot.',
  'The evaluation section uses confidence intervals as decorative punctuation.',
  'The authors cite a survey but seem to have stopped reading after the title.',
  'The system diagram has seven arrows entering a box labeled "magic", which may be accurate but is not reassuring.',
  'The work is potentially useful, but the current draft asks reviewers to perform archaeology with page limits.',
  'Several claims are plausible after sufficient coffee, but plausibility is not a substitute for experiments.',
  'The paper introduces three new terms for one existing idea and then evaluates none of them.',
  'The related-work section is concise in the way a missing luggage claim is concise.',
  'The contribution may be real, but it is currently hiding behind acronyms and heroic assumptions.',
  'The benchmark appears custom-built to admire the proposed method.',
  'The paper is well formatted, which briefly distracted the committee from the absence of ablations.',
  'The authors answer an interesting question, but unfortunately not the one stated in the abstract.',
  'The notation is dense enough to require its own registration desk.',
  'The experiments show promise, especially for the hypothesis that reviewers enjoy guessing units.',
  'The limitations section is honest, comprehensive, and accidentally the strongest part of the paper.',
  'The paper would benefit from comparing against methods published after the invention of the current problem.',
  'The result table contains bold numbers, but boldness is not statistical significance.',
  'The proposed approach is elegant until it encounters data, at which point it becomes a policy suggestion.',
  'The writing suggests three papers negotiated custody of one abstract.',
  'The artifact instructions are enthusiastic, but enthusiasm does not install dependencies.',
  'The paper makes an ambitious claim, then delegates evidence to a footnote with excellent posture.',
  'The conclusion overstates the findings by approximately one keynote talk.',
  'The evaluation metric is convenient, author-defined, and suspiciously friendly.',
  'The case study is interesting, but one case is a case study, not a trend with a beard.',
  'The authors promise a release after acceptance, which is also when reviewers promise to become patient.',
  'The rebuttal would need to introduce a new paper rather than clarify this one.',
  'The negative results are hidden so well that the committee considered nominating them for best artifact.',
  'The paper treats missing baselines as a lifestyle choice.',
  'The claimed generality is currently supported by one dataset and a lot of eye contact.',
  'The discussion section is fluent, confident, and only occasionally adjacent to the results.',
  'The figures are colorful enough to imply progress, but the axis labels remain emotionally unavailable.',
  'The proposed taxonomy contains a category for every example except the hard one.',
  'The paper appears to confuse "we can" with "we did".',
  'The study design has the energy of a pilot study that booked the main conference room too early.'
];

const earlyRejectTopics = [
  'incremental novelty',
  'insufficient experiments',
  'unclear threat model',
  'weak baselines',
  'missing ablation',
  'unconvincing artifact',
  'TBD venue assumptions',
  'low-quality figures',
  'overconfident abstract',
  'committee fatigue',
  'underexplained notation',
  'optimistic benchmarking',
  'thin related work',
  'fragile claims',
  'unclear evaluation metric',
  'missing statistical analysis',
  'single-dataset evidence',
  'unlabeled plots',
  'appendix dependency',
  'uncalibrated confidence',
  'unreleased implementation',
  'unclear user study',
  'narrow case study',
  'unmotivated terminology',
  'ambiguous problem statement',
  'overstated conclusion',
  'insufficient negative results',
  'unclear reproducibility story',
  'deadline-shaped writing'
];

function randomInt(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function sampleMany(values, count) {
  const pool = [...values];
  const sampled = [];

  while (sampled.length < count && pool.length) {
    const index = Math.floor(Math.random() * pool.length);
    sampled.push(pool.splice(index, 1)[0]);
  }

  return sampled;
}

async function assignBacklogToReviewer(reviewerId) {
  const { papers, assignments } = collections();
  const backlog = await papers.find({ status: { $ne: 'Registered' } }).sort({ createdAt: -1 }).limit(20).toArray();
  if (!backlog.length) return;

  await assignments.bulkWrite(backlog.map((paper) => ({
    updateOne: {
      filter: { paperId: paper._id, reviewerId },
      update: { $setOnInsert: { paperId: paper._id, reviewerId, createdAt: new Date() } },
      upsert: true
    }
  })));
}

function buildEarlyRejectReview() {
  const score = randomInt(1, 3);
  const confidence = randomInt(3, 5);
  const sentences = sampleMany(earlyRejectSentences, randomInt(5, 10));
  const topics = sampleMany(earlyRejectTopics, randomInt(3, 5));

  return {
    score,
    confidence,
    recommendation: 'Early Reject',
    comments: `${sentences.join(' ')} Main concerns: ${topics.join('; ')}.`
  };
}

async function fileAutomaticEarlyRejectReview(paperId) {
  const { users, reviews, assignments } = collections();
  const reviewerRows = await users.find({ role: 'reviewer' }).sort({ username: 1 }).limit(8).toArray();
  const selectedReviewers = sampleMany(reviewerRows, randomInt(3, 5));
  if (!selectedReviewers.length) return;

  await assignments.bulkWrite(selectedReviewers.map((reviewer) => ({
    updateOne: {
      filter: { paperId, reviewerId: reviewer._id },
      update: { $setOnInsert: { paperId, reviewerId: reviewer._id, createdAt: new Date(), source: 'pc-triage' } },
      upsert: true
    }
  })));

  await reviews.bulkWrite(selectedReviewers.map((reviewer) => ({
    updateOne: {
      filter: { paperId, reviewerId: reviewer._id },
      update: {
        $setOnInsert: {
          paperId,
          reviewerId: reviewer._id,
          ...buildEarlyRejectReview(),
          createdAt: new Date()
        }
      },
      upsert: true
    }
  })));
}

async function saveSubmissionParts(request) {
  const fields = {};
  let pdfPath = '';
  let savedAnyFile = false;

  for await (const part of request.parts()) {
    if (part.type === 'file') {
      if (part.fieldname !== 'pdf') {
        part.file.resume();
        continue;
      }

      const ext = path.extname(part.filename || '') || '.pdf';
      const filename = `${Date.now()}-${crypto.randomBytes(8).toString('hex')}${ext}`;
      const target = path.join(config.uploadsDir, filename);
      await pipeline(part.file, fs.createWriteStream(target));
      pdfPath = `/public/uploads/${filename}`;
      savedAnyFile = true;
    } else {
      fields[part.fieldname] = part.value;
    }
  }

  if (!savedAnyFile) throw new Error('PDF upload is required');
  return { fields, pdfPath };
}

function scheduleAutomaticRejection(paperId) {
  // Because Big-1 is busy, unresolved submissions receive the accelerated scholarly experience.
  setTimeout(async () => {
    const { papers } = collections();
    await papers.updateOne(
      { _id: paperId, status: 'Submitted' },
      { $set: { status: 'Under Review', updatedAt: new Date() } }
    );
  }, config.timing.underReviewAfterMs);

  setTimeout(async () => {
    const { papers } = collections();
    const result = await papers.updateOne(
      { _id: paperId, status: { $in: ['Submitted', 'Under Review'] } },
      { $set: { status: 'Early Reject', updatedAt: new Date(), decidedAt: new Date(), decidedBy: 'PC triage desk' } }
    );

    if (result.modifiedCount) {
      await fileAutomaticEarlyRejectReview(paperId);
    }
  }, config.timing.rejectAfterMs);
}

async function submitPaperForReview(paper, user) {
  const { papers } = collections();
  const ownerId = paper.ownerId && paper.ownerId.toString();
  if (ownerId !== user.id || paper.status !== 'Registered') return false;

  const result = await papers.updateOne(
    { _id: paper._id, status: 'Registered' },
    { $set: { status: 'Submitted', submittedAt: new Date(), updatedAt: new Date() } }
  );

  if (result.modifiedCount) {
    scheduleAutomaticRejection(paper._id);
    return true;
  }

  return false;
}

function paperOwnerId(user) {
  return new ObjectId(user.id);
}

module.exports = {
  assignBacklogToReviewer,
  saveSubmissionParts,
  scheduleAutomaticRejection,
  submitPaperForReview,
  paperOwnerId
};
