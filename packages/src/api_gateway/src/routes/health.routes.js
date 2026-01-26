const express = require("express");

const router = express.Router();

router.get("/health", (req, res) => {
  res.json({
    status: "UP",
    service: "api-gateway"
  });
});

module.exports = router;