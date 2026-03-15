const SlackMessage = require("../models/slackMessage.model");
const slackConnector = require("../connectors/slack.connector");

const processEvent = async (event) => {
  const saved = await SlackMessage.save({
    messageTs: event.ts,
    channelId: event.channel,
    userId: event.user,
    text: event.text,
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
