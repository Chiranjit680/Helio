const { pool } = require("../config/database");
const { generateEmbedding } = require("./embeddings");
const { toSql } = require("pgvector");
/**
 * Search Slack messages by meaning, not keywords.
 * HR example:   "messages about new employee John onboarding"
 * Finance ex:   "invoice verification electronics pending"
 *
 * @param {string} queryText   - natural language search query
 * @param {number} nResults    - how many results to return
 * @param {Object} filters     - optional { channelId, department, dateFrom }
 */

const searchMessages = async (queryText, nResults = 5, filters = {}) => {
  const queryVector = await generateEmbedding(queryText);
  const conditions = ["embedding IS NOT NULL"];
  const params = [toSql(queryVector)];
  let next = 2;

  if(filters.channelId) {
    conditions.push(`channel_id = $${next++}`);
    params.push(filters.channelId);
  }
  if(filters.department) {
    conditions.push(`channel_name ILIKE $${next++}`);
    params.push(filters.department);
  }
  if (filters.dateFrom) {
    conditions.push(`created_at >= $${next++}`);
    params.push(filters.dateFrom);
  }

  params.push(nResults);
  const sql = `
    SELECT
      channel_name,
      username,
      text,
      created_at,
      1 - (embedding <=> $1::vector) AS similarity_score
    FROM slack_messages
    WHERE ${conditions.join(" AND ")}
    ORDER BY embedding <=> $1::vector   -- closest vector first
    LIMIT $${next}
  `;

    const { rows } = await pool.query(sql, params);
    const results = rows.filter(r => parseFloat(r.similarity_score) >= 0.35).map(r => ({
      channel         : r.channel_name,
      author          : r.username,
      text            : r.text,
      timestamp       : r.created_at,
      similarityScore : parseFloat(r.similarity_score).toFixed(4),
    }));
    return {
    query    : queryText,
    count    : results.length,
    results,
    // keep these shapes so your existing controller works unchanged
    metadatas: results,
    distances: results.map(r => (1 - parseFloat(r.similarityScore)).toFixed(4)),
    };
};


/**
 * Get collection statistics
 * Useful for debugging and monitoring
 */
const getStats = async () => {
  const { rows } = await pool.query(`
    SELECT COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded_count FROM slack_messages
  `);
  return {
    collectionName : "slack_messages (pgvector)",
    totalVectors   : parseInt(rows[0].embedded_count),
    enabled        : true,
  };
};

module.exports = {
  searchMessages,
  getStats
};