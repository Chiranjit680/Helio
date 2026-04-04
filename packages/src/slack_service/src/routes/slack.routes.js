const express = require("express");
const router = express.Router();
const slackController = require("../controllers/slack.controller");
const verifySlackSignature = require("../middleware/verifySlackSignature");

// Basic endpoints
router.get("/health", slackController.healthCheck);
router.get("/messages", slackController.getMessages);
router.post("/send", slackController.sendMessage);
router.post("/events", verifySlackSignature, slackController.handleEvent);

// Semantic search endpoint
router.get("/search", slackController.semanticSearch);

// Important messages endpoint
router.get("/important", slackController.getImportantMessages);

// System statistics
router.get("/stats", slackController.getSystemStats);

// Admin endpoints
router.post("/admin/bootstrap-channels", slackController.adminBootstrapChannels);

// Broadcast endpoint
router.post("/broadcast", slackController.broadcastMessage);

module.exports = router;