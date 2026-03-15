const { pool } = require("../config/database");

const SlackMessage = {
  async save({ messageTs, channelId, userId, text }) {
    const result = await pool.query(
      `INSERT INTO slack_messages (message_ts, channel_id, user_id, text)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (message_ts) DO NOTHING
       RETURNING *`,
      [messageTs, channelId, userId, text]
    );
    return result.rows[0] || null;
  },

  async getAll() {
    const result = await pool.query(
      "SELECT * FROM slack_messages ORDER BY created_at DESC"
    );
    return result.rows;
  },
};

module.exports = SlackMessage;
