const express = require("express");
const router = express.Router();
const slackController = require("../controllers/slack.controller");
const verifySlackSignature = require("../middleware/verifySlackSignature");

router.get("/health", slackController.healthCheck);
router.get("/messages", slackController.getMessages);
router.post("/send", slackController.sendMessage);
router.post("/events", verifySlackSignature, slackController.handleEvent);

module.exports = router;