const { WebClient } = require("@slack/web-api");

const slackClient = new WebClient(process.env.SLACK_BOT_TOKEN);

const sendMessage = async (channel, text) => {
  const result = await slackClient.chat.postMessage({ channel, text });
  return result;
};

module.exports = { sendMessage };
