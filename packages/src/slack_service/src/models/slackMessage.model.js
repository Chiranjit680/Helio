const { pool } = require("../config/database");
const { toSql } = require("pgvector");

const SlackMessage = {
  async save({ messageTs, channelId, channelName, userId, username, text, embedding }) {
    const result = await pool.query(
      `INSERT INTO slack_messages (message_ts, channel_id, channel_name, user_id, username, text, embedding)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       ON CONFLICT (message_ts) DO NOTHING
       RETURNING *`,
      [messageTs, channelId, channelName || null, userId, username || null, text, embedding ? toSql(embedding) : null]
    );
    return result.rows[0] || null;
  },

  async getAll() {
    const result = await pool.query(
      `SELECT id, message_ts, channel_id, channel_name, user_id, username, text, importance_score, category, created_at
       FROM slack_messages ORDER BY created_at DESC`
    );
    return result.rows;
  },

  async getImportant(limit = 10) {
    const result = await pool.query(
      `SELECT id, message_ts, channel_id, channel_name, user_id, username, text, importance_score, created_at
       FROM slack_messages
       WHERE importance_score >= 3
       ORDER BY importance_score DESC, created_at DESC
       LIMIT $1`,
      [limit]
    );
    return result.rows;
  },
  async getStats() {
    const result = await pool.query(`
      SELECT
        COUNT(*)                                        AS total_messages,
        COUNT(*) FILTER (WHERE embedding IS NOT NULL)   AS synced_to_pgvector,
        COUNT(*) FILTER (WHERE embedding IS NULL)       AS pending_sync,
        COUNT(DISTINCT channel_id)                      AS unique_channels,
        COUNT(DISTINCT user_id)                         AS unique_users
      FROM slack_messages
    `);
    return result.rows[0];
  }
};

module.exports = SlackMessage;
