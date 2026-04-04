const { WebClient } = require("@slack/web-api");

const slackClient = new WebClient(process.env.SLACK_BOT_TOKEN);

const channelCache = {};
const userCache = {};

const sendMessage = async (channel, text) => {
  const result = await slackClient.chat.postMessage({ channel, text });
  return result;
};

const sendRichMessage = async (channel, text, blocks) => {
  const result = await slackClient.chat.postMessage({ channel, text, blocks });
  return result;
};

const resolveChannelName = async (channelId) => {
  if (!channelId) return "unknown-channel";
  if (channelCache[channelId]) return channelCache[channelId];

  try {
    const res  = await slackClient.conversations.info({ channel: channelId });
    const name = res.channel.name;
    channelCache[channelId] = name;
    return name;
  } catch {
    // Bot might not be a member of this channel — fall back silently
    return channelId;
  }
};

const resolveUsername = async (userId) => {
  if (!userId) return "unknown-user";
  if (userCache[userId]) return userCache[userId];

  try {
    const res  = await slackClient.users.info({ user: userId });
    const name = res.user.real_name || res.user.display_name || res.user.name;
    userCache[userId] = name;
    return name;
  } catch {
    return userId;
  }
};


const getAllChannels = async () => {
  const result = await slackClient.conversations.list({
    types : "public_channel,private_channel",
    limit : 1000,
  });
  return result.channels || [];
};

module.exports = {
  sendMessage,
  sendRichMessage,
  resolveChannelName,
  resolveUsername,
  getAllChannels,
};