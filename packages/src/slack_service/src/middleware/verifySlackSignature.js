const crypto = require("crypto");

const verifySlackSignature = (req, res, next) => {
  const signingSecret = process.env.SLACK_SIGNING_SECRET;
  const timestamp = req.headers["x-slack-request-timestamp"];
  const slackSignature = req.headers["x-slack-signature"];

  if (!timestamp || !slackSignature) {
    return res.status(400).json({ error: "Missing Slack signature headers" });
  }

  // Reject requests older than 5 minutes to prevent replay attacks
  const fiveMinutesAgo = Math.floor(Date.now() / 1000) - 60 * 5;
  if (parseInt(timestamp) < fiveMinutesAgo) {
    return res.status(403).json({ error: "Request too old" });
  }

  const sigBaseString = `v0:${timestamp}:${req.rawBody}`;
  const mySignature =
    "v0=" +
    crypto
      .createHmac("sha256", signingSecret)
      .update(sigBaseString, "utf8")
      .digest("hex");

  try {
    const isValid = crypto.timingSafeEqual(
      Buffer.from(mySignature, "utf8"),
      Buffer.from(slackSignature, "utf8")
    );
    if (!isValid) {
      return res.status(403).json({ error: "Invalid signature" });
    }
  } catch {
    return res.status(403).json({ error: "Invalid signature" });
  }

  next();
};

module.exports = verifySlackSignature;
