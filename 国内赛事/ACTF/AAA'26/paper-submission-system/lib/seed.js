const crypto = require('crypto');
const bcrypt = require('bcryptjs');
const config = require('./config');
const { collections } = require('../db');

async function seedDatabase() {
  const { users, papers, reviews, assignments, reviewerInvites, reviewerRubrics } = collections();

  const adminHash = await bcrypt.hash(config.adminPassword, 10);
  await users.updateOne(
    { username: 'admin' },
    {
      $set: {
        username: 'admin',
        email: 'admin@aaa26.big1',
        passwordHash: adminHash,
        role: 'admin',
        affiliation: 'AAA26 Big-1 Chairing Committee, Location TBD',
        updatedAt: new Date()
      },
      $setOnInsert: { createdAt: new Date() }
    },
    { upsert: true }
  );

  const sampleReviewerHash = await bcrypt.hash(crypto.randomBytes(12).toString('hex'), 10);
  await users.updateOne(
    { username: 'pc-reviewer' },
    {
      $setOnInsert: {
        username: 'pc-reviewer',
        email: 'pc-reviewer@aaa26.big1',
        passwordHash: sampleReviewerHash,
        role: 'reviewer',
        affiliation: 'Artifact Review Desk, Hall TBD',
        createdAt: new Date()
      }
    },
    { upsert: true }
  );

  const extraReviewers = [
    ['pc-reviewer-2', 'pc-reviewer-2@aaa26.big1', 'Basement Area Chair, Track TBD'],
    ['meta-reviewer', 'meta-reviewer@aaa26.big1', 'Big-1 Meta-Review Desk'],
    ['artifact-chair', 'artifact-chair@aaa26.big1', 'Artifact Reproduction Committee'],
    ['methodology-chair', 'methodology-chair@aaa26.big1', 'Methods and Mild Disappointment Track'],
    ['proceedings-shepherd', 'proceedings-shepherd@aaa26.big1', 'Proceedings Formatting Desk']
  ];

  for (const [username, email, affiliation] of extraReviewers) {
    await users.updateOne(
      { username },
      {
        $setOnInsert: {
          username,
          email,
          passwordHash: sampleReviewerHash,
          role: 'reviewer',
          affiliation,
          createdAt: new Date()
        }
      },
      { upsert: true }
    );
  }

  const reviewerNames = ['pc-reviewer', ...extraReviewers.map(([username]) => username)];
  const reviewerRows = await users.find({ username: { $in: reviewerNames } }).toArray();
  const reviewerAt = (index) => reviewerRows[index % reviewerRows.length];
  const sampleCount = await papers.countDocuments({ seeded: true });

  if (sampleCount === 0) {
    const seededAuthorHash = await bcrypt.hash(crypto.randomBytes(12).toString('hex'), 10);
    const seededAuthors = await users.insertMany([
      {
        username: 'tbd-cartographer',
        email: 'maps@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Department of Venue Discovery, TBD University',
        createdAt: new Date()
      },
      {
        username: 'artifact-finalist',
        email: 'finalist@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Overnight Submission Lab',
        createdAt: new Date()
      },
      {
        username: 'big1-author',
        email: 'big1@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Institute for One Accepted Paper',
        createdAt: new Date()
      },
      {
        username: 'plotly-apologist',
        email: 'figures@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'School of Unlabeled Axes',
        createdAt: new Date()
      },
      {
        username: 'deadline-survivor',
        email: 'deadline@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Last-Minute Systems Lab',
        createdAt: new Date()
      },
      {
        username: 'baseline-summoner',
        email: 'baselines@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Center for Comparative Overclaiming',
        createdAt: new Date()
      },
      {
        username: 'appendix-whisperer',
        email: 'appendix@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Institute of Supplemental Regret',
        createdAt: new Date()
      },
      {
        username: 'rebuttal-poet',
        email: 'rebuttal@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Department of Polite Disagreement',
        createdAt: new Date()
      },
      {
        username: 'ablation-accountant',
        email: 'ablations@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Office of Missing Tables',
        createdAt: new Date()
      },
      {
        username: 'chair-patience-lab',
        email: 'patience@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Laboratory for Committee Endurance',
        createdAt: new Date()
      },
      {
        username: 'unit-labeler',
        email: 'units@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Department of Axis Accountability',
        createdAt: new Date()
      },
      {
        username: 'future-work-maximalist',
        email: 'future@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Institute for Later Clarification',
        createdAt: new Date()
      },
      {
        username: 'anonymous-coauthor',
        email: 'anonymous@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Double-Blind Naming Consortium',
        createdAt: new Date()
      },
      {
        username: 'proceedings-dreamer',
        email: 'proceedings@example.org',
        passwordHash: seededAuthorHash,
        role: 'user',
        affiliation: 'Center for Camera-Ready Ambition',
        createdAt: new Date()
      }
    ]);

    const authorIds = Object.values(seededAuthors.insertedIds);
    const inserted = await papers.insertMany([
      {
        ownerId: authorIds[0],
        title: 'A Mechanized Proof That the Conference Is Held in TBD',
        abstract: 'We model airport, hotel, and hallway rumors as a distributed consensus protocol and prove the venue remains TBD under partial synchrony.',
        authors: [{ name: 'Dana Q.', email: 'dana@example.org' }],
        topics: ['systems', 'measurement', 'TBD logistics'],
        pdfPath: '/public/sample.pdf',
        status: 'Early Reject',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 5)
      },
      {
        ownerId: authorIds[1],
        title: 'ACTF Artifact Evaluation for Papers Written During Finals Week',
        abstract: 'A practical protocol for determining whether an artifact is reproducible, deadline-driven, or both.',
        authors: [{ name: 'Riley Z.', email: 'riley@example.org' }],
        topics: ['ACTF', 'artifacts', 'reproducibility'],
        pdfPath: '/public/sample.pdf',
        status: 'Under Review',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 3)
      },
      {
        ownerId: authorIds[2],
        title: 'Big-1 Acceptance Considered Too Generous',
        abstract: 'We report a longitudinal study of a conference with one acceptance slot and an unlimited supply of polite rejection templates.',
        authors: [{ name: 'Casey M.', email: 'casey@example.org' }],
        topics: ['conferences', 'program committees', 'Big-1'],
        pdfPath: '/public/sample.pdf',
        status: 'Rejected',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000)
      },
      {
        ownerId: authorIds[3],
        title: 'Ablations Are Left as an Exercise for the Reviewer',
        abstract: 'We introduce a plotting library wrapper that makes every result look statistically significant in the proceedings preview.',
        authors: [{ name: 'Morgan P.', email: 'morgan@example.org' }],
        topics: ['visualization', 'experiments', 'reviewer wellness'],
        pdfPath: '/public/sample.pdf',
        status: 'Submitted',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 / 2)
      },
      {
        ownerId: authorIds[4],
        title: 'Registered But Not Ready: A Deadline Ethnography',
        abstract: 'An observational study of authors who upload a half-finished draft and promise the real contribution will arrive before review.',
        authors: [{ name: 'Taylor N.', email: 'taylor@example.org' }],
        topics: ['deadlines', 'TBD', 'human factors'],
        pdfPath: '/public/sample.pdf',
        status: 'Registered',
        seeded: true,
        createdAt: new Date(Date.now() - 3600000)
      },
      {
        ownerId: authorIds[5],
        title: 'A Unified Theory of Baselines We Could Not Run',
        abstract: 'We propose a taxonomy of missing baselines and show that reviewers can always name one more after rebuttal closes.',
        authors: [{ name: 'Jordan V.', email: 'jordan@example.org' }],
        topics: ['evaluation', 'baselines', 'rebuttals'],
        pdfPath: '/public/sample.pdf',
        status: 'Early Reject',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 2)
      },
      {
        ownerId: authorIds[6],
        title: 'Appendix-First Paper Writing',
        abstract: 'We study the increasingly common workflow where the main paper summarizes an appendix nobody has opened yet.',
        authors: [{ name: 'Quinn R.', email: 'quinn@example.org' }],
        topics: ['writing', 'appendices', 'review process'],
        pdfPath: '/public/sample.pdf',
        status: 'Under Review',
        seeded: true,
        createdAt: new Date(Date.now() - 7200000)
      },
      {
        ownerId: authorIds[7],
        title: 'A Rebuttal Written Entirely in Future Work',
        abstract: 'We evaluate whether a response can be both gracious and composed entirely of promises to clarify after acceptance.',
        authors: [{ name: 'Avery L.', email: 'avery@example.org' }],
        topics: ['rebuttals', 'author response', 'optimism'],
        pdfPath: '/public/sample.pdf',
        status: 'Rejected',
        seeded: true,
        createdAt: new Date(Date.now() - 5400000)
      },
      {
        ownerId: authorIds[8],
        title: 'Ablation Tables Considered Harmful to Deadline Sleep',
        abstract: 'We compare removing each component to removing the weekend and find both interventions reduce author morale.',
        authors: [{ name: 'Sam I.', email: 'sam@example.org' }],
        topics: ['evaluation', 'ablations', 'deadline management'],
        pdfPath: '/public/sample.pdf',
        status: 'Early Reject',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 4)
      },
      {
        ownerId: authorIds[9],
        title: 'The Program Committee as a Distributed Optimism Filter',
        abstract: 'A qualitative model of how reviewer confidence, chair patience, and page limits converge to a stable maybe.',
        authors: [{ name: 'Robin K.', email: 'robin@example.org' }],
        topics: ['program committees', 'review dynamics', 'human factors'],
        pdfPath: '/public/sample.pdf',
        status: 'Under Review',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 3.5)
      },
      {
        ownerId: authorIds[10],
        title: 'On the Statistical Significance of Boldface in Result Tables',
        abstract: 'We show that bold numbers improve author confidence even when confidence intervals remain spiritually unresolved.',
        authors: [{ name: 'Sky T.', email: 'sky@example.org' }],
        topics: ['statistics', 'tables', 'visual communication'],
        pdfPath: '/public/sample.pdf',
        status: 'Rejected',
        seeded: true,
        createdAt: new Date(Date.now() - 86400000 * 2.5)
      },
      {
        ownerId: authorIds[11],
        title: 'A Chair-Friendly Algorithm for Assigning Blame to Reviewer Two',
        abstract: 'We present a scheduling heuristic that routes all impossible decisions toward the most confident anonymous paragraph.',
        authors: [{ name: 'Jules B.', email: 'jules@example.org' }],
        topics: ['review process', 'meta-review', 'committee tooling'],
        pdfPath: '/public/sample.pdf',
        status: 'Submitted',
        seeded: true,
        createdAt: new Date(Date.now() - 14400000)
      },
      {
        ownerId: authorIds[12],
        title: 'Double-Blind Review of a Paper Whose Title Names the Lab',
        abstract: 'We examine anonymity protocols under titles, datasets, acknowledgements, and self-citations that wave enthusiastically.',
        authors: [{ name: 'Blair C.', email: 'blair@example.org' }],
        topics: ['double-blind review', 'anonymity', 'scholarly process'],
        pdfPath: '/public/sample.pdf',
        status: 'Early Reject',
        seeded: true,
        createdAt: new Date(Date.now() - 9000000)
      },
      {
        ownerId: authorIds[13],
        title: 'Proceedings-Ready LaTeX Without Proceedings-Ready Ideas',
        abstract: 'A case study in immaculate formatting, carefully aligned equations, and a contribution that remains under gentle negotiation.',
        authors: [{ name: 'Harper S.', email: 'harper@example.org' }],
        topics: ['writing', 'typesetting', 'conference proceedings'],
        pdfPath: '/public/sample.pdf',
        status: 'Registered',
        seeded: true,
        createdAt: new Date(Date.now() - 1800000)
      }
    ]);

    const paperIds = Object.values(inserted.insertedIds);
    await reviews.insertMany([
      {
        paperId: paperIds[0],
        reviewerId: reviewerAt(0)._id,
        score: 2,
        confidence: 4,
        recommendation: 'Early Reject',
        comments: 'The submission is charming, but the proof assumes the room number exists and the baseline is "ask hallway rumors". The model is expressive enough to represent every possible venue except a confirmed one. The evaluation would be stronger with even one actual travel itinerary. The paper also treats hallway rumors as a reliable broadcast channel, which may be realistic but still needs citation. Main concerns: insufficient experiments; weak baselines; TBD venue assumptions.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[0],
        reviewerId: reviewerAt(1)._id,
        score: 1,
        confidence: 5,
        recommendation: 'Early Reject',
        comments: 'Low-quality evaluation: no hotels, no airports, no actual venue, and the theorem statement has three TBDs. I appreciate the ambition, but the assumptions do most of the work and then ask for a travel grant. The paper needs a clearer problem statement and fewer jokes doing structural support. Figure 2 is memorable, mostly because the axis labels are taking personal leave. Main concerns: unclear evaluation metric; overconfident abstract; unlabeled plots.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[0],
        reviewerId: reviewerAt(2)._id,
        score: 2,
        confidence: 3,
        recommendation: 'Early Reject',
        comments: 'The venue consensus story is funny and almost useful. Unfortunately, the technical contribution is closer to a metaphor with appendices. The related work should discuss actual distributed systems instead of only committee folklore. The proof sketch skips the failure case where everyone books different hotels. Main concerns: thin related work; fragile claims; appendix dependency.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[1],
        reviewerId: reviewerAt(0)._id,
        score: 6,
        confidence: 3,
        recommendation: 'Weak Reject',
        comments: 'The artifact runs on my machine, which is worrying because my machine is not in the spec. The paper is useful and written with rare kindness toward future reproducers. However, the evaluation has one deadline-adjacent participant and one heroic shell history. I would like to see broader tasks, clearer failure modes, and less confidence from the coffee budget. Main concerns: narrow case study; unclear reproducibility story; missing statistical analysis.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[1],
        reviewerId: reviewerAt(2)._id,
        score: 5,
        confidence: 2,
        recommendation: 'Weak Reject',
        comments: 'The contribution is useful for artifact evaluation, but the experiments need more than one deadline-adjacent participant. I like the practical tone and the examples are painfully familiar. The draft still reads like a checklist trying to become a method section. Please add baselines, include failure cases, and define what success means before the final panic. Main concerns: weak baselines; ambiguous problem statement; deadline-shaped writing.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[2],
        reviewerId: reviewerAt(1)._id,
        score: 4,
        confidence: 5,
        recommendation: 'Reject',
        comments: 'The title is empirically accurate. The contribution is emotionally complicated. The paper gives a persuasive account of selectivity, but the analysis mostly restates the call for papers with thicker eyebrows. I wanted more data and fewer adjectives about chair morale. The result is readable, but not yet a research contribution. Main concerns: incremental novelty; insufficient experiments; committee fatigue.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[2],
        reviewerId: reviewerAt(3)._id,
        score: 3,
        confidence: 4,
        recommendation: 'Reject',
        comments: 'Incremental novelty over the classic "conference is too selective" paper. Please add an ablation for chair patience. The work claims a new theory but largely measures the obvious with impressive seriousness. The writing is funny, although sometimes the joke is carrying the theorem. I would reconsider with stronger evidence and a less theatrical conclusion. Main concerns: overstated conclusion; missing ablation; thin related work.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[5],
        reviewerId: reviewerAt(0)._id,
        score: 2,
        confidence: 4,
        recommendation: 'Early Reject',
        comments: 'The missing baseline is unfortunately the paper. Strong title, limited evidence. The taxonomy is amusing and probably complete, but the evaluation demonstrates the very problem it names. A table of baselines that were not run is not the same as running them, even at Big-1 scale. The paper needs a real comparison and a less defensive limitations section. Main concerns: weak baselines; insufficient experiments; overconfident abstract.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[5],
        reviewerId: reviewerAt(2)._id,
        score: 3,
        confidence: 3,
        recommendation: 'Reject',
        comments: 'The taxonomy is accurate, but mostly because it enumerates things this submission also did not evaluate. I enjoyed the writing and found the categories useful. The problem is that the paper stops at naming the absence and calls that measurement. The authors should add at least two real comparisons and explain why the chosen baselines matter. Main concerns: unclear evaluation metric; unreleased implementation; missing statistical analysis.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[5],
        reviewerId: reviewerAt(3)._id,
        score: 2,
        confidence: 4,
        recommendation: 'Early Reject',
        comments: 'This draft understands reviewer frustration with unusual precision. It does not yet transform that frustration into a convincing experiment. The central claim could be interesting if tested across several tasks instead of described around them. The rebuttal should not be asked to do the job of the main paper. Main concerns: single-dataset evidence; fragile claims; unclear reproducibility story.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[6],
        reviewerId: reviewerAt(1)._id,
        score: 5,
        confidence: 2,
        recommendation: 'Weak Reject',
        comments: 'The appendix is promising. The main paper should consider introducing itself to it. There are good ideas here, but the organization asks readers to assemble them like furniture without diagrams. The evaluation is surprisingly complete once found, which makes the main narrative feel under-edited. I recommend a rewrite that promotes the strongest material before page 14. Main concerns: appendix dependency; unclear problem statement; deadline-shaped writing.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[7],
        reviewerId: reviewerAt(2)._id,
        score: 4,
        confidence: 4,
        recommendation: 'Reject',
        comments: 'The rebuttal is polite enough to improve the mood, but not the score. The paper anticipates every concern by promising to clarify later. This is an elegant social strategy and a weak empirical one. The contribution needs to exist in the submission rather than in a future branch of author intent. Main concerns: overstated conclusion; insufficient experiments; uncalibrated confidence.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[7],
        reviewerId: reviewerAt(3)._id,
        score: 3,
        confidence: 3,
        recommendation: 'Reject',
        comments: 'Several concerns are answered with future tense. The committee has reviewed the future and remains unconvinced. The authors are gracious and the response is coherent, but it cannot add missing experiments retroactively. I would encourage a resubmission with the promised clarifications already present. Main concerns: missing ablation; unclear reproducibility story; overconfident abstract.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[8],
        reviewerId: reviewerAt(0)._id,
        score: 2,
        confidence: 4,
        recommendation: 'Early Reject',
        comments: 'The paper is correct that ablations are harmful to sleep. Unfortunately, conferences are not optimized for sleep. The method section removes components but never explains what each component was supposed to do. The strongest result is that deadlines reduce experimental diversity, which the committee has independently reproduced. Main concerns: missing ablation; ambiguous problem statement; deadline-shaped writing.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[8],
        reviewerId: reviewerAt(1)._id,
        score: 1,
        confidence: 5,
        recommendation: 'Early Reject',
        comments: 'This submission argues against ablation tables while needing exactly one. The evaluation is thin, the baselines are tired, and the conclusion has already left for the rebuttal period. I enjoyed the title and one footnote, which is not enough for acceptance. The figures also need units before they can hurt anyone responsibly. Main concerns: weak baselines; unlabeled plots; overstated conclusion.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[8],
        reviewerId: reviewerAt(2)._id,
        score: 3,
        confidence: 3,
        recommendation: 'Early Reject',
        comments: 'There is a useful workshop paper hiding here. The current version chooses comedy over measurement too often. A clearer benchmark and one serious comparison would make the joke land better. The claims about author morale are relatable but not quantified. Main concerns: insufficient experiments; unclear evaluation metric; narrow case study.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[9],
        reviewerId: reviewerAt(1)._id,
        score: 5,
        confidence: 3,
        recommendation: 'Weak Reject',
        comments: 'The distributed optimism model captures the review process with unsettling accuracy. I like the qualitative interviews and the diagram of chair patience. The paper still needs a stronger bridge from anecdotes to mechanism. The current evidence supports "reviewing is strange", which the committee accepts as background knowledge. Main concerns: thin related work; missing statistical analysis; unclear user study.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[9],
        reviewerId: reviewerAt(3)._id,
        score: 6,
        confidence: 2,
        recommendation: 'Weak Accept',
        comments: 'This is readable, relevant, and more self-aware than most process papers. The claims are modest enough to survive contact with reviewers. I would like clearer coding methodology and a table separating jokes from findings. The contribution is not huge, but the paper improves the room. Main concerns: unclear user study; narrow case study; unmotivated terminology.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[10],
        reviewerId: reviewerAt(2)._id,
        score: 3,
        confidence: 5,
        recommendation: 'Reject',
        comments: 'Boldface is not a statistical test, even when applied consistently. The paper has a delightful premise but stops before the hard part. The authors should evaluate actual reader interpretation instead of counting how often authors feel victorious. The table captions are excellent, which only emphasizes the missing study. Main concerns: unclear evaluation metric; insufficient experiments; overconfident abstract.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[10],
        reviewerId: reviewerAt(0)._id,
        score: 4,
        confidence: 4,
        recommendation: 'Reject',
        comments: 'I appreciate any paper willing to interrogate result-table theater. The draft has good instincts and weak evidence. A small user study would make the argument much stronger than another paragraph about typographic confidence. The current version is funny but under-supported. Main concerns: missing statistical analysis; narrow case study; weak baselines.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[12],
        reviewerId: reviewerAt(3)._id,
        score: 2,
        confidence: 4,
        recommendation: 'Early Reject',
        comments: 'The anonymity problem is real, but this paper demonstrates it more than it solves it. The title, dataset, and acknowledgements all point in the same direction with admirable teamwork. The proposed mitigation is mostly advice to be less recognizable. I wanted a concrete evaluation and a calmer conclusion. Main concerns: unclear threat model; insufficient experiments; overstated conclusion.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[12],
        reviewerId: reviewerAt(0)._id,
        score: 3,
        confidence: 3,
        recommendation: 'Early Reject',
        comments: 'The submission has a strong premise and several sharp examples. It lacks a method for measuring how often the problem matters in practice. The writing is lively, but some sections treat jokes as evidence. A broader dataset of submissions would help. Main concerns: single-dataset evidence; ambiguous problem statement; thin related work.',
        createdAt: new Date()
      },
      {
        paperId: paperIds[12],
        reviewerId: reviewerAt(1)._id,
        score: 2,
        confidence: 5,
        recommendation: 'Early Reject',
        comments: 'The paper asks an important process question with a surprisingly casual experiment. I agree the current norms are awkward. I do not agree that three examples and a flowchart settle the matter. The authors should add a real annotation protocol and report disagreement. Main concerns: unclear user study; missing statistical analysis; fragile claims.',
        createdAt: new Date()
      }
    ]);

    await assignments.insertMany(
      paperIds.flatMap((paperId, paperIndex) => [
        {
          paperId,
          reviewerId: reviewerAt(paperIndex)._id,
          createdAt: new Date()
        },
        {
          paperId,
          reviewerId: reviewerAt(paperIndex + 1)._id,
          createdAt: new Date()
        }
      ])
    );
  }

  await reviewerInvites.updateOne(
    { email: 'committee-shadow@aaa26.big1' },
    {
      $setOnInsert: {
        email: 'committee-shadow@aaa26.big1',
        code: crypto.randomBytes(18).toString('hex'),
        track: 'systems',
        kind: 'overflow',
        rubricId: 'big1-overflow-systems',
        chairStamp: crypto.randomBytes(16).toString('hex'),
        used: false,
        note: 'Overflow reviewer slot for the room marked TBD.',
        createdAt: new Date()
      }
    },
    { upsert: true }
  );

  await reviewerRubrics.updateOne(
    { rubricId: 'big1-overflow-systems' },
    {
      $setOnInsert: {
        rubricId: 'big1-overflow-systems',
        track: 'systems',
        active: true,
        portfolioSeal: crypto.randomBytes(16).toString('hex'),
        serviceDesk: {
          queue: 'overflow',
          externalKey: 'overflowReference',
          credential: 'invitation'
        },
        requiredAreas: ['systems', 'review process', 'artifact sanity'],
        minimumScore: 37,
        labels: ['TBD logistics', 'baseline realism', 'committee stamina'],
        createdAt: new Date()
      }
    },
    { upsert: true }
  );

  console.log('[AAA26] admin username: admin');
  console.log(`[AAA26] admin password: ${config.adminPassword}`);
  console.log(`[AAA26] venue: ${config.conference.venue}`);
}

module.exports = { seedDatabase };
