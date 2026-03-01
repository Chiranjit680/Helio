const { createServer } = require("./server");
const healthRoutes = require("./routes/health.routes");
const emailRoutes = require("./routes/email.routes");

const PORT = process.env.PORT || 3000;
const EMAIL_SERVICE_URL = process.env.EMAIL_SERVICE_URL || "http://localhost:8000";

const app = createServer();

// =========== REGISTER ROUTES =============
app.use("/api/health", healthRoutes);
app.use("/api/email", emailRoutes);

// =========== STARTUP =============
const server = app.listen(PORT, () => {
  console.log(`

          HELIO API GATEWAY STARTED              
╠════════════════════════════════════════════════════╣
║  Environment: ${process.env.NODE_ENV || "development"}
║  Port:        ${PORT}
║  Email Service: ${EMAIL_SERVICE_URL}
║  
║  Endpoints:
║  ├─ Root:      http://localhost:${PORT}/
║  ├─ Health:    http://localhost:${PORT}/api/health
║  └─ Email API: http://localhost:${PORT}/api/email
║
║  Security:
║  ├─ Rate Limiting: (100 req/15min)
║  └─ CORS: Enabled
╚════════════════════════════════════════════════════╝
  `);
  
  // Log environment info in dev mode
  if (process.env.NODE_ENV === "development") {
    console.log("Dev Mode: Detailed logging enabled");
  }
});

// =========== GRACEFUL SHUTDOWN =============
const gracefulShutdown = (signal) => {
  console.log(`\n${signal} received, shutting down gracefully...`);
  
  server.close(() => {
    console.log("Server closed");
    process.exit(0);
  });
  
  // Force shutdown after 10 seconds
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 10000);
};

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

// =========== UNHANDLED ERRORS =============
process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  process.exit(1);
});

