const express = require("express");

function createServer() {
  const app = express();

  app.use(express.json());

  return app;
}

module.exports = { createServer };