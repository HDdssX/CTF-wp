const path = require('path');
const crypto = require('crypto');

const rootDir = path.join(__dirname, '..');
const publicDir = path.join(rootDir, 'public');

module.exports = {
  port: Number(process.env.PORT || 3000),
  host: process.env.HOST || '0.0.0.0',
  jwtSecret: process.env.JWT_SECRET || `aaa26_${crypto.randomBytes(24).toString('hex')}`,
  adminPassword: process.env.ADMIN_PASSWORD || crypto.randomBytes(16).toString('hex'),
  rootDir,
  publicDir,
  uploadsDir: path.join(publicDir, 'uploads'),
  cameraReadyDir: path.join(publicDir, 'camera-ready'),
  thumbnailsDir: path.join(publicDir, 'camera-ready', 'thumbs'),
  decisionStatuses: ['Registered', 'Submitted', 'Under Review', 'Early Reject', 'Rejected', 'Accepted'],
  timing: {
    underReviewAfterMs: 3000,
    rejectAfterMs: 10000
  },
  conference: {
    name: "AAA'26 Big-1 Conference",
    shortName: 'AAA26 Big-1',
    organizer: 'Association for Adversarial Artifacts',
    cohost: 'Artifact Evaluation Committee',
    venue: 'TBD Convention Center, Room TBD, City TBD',
    deadline: 'Whenever the chairs finish the last program update',
    motto: 'One acceptance, many carefully formatted disappointments.'
  }
};
