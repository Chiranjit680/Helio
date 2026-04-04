require("dotenv").config();
const express = require("express");
const cors = require("cors");

const { initDatabase } = require("./src/config/database");
const slackRoutes = require("./src/routes/slack.routes");
const { initEmbedder } = require("./src/knowledgeBase/embeddings");
const { initBroadcastDB } = require("./src/services/broadcastServices");

const app  = express();
const PORT = process.env.PORT || 8002;

app.use(cors());
app.use(express.json({
  verify: (req, _res, buf) => { req.rawBody = buf.toString(); }
}));
app.use("/api/slack", slackRoutes);

const start = async () => {
  try {
    console.log("Starting Slack Service...\n");

    console.log("[1/3] Initializing PostgreSQL + pgvector...");
    await initDatabase();

    console.log("[2/3] Loading MiniLM-L6 model (first run ~10s)...");
    await initEmbedder();

    console.log("[3/3] Initializing broadcast service...");
    await initBroadcastDB();

    app.listen(PORT, () => {
      console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
      console.log(`Slack Service is READY`);
      console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
      console.log(` Server:    http://localhost:${PORT}`);
      console.log(` Search:    GET  /api/slack/search?query=...`);
      console.log(` Broadcast: POST /api/slack/broadcast`);
      console.log(` Bootstrap: POST /api/slack/admin/bootstrap-channels`);
      console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
    });
  } catch (err) {
    console.error("Failed to start:", err.message);
    process.exit(1);
  }
};

start();