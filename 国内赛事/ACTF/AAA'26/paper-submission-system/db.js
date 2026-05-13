const { MongoClient, ObjectId } = require('mongodb');

const mongoUrl = process.env.MONGO_URL || 'mongodb://127.0.0.1:27017';
const dbName = process.env.MONGO_DB || 'aaa26_big1';

let client;
let database;

async function connectDatabase() {
  if (database) return database;

  client = new MongoClient(mongoUrl);
  await client.connect();
  database = client.db(dbName);

  await Promise.all([
    database.collection('users').createIndex({ username: 1 }, { unique: true }),
    database.collection('users').createIndex({ email: 1 }, { unique: true }),
    database.collection('papers').createIndex({ ownerId: 1, createdAt: -1 }),
    database.collection('reviews').createIndex({ paperId: 1, reviewerId: 1 }, { unique: true }),
    database.collection('assignments').createIndex({ paperId: 1, reviewerId: 1 }, { unique: true }),
    database.collection('reviewerInvites').createIndex({ email: 1, code: 1 }),
    database.collection('reviewerRubrics').createIndex({ rubricId: 1 }, { unique: true }),
    database.collection('reviewerServiceRecords').createIndex({ userId: 1, createdAt: -1 }),
    database.collection('reviewerServiceSyncs').createIndex({ createdAt: -1 })
  ]);

  return database;
}

function collections() {
  if (!database) throw new Error('Database is not connected');
  return {
    users: database.collection('users'),
    papers: database.collection('papers'),
    reviews: database.collection('reviews'),
    assignments: database.collection('assignments'),
    reviewerInvites: database.collection('reviewerInvites'),
    reviewerRubrics: database.collection('reviewerRubrics'),
    reviewerServiceRecords: database.collection('reviewerServiceRecords'),
    reviewerServiceSyncs: database.collection('reviewerServiceSyncs')
  };
}

async function closeDatabase() {
  if (client) await client.close();
}

module.exports = {
  ObjectId,
  connectDatabase,
  collections,
  closeDatabase
};
