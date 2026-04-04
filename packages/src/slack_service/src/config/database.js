const { Pool } = require("pg");
const pgvector = require("pgvector/pg");

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const initDatabase = async () => {
  const client = await pool.connect();
  try {

    await pgvector.registerType(client);

    await client.query(`CREATE EXTENSION IF NOT EXISTS vector;`);

    await client.query(`
      CREATE TABLE IF NOT EXISTS slack_messages (
        id SERIAL PRIMARY KEY,
        message_ts TEXT UNIQUE NOT NULL,
        channel_id TEXT NOT NULL,
        channel_name TEXT,
        user_id TEXT,
        username TEXT,
        text TEXT NOT NULL,
        embedding vector(384),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        importance_score INTEGER DEFAULT 0,
        category TEXT
      )
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS slack_channels (
        id           SERIAL PRIMARY KEY,
        channel_id   TEXT UNIQUE NOT NULL,
        channel_name TEXT NOT NULL,
        topic        TEXT,
        purpose      TEXT,
        is_private   BOOLEAN DEFAULT FALSE,
        embedding    vector(384),        -- name + topic + purpose embedded
        updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_channel_id ON slack_messages(channel_id);
      CREATE INDEX IF NOT EXISTS idx_user_id ON slack_messages(user_id);
      CREATE INDEX IF NOT EXISTS idx_created_at ON slack_messages(created_at DESC);
    `);

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_messages_embedding
        ON slack_messages
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    `);

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_channels_embedding
        ON slack_channels
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    `);

    console.log("Database initialized: slack_messages table ready");
  } finally {
    client.release();
  }
};

pool.on("connect", async (client) => {
  await pgvector.registerType(client);
});


module.exports = { pool, initDatabase };
