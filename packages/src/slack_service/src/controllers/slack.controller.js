const slackService = require("../services/slack.service");

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

module.exports = { handleEvent, getMessages, sendMessage, healthCheck };
