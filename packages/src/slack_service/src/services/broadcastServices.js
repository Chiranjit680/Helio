const { WebClient }        = require("@slack/web-api");
const { pool }             = require("../config/database");
const { generateEmbedding } = require("../knowledgeBase/embeddings");
const { toSql }            = require("pgvector");

const slack = new WebClient(process.env.SLACK_BOT_TOKEN);

/*
 * Index all channels into the slack_channels table.
 * Run once via POST /api/slack/admin/bootstrap-channels.
 */
const bootstrapChannels = async () => {
  const result   = await slack.conversations.list({
    types : "public_channel,private_channel",
    limit : 1000,
  });
  const channels = result.channels || [];
  let indexed    = 0;

  for (const ch of channels) {
    try {
      // Combine name + topic + purpose into one rich string for embedding
      const embedInput = [
        ch.name,
        ch.topic?.value   || "",
        ch.purpose?.value || "",
      ].join(" ").trim();

      const embedding = await generateEmbedding(embedInput);

      await pool.query(
        `INSERT INTO slack_channels (channel_id, channel_name, topic, purpose, is_private, embedding)
         VALUES ($1, $2, $3, $4, $5, $6)
         ON CONFLICT (channel_id) DO UPDATE SET
           channel_name = EXCLUDED.channel_name,
           topic        = EXCLUDED.topic,
           purpose      = EXCLUDED.purpose,
           embedding    = EXCLUDED.embedding,
           updated_at   = NOW()`,
        [
          ch.id,
          ch.name,
          ch.topic?.value   || null,
          ch.purpose?.value || null,
          ch.is_private     || false,
          toSql(embedding),
        ]
      );

      indexed++;
      console.log(`[Bootstrap] ✅ Indexed #${ch.name}`);
    } catch (err) {
      console.error(`[Bootstrap] ❌ Failed #${ch.name}:`, err.message);
    }
  }

  return { indexed, total: channels.length };
};

/*
 * Find relevant channels for an intent, then send the message to them.
 */
const smartBroadcast = async ({
  intent,
  messageBody,
  topK      = 5,
  threshold = 0.45,
}) => {
  const intentVector = await generateEmbedding(intent);

  // Find channels whose name+topic+purpose is most similar to the intent
  const { rows: channels } = await pool.query(
    `SELECT
       channel_id,
       channel_name,
       1 - (embedding <=> $1::vector) AS similarity_score
     FROM slack_channels
     WHERE embedding IS NOT NULL
     ORDER BY embedding <=> $1::vector
     LIMIT $2`,
    [toSql(intentVector), topK]
  );

  const sentTo  = [];
  const failed  = [];
  const skipped = [];

  for (const ch of channels) {
    const score = parseFloat(ch.similarity_score);

    if (score < threshold) {
      skipped.push({ channel: ch.channel_name, score: score.toFixed(4) });
      continue;
    }

    try {
      await slack.chat.postMessage({
        channel : ch.channel_id,
        text    : messageBody,
        blocks  : [
          { type: "section", text: { type: "mrkdwn", text: messageBody } },
          {
            type     : "context",
            elements : [{
              type : "mrkdwn",
              text : `_Sent via Helio Intelligence · Relevance: ${(score * 100).toFixed(0)}%_`,
            }],
          },
        ],
      });
      sentTo.push({ channel: ch.channel_name, channelId: ch.channel_id, score: score.toFixed(4) });
    } catch (err) {
      failed.push({ channel: ch.channel_name, error: err.message });
    }
  }

  return { sentTo, failed, skipped, total: sentTo.length };
};

const initBroadcastDB = async () => {
  console.log("✅ Broadcast service ready (pgvector)");
};

module.exports = { initBroadcastDB, bootstrapChannels, smartBroadcast };