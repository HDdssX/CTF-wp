const path = require('path');
const { ObjectId, collections } = require('../db');

const MAX_PROFILE_BYTES = 16 * 1024;
const REVIEWER_TRACKS = ['systems', 'security', 'artifacts', 'process'];
const DEFAULT_AREAS = ['systems', 'review process', 'artifact sanity'];
const SERVICE_DESK_FIELDS = {
  overflowReference: ['committee', 'registration', 'reference'],
  season: ['committee', 'registration', 'season'],
  desk: ['committee', 'desk']
};
const SERVICE_DESK_CREDENTIALS = {
  invitation: 'code'
};

function asArray(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function normalizeTrack(value) {
  const track = String(value || '').trim().toLowerCase();
  return REVIEWER_TRACKS.includes(track) ? track : 'systems';
}

function normalizeAreas(value) {
  return asArray(value)
    .flatMap((entry) => String(entry || '').split(','))
    .map((entry) => entry.trim().toLowerCase())
    .filter(Boolean)
    .slice(0, 12);
}

function normalizeScore(value) {
  const score = Number(value || 0);
  if (!Number.isFinite(score)) return 0;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function displayText(value, fallback = '') {
  if (['string', 'number', 'boolean'].includes(typeof value)) {
    const text = String(value).trim();
    return text ? text.slice(0, 120) : fallback;
  }
  return fallback;
}

function valueAtPath(value, pathParts) {
  let current = value;
  for (const part of pathParts || []) {
    if (!isPlainObject(current)) return undefined;
    current = current[part];
  }
  return current;
}

function appendField(fields, name, value) {
  if (fields[name] === undefined) {
    fields[name] = value;
  } else if (Array.isArray(fields[name])) {
    fields[name].push(value);
  } else {
    fields[name] = [fields[name], value];
  }
}

function isJsonPart(part) {
  const ext = path.extname(part.filename || '').toLowerCase();
  const mimetype = String(part.mimetype || '').toLowerCase();
  return ext === '.json' || mimetype.includes('json');
}

async function readSmallFile(part) {
  const chunks = [];
  let total = 0;

  for await (const chunk of part.file) {
    total += chunk.length;
    if (total > MAX_PROFILE_BYTES) throw new Error('profile attachment is too large');
    chunks.push(chunk);
  }

  return Buffer.concat(chunks).toString('utf8');
}

async function parseProfileAttachment(part) {
  if (!isJsonPart(part)) {
    part.file.resume();
    return null;
  }

  const parsed = JSON.parse(await readSmallFile(part));
  if (!isPlainObject(parsed)) return null;
  return parsed;
}

function summarizeServiceRecord(raw, filename) {
  const committee = isPlainObject(raw.committee) ? raw.committee : {};
  const source = displayText(raw.source, displayText(raw.provider, displayText(committee.source, 'External service record')));
  const label = displayText(raw.label, displayText(raw.title, displayText(committee.role, displayText(committee.track, 'Committee service'))));
  const seasons = asArray(raw.seasons || raw.years || committee.seasons || committee.years)
    .map((entry) => displayText(entry))
    .filter(Boolean)
    .slice(0, 4);
  const areas = normalizeAreas(raw.areas || committee.areas).slice(0, 5);

  return {
    filename: displayText(filename, 'service-record.json'),
    source,
    label,
    seasons,
    areas,
    importedAt: new Date()
  };
}

async function readReviewerProfile(request) {
  const fields = {};
  let imported = null;
  let importedFilename = '';

  for await (const part of request.parts()) {
    if (part.type === 'file') {
      if (part.fieldname === 'profileFile') {
        importedFilename = part.filename || '';
        imported = await parseProfileAttachment(part);
      } else {
        part.file.resume();
      }
    } else {
      appendField(fields, part.fieldname, part.value);
    }
  }

  return {
    draft: {
      track: normalizeTrack(fields.track),
      areas: normalizeAreas(fields.areas),
      score: normalizeScore(fields.score),
      statement: String(fields.statement || '').slice(0, 1000),
      updatedAt: new Date()
    },
    imported,
    importedFilename
  };
}

async function saveReviewerServiceRecord(userId, profile) {
  if (!profile.imported) return null;

  const { reviewerServiceRecords } = collections();
  const now = new Date();
  const record = {
    userId: new ObjectId(userId),
    retainedMetadata: profile.imported,
    summary: summarizeServiceRecord(profile.imported, profile.importedFilename),
    createdAt: now
  };

  await reviewerServiceRecords.insertOne(record);
  return record;
}

async function latestReviewerServiceRecord(userId) {
  const { reviewerServiceRecords } = collections();
  return reviewerServiceRecords.findOne(
    { userId: new ObjectId(userId) },
    { sort: { createdAt: -1 } }
  );
}

function hasRequiredAreas(profile, rubric) {
  const areas = new Set(profile.areas || []);
  return (rubric.requiredAreas || []).every((area) => areas.has(String(area).toLowerCase()));
}

function serviceDeskPolicy(rubric) {
  const configured = isPlainObject(rubric.serviceDesk) ? rubric.serviceDesk : {};
  return {
    queue: displayText(configured.queue, 'overflow'),
    externalKey: displayText(configured.externalKey, 'overflowReference'),
    credential: displayText(configured.credential, 'invitation')
  };
}

function buildServiceDeskPacket(record, rubric) {
  if (!record || !rubric) return null;

  const policy = serviceDeskPolicy(rubric);
  const fieldPath = SERVICE_DESK_FIELDS[policy.externalKey];
  if (!fieldPath) return null;

  return {
    queue: policy.queue,
    slotField: SERVICE_DESK_CREDENTIALS[policy.credential] || SERVICE_DESK_CREDENTIALS.invitation,
    slotValue: valueAtPath(record.retainedMetadata, fieldPath),
    recordId: record._id
  };
}

function assignmentSlotQuery(submitted, rubric, packet) {
  if (!packet || packet.slotValue === undefined) return null;

  return {
    used: false,
    track: submitted.track,
    kind: packet.queue,
    rubricId: rubric.rubricId,
    [packet.slotField]: packet.slotValue
  };
}

function submittedProfileMeetsRubric(submitted, rubric) {
  return Boolean(
    submitted.score >= Number(rubric.minimumScore || 0) &&
    hasRequiredAreas(submitted, rubric)
  );
}

async function recordServiceDeskSync(user, submitted, record, rubric, sync) {
  const { reviewerServiceSyncs } = collections();
  await reviewerServiceSyncs.insertOne({
    userId: user._id,
    username: user.username,
    email: user.email,
    track: submitted.track,
    status: sync.status,
    message: sync.message,
    serviceRecordId: sync.recordId,
    serviceRecordSummary: record ? record.summary : null,
    rubricId: rubric ? rubric.rubricId : null,
    rubricLabels: rubric ? rubric.labels || [] : [],
    createdAt: sync.updatedAt
  });
}

function defaultDraft() {
  return {
    track: 'systems',
    areas: DEFAULT_AREAS,
    score: 10,
    statement: 'I can review baselines, artifacts, and deadline-shaped arguments.'
  };
}

async function reviewerProfileView(userId) {
  const { users } = collections();
  const user = await users.findOne({ _id: new ObjectId(userId) });
  const latestRecord = await latestReviewerServiceRecord(userId);
  const reviewerProfile = user && user.reviewerProfile ? user.reviewerProfile : {};

  return {
    reviewerProfile: {
      status: reviewerProfile.status || 'Draft',
      draft: reviewerProfile.draft || defaultDraft(),
      submitted: reviewerProfile.submitted || null,
      serviceRecordSummary: latestRecord ? latestRecord.summary : reviewerProfile.serviceRecordSummary || null,
      serviceSync: reviewerProfile.serviceSync || null
    },
    latestServiceRecord: latestRecord
  };
}

async function saveReviewerProfile(userId, profile) {
  const { users } = collections();
  const id = new ObjectId(userId);
  const existing = await users.findOne({ _id: id });
  const existingProfile = existing && existing.reviewerProfile ? existing.reviewerProfile : {};
  const serviceRecord = await saveReviewerServiceRecord(userId, profile);
  const nextStatus = existingProfile.status === 'Submitted'
    ? 'Submitted'
    : serviceRecord
      ? 'Service Record Imported'
      : 'Draft';

  const set = {
    'reviewerProfile.status': nextStatus,
    'reviewerProfile.draft': profile.draft,
    'reviewerProfile.updatedAt': new Date()
  };

  if (serviceRecord) {
    set['reviewerProfile.serviceRecordSummary'] = serviceRecord.summary;
  }

  await users.updateOne({ _id: id }, { $set: set });
  return { serviceRecord, status: nextStatus };
}

async function submitReviewerProfile(userId) {
  const { users } = collections();
  const id = new ObjectId(userId);
  const user = await users.findOne({ _id: id });
  const draft = user && user.reviewerProfile && user.reviewerProfile.draft;
  const latestRecord = await latestReviewerServiceRecord(userId);

  if (!draft) {
    return { ok: false, message: 'Reviewer profile needs service areas before submission.' };
  }
  if (!latestRecord) {
    return { ok: false, message: 'Reviewer profile needs a service record before submission.' };
  }

  await users.updateOne(
    { _id: id },
    {
      $set: {
        'reviewerProfile.status': 'Submitted',
        'reviewerProfile.submitted': { ...draft, submittedAt: new Date() },
        'reviewerProfile.serviceRecordSummary': latestRecord.summary,
        'reviewerProfile.serviceSync': {
          status: 'pending',
          message: 'Service record is waiting for the next committee sync.',
          updatedAt: new Date()
        }
      }
    }
  );

  return { ok: true, message: 'Reviewer profile submitted for committee service sync.' };
}

async function syncReviewerServiceSlot(userId) {
  const { users, reviewerInvites, reviewerRubrics } = collections();
  const id = new ObjectId(userId);
  const user = await users.findOne({ _id: id });
  const profile = user && user.reviewerProfile;
  const submitted = profile && profile.submitted;
  const latestRecord = await latestReviewerServiceRecord(userId);
  const now = new Date();

  if (!submitted || profile.status !== 'Submitted') {
    return { matched: false, message: 'Submit the reviewer profile before committee sync.' };
  }

  const rubric = await reviewerRubrics.findOne({
    active: true,
    track: submitted.track
  });
  const packet = buildServiceDeskPacket(latestRecord, rubric);
  const slotQuery = rubric ? assignmentSlotQuery(submitted, rubric, packet) : null;
  let matched = false;

  if (rubric && slotQuery) {
    const invite = await reviewerInvites.findOne(slotQuery);
    matched = Boolean(invite && submittedProfileMeetsRubric(submitted, rubric));
  }

  const sync = {
    status: matched ? 'matched' : 'waiting',
    message: matched ? 'Committee service desk has an available assignment slot.' : 'Committee service desk has not found an assignment slot yet.',
    recordId: packet ? packet.recordId : latestRecord ? latestRecord._id : null,
    updatedAt: now
  };

  await users.updateOne(
    { _id: id },
    {
      $set: {
        'reviewerProfile.serviceSync': sync,
        'reviewerProfile.serviceRecordSummary': latestRecord ? latestRecord.summary : null
      }
    }
  );
  await recordServiceDeskSync(user, submitted, latestRecord, rubric, sync);

  return { matched, message: sync.message };
}

module.exports = {
  readReviewerProfile,
  saveReviewerProfile,
  submitReviewerProfile,
  syncReviewerServiceSlot,
  reviewerProfileView
};
