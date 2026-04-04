const slackService = require("../services/slack.service");
const SlackMessage = require("../models/slackMessage.model");
const { bootstrapChannels, smartBroadcast } = require("../services/broadcastServices");

const {
  searchMessages,
  getStats: getKBStats
} = require("../knowledgeBase/slack.knowledgeBase");

const handleEvent = async (req, res) => {
  const { type, event, challenge } = req.body;

  // Slack URL verification challenge
  if (type === "url_verification") {
    return res.json({ challenge });
  }

  // Respond immediately to avoid Slack retry
  res.status(200).send();

  // Process event asynchronously
  if (type === "event_callback" && event) {
    // Ignore bot messages and message subtypes (edits, deletes, etc.)
    if (event.bot_id || event.subtype) return;

    if (event.type === "message") {
      try {
        await slackService.processEvent(event);
      } catch (err) {
        console.error("Error processing Slack event:", err.message);
      }
    }
  }
};

const getMessages = async (req, res) => {
  try {
    const messages = await slackService.getMessages();
    res.json({ messages });
  } catch (err) {
    console.error("Error fetching messages:", err.message);
    res.status(500).json({ error: "Failed to fetch messages" });
  }
};

const sendMessage = async (req, res) => {
  const { channel, text } = req.body;

  if (!channel || !text) {
    return res.status(400).json({ error: "channel and text are required" });
  }

  try {
    const result = await slackService.sendMessage(channel, text);
    res.json({ ok: true, ts: result.ts });
  } catch (err) {
    console.error("Error sending message:", err.message);
    res.status(500).json({ error: "Failed to send message" });
  }
};

const healthCheck = (req, res) => {
  res.json({ status: "ok" });
};

const semanticSearch = async (req, res) => {
  const { query, limit = 5 } = req.query;

  if (!query) {
    return res.status(400).json({ 
      error: "query parameter is required",
      example: "/api/slack/search?query=deployment%20issues&limit=5"
    });
  }

  try {
    const results = await searchMessages(query, parseInt(limit));
    
    res.json({
      query: results.query,
      count: results.count,
      results: results.results
    });
  } catch (err) {
    console.error("Semantic search failed:", err);
    res.status(500).json({ error: "Search failed", details: err.message });
  }
};

// Get system statistics
const getSystemStats = async (req, res) => {
  try {
    const pgStats = await SlackMessage.getStats();
    const kbStats = await getKBStats();

    res.json({
      postgres: {
        total_messages: parseInt(pgStats.total_messages),
        embedded_messages: parseInt(pgStats.synced_to_pgvector),
        pending_embedding: parseInt(pgStats.pending_sync),
        unique_channels: parseInt(pgStats.unique_channels),
        unique_users: parseInt(pgStats.unique_users)
      },
      pgvector: {
        collection_name: kbStats.collectionName,
        total_vectors: kbStats.totalVectors,
        enabled: kbStats.enabled
      }
    });
  } catch (err) {
    console.error("Failed to fetch stats:", err);
    res.status(500).json({ error: "Failed to fetch statistics" });
  }
};

// Get important messages (for future AI scoring)
const getImportantMessages = async (req, res) => {
  try {
    const { limit = 10 } = req.query;
    const messages = await SlackMessage.getImportant(parseInt(limit));
    
    res.json({
      count: messages.length,
      messages: messages
    });
  } catch (err) {
    console.error("Failed to fetch important messages:", err);
    res.status(500).json({ error: "Failed to fetch important messages" });
  }
};

// Bootstrap channels - Index all Slack channels with embeddings
const adminBootstrapChannels = async (req, res) => {
  try {
    console.log("[Admin] Bootstrapping channels...");
    const result = await bootstrapChannels();
    
    res.json({
      status: "ok",
      message: `Successfully indexed ${result.indexed} out of ${result.total} channels`,
      indexed: result.indexed,
      total: result.total
    });
  } catch (err) {
    console.error("[Admin] Bootstrap failed:", err);
    res.status(500).json({ error: "Bootstrap failed", details: err.message });
  }
};

// Smart broadcast - Send message to relevant channels based on intent
const broadcastMessage = async (req, res) => {
  const { intent, message, messageBody, topK = 5, threshold = 0.45 } = req.body;
  const actualMessage = message || messageBody;

  if (!intent || !actualMessage) {
    return res.status(400).json({
      error: "intent and message (or messageBody) are required",
      example: {
        intent: "deployment and infrastructure updates",
        message: "New deployment pipeline is ready for testing",
        topK: 5,
        threshold: 0.45
      }
    });
  }

  try {
    const result = await smartBroadcast({
      intent,
      messageBody: actualMessage,
      topK: parseInt(topK),
      threshold: parseFloat(threshold)
    });

    res.json({
      status: "ok",
      sent_to: result.sentTo,
      failed: result.failed,
      skipped: result.skipped,
      total_sent: result.total
    });
  } catch (err) {
    console.error("Broadcast failed:", err);
    res.status(500).json({ error: "Broadcast failed", details: err.message });
  }
};

module.exports = {
  handleEvent,
  getMessages,
  sendMessage,
  healthCheck,
  semanticSearch,
  getSystemStats,
  getImportantMessages,
  adminBootstrapChannels,
  broadcastMessage
};
