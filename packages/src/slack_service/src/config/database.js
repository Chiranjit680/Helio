const { Pool } = require("pg");

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const initDatabase = async () => {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS slack_messages (
        id SERIAL PRIMARY KEY,
        message_ts TEXT UNIQUE,
        channel_id TEXT,
        user_id TEXT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log("Database initialized: slack_messages table ready");
  } finally {
    client.release();
  }
};

module.exports = { pool, initDatabase };
