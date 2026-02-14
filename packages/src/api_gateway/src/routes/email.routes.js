const express = require("express");
const axios = require("axios");

const router = express.Router();

const EMAIL_SERVICE_URL = process.env.EMAIL_SERVICE_URL || "http://localhost:8000";
const GATEWAY_BASE_URL = process.env.GATEWAY_BASE_URL || "http://localhost:3000";

// ==================== PROXY HELPER ====================
async function proxyToEmailService(req, res, endpoint, method = "GET") {
  try {
    const config = {
      method,
      url: `${EMAIL_SERVICE_URL}${endpoint}`,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
        // Forward authorization header if present
        ...(req.headers.authorization && { 
          Authorization: req.headers.authorization 
        })
      }
    };

    // Forward query params
    if (Object.keys(req.query).length > 0) {
      config.params = req.query;
    }

    // Forward body for POST/PUT/PATCH
    if (["POST", "PUT", "PATCH"].includes(method) && req.body) {
      config.data = req.body;
    }

    const response = await axios(config);
    return res.status(response.status).json(response.data);

  } catch (error) {
    console.error(`[Email Proxy Error] ${method} ${endpoint}:`, error.message);
    
    if (error.response) {
      // Forward error response from email service
      return res.status(error.response.status).json(error.response.data);
    }
    
    // Service unavailable
    return res.status(503).json({
      error: "Email service unavailable",
      message: error.message,
      service: "email-service",
      timestamp: new Date().toISOString()
    });
  }
}

// ==================== OAUTH2 ROUTES ====================
// IMPORTANT: These must be handled specially for OAuth flow

// Start Google OAuth flow
router.get("/auth/google", async (req, res) => {
  try {
    // Redirect directly to email service OAuth endpoint
    const response = await axios.get(`${EMAIL_SERVICE_URL}/api/email/auth/google`, {
      maxRedirects: 0,
      validateStatus: (status) => status >= 200 && status < 400
    });
    
    // If email service returns a redirect URL, forward it
    if (response.headers.location) {
      return res.redirect(response.headers.location);
    }
    
    return res.json(response.data);
  } catch (error) {
    if (error.response?.status === 302 || error.response?.status === 307) {
      // Handle redirect
      return res.redirect(error.response.headers.location);
    }
    
    console.error("[OAuth Start Error]:", error.message);
    return res.status(500).json({ error: "Failed to start OAuth flow" });
  }
});

// OAuth callback - Google redirects here after user consent
router.get("/auth/google/callback", async (req, res) => {
  try {
    // Forward the callback with all query params (code, state, etc.)
    const queryString = new URLSearchParams(req.query).toString();
    const callbackUrl = `${EMAIL_SERVICE_URL}/api/email/auth/google/callback?${queryString}`;
    
    const response = await axios.get(callbackUrl, {
      maxRedirects: 0,
      validateStatus: (status) => status >= 200 && status < 400
    });
    
    return res.json(response.data);
  } catch (error) {
    if (error.response?.status >= 300 && error.response?.status < 400) {
      return res.redirect(error.response.headers.location);
    }
    
    console.error("[OAuth Callback Error]:", error.message);
    return res.status(500).json({ 
      error: "OAuth callback failed",
      details: error.response?.data || error.message
    });
  }
});

// Check auth status
router.get("/auth/status", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/auth/status", "GET");
});

// Logout / revoke token
router.post("/auth/logout", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/auth/logout", "POST");
});

// ==================== EMAIL CRUD ROUTES ====================

// Get all emails with optional filters
router.get("/all", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/all", "GET");
});

// Get unread emails
router.get("/unread", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/unread", "GET");
});

// Get important/priority emails
router.get("/important", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/important", "GET");
});

// Get emails by priority level (1, 2, or 3)
router.get("/priority/:level", (req, res) => {
  const { level } = req.params;
  return proxyToEmailService(req, res, `/api/email/priority/${level}`, "GET");
});

// Sync emails from provider
router.get("/sync", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/sync", "GET");
});

router.post("/sync", (req, res) => {
  return proxyToEmailService(req, res, "/api/email/sync", "POST");
});

// Get single email by ID
router.get("/:id", (req, res) => {
  const { id } = req.params;
  return proxyToEmailService(req, res, `/api/email/${id}`, "GET");
});

// Get email summary (AI-generated)
router.get("/:id/summary", (req, res) => {
  const { id } = req.params;
  return proxyToEmailService(req, res, `/api/email/${id}/summary`, "GET");
});

// Get email classification/intent
router.get("/:id/classification", (req, res) => {
  const { id } = req.params;
  return proxyToEmailService(req, res, `/api/email/${id}/classification`, "GET");
});

// ==================== HEALTH CHECK ====================
router.get("/health", async (req, res) => {
  try {
    const response = await axios.get(`${EMAIL_SERVICE_URL}/api/email/health`, {
      timeout: 5000
    });
    
    return res.json({
      gateway: "healthy",
      emailService: response.data,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return res.status(503).json({
      gateway: "healthy",
      emailService: {
        status: "unhealthy",
        error: error.message
      },
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;