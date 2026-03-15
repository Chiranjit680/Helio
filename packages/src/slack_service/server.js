require("dotenv").config();
const express = require("express");
const cors = require("cors");
const { initDatabase } = require("./src/config/database");
const slackRoutes = require("./src/routes/slack.routes");

const app = express();
const PORT = process.env.PORT || 8002;

app.use(cors());

// Capture raw body for Slack signature verification
app.use(
  express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf.toString();
    },
  })
);


app.use("/api/slack", slackRoutes);


const start = async () => {
  try {
    await initDatabase();
    app.listen(PORT, () => {
      console.log(`Slack service running on port ${PORT}`);
    });
  } catch (err) {
    console.error("Failed to start Slack service:", err.message);
    process.exit(1);
  }
};

start();
