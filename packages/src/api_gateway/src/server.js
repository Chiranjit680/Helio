require("dotenv").config();
const express = require("express");
const rateLimit = require("express-rate-limit");
const helmet = require("helmet");
const cors = require("cors");

function createServer() {
  const app = express();

  // ==================== SECURITY ====================
  app.use(helmet({
    // Disable some helmet features that interfere with OAuth redirects
    contentSecurityPolicy: false
  }));

  // CORS - Important for OAuth flow
  const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(",") || [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000"
  ];

  app.use(cors({
    origin: function (origin, callback) {
      // Allow requests with no origin (OAuth redirects, Postman, etc.)
      if (!origin) return callback(null, true);
      if (allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("Not allowed by CORS"));
      }
    },
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With"]
  }));

  // ==================== RATE LIMITING ====================
  const generalLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,
    message: { error: "Too many requests, please try again later" },
    skip: (req) => {
      // Skip rate limiting for health checks and OAuth callbacks
      return req.path.includes("/health") || 
             req.path.includes("/auth/google/callback");
    }
  });

  // Stricter limit for auth endpoints to prevent abuse
  const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10, // Only 10 auth attempts per 15 min
    message: { error: "Too many authentication attempts" }
  });

  app.use("/api/", generalLimiter);
  app.use("/api/email/auth/google", authLimiter);

  // ==================== BODY PARSING ====================
  app.use(express.json({ limit: "10mb" }));
  app.use(express.urlencoded({ extended: true, limit: "10mb" }));

  // ==================== REQUEST LOGGING ====================
  app.use((req, res, next) => {
    const start = Date.now();
    
    res.on("finish", () => {
      const duration = Date.now() - start;
      const logLine = `[${new Date().toISOString()}] ${req.method} ${req.originalUrl} - ${res.statusCode} (${duration}ms)`;
      
      if (res.statusCode >= 400) {
        console.error(logLine);
      } else {
        console.log(logLine);
      }
    });
    
    next();
  });

  // ==================== ROOT INFO ====================
  app.get("/", (req, res) => {
    res.json({
      service: "Helio API Gateway",
      version: "1.0.0-mvp",
      status: "operational",
      timestamp: new Date().toISOString(),
      endpoints: {
        health: "/api/health",
        email: {
          base: "/api/email",
          auth: "/api/email/auth/google",
          sync: "/api/email/sync",
          all: "/api/email/all",
          unread: "/api/email/unread",
          important: "/api/email/important"
        }
      }
    });
  });

  // ==================== GATEWAY HEALTH ====================
  app.get("/health", (req, res) => {
    res.json({
      status: "healthy",
      service: "api-gateway",
      uptime: Math.floor(process.uptime()),
      memory: process.memoryUsage(),
      timestamp: new Date().toISOString()
    });
  });

  // ==================== 404 HANDLER ====================
  app.use((req, res, next) => {
    res.status(404).json({
      error: "Not Found",
      message: `Route ${req.method} ${req.path} does not exist`,
      availableEndpoints: ["/api/email", "/api/health"]
    });
  });

  // ==================== ERROR HANDLER ====================
  app.use((err, req, res, next) => {
    console.error(`[Error] ${err.message}`);
    console.error(err.stack);

    res.status(err.status || 500).json({
      error: err.message || "Internal Server Error",
      ...(process.env.NODE_ENV === "development" && { stack: err.stack })
    });
  });

  return app;
}

module.exports = { createServer };