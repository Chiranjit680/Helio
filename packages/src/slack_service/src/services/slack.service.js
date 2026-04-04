const SlackMessage = require("../models/slackMessage.model");
const slackConnector = require("../connectors/slack.connector");
const { generateEmbedding } = require("../knowledgeBase/embeddings");

const processEvent = async (event) => {
  const channelName = await slackConnector.resolveChannelName(event.channel);
  const username    = await slackConnector.resolveUsername(event.user);

  const embedInput = `Channel: ${channelName} | User: ${username} | ${event.text}`;
  const embedding  = await generateEmbedding(embedInput);

  const saved = await SlackMessage.save({
    messageTs: event.ts,
    channelId: event.channel, channelName,
    userId: event.user, username,
    text: event.text, embedding
  });
  return saved;
};

const getMessages = async () => {
  return SlackMessage.getAll();
};

const sendMessage = async (channel, text) => {
  return slackConnector.sendMessage(channel, text);
};

module.exports = { processEvent, getMessages, sendMessage };
