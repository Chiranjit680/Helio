const logger = require('../utils/logger');

/**
 * Request logging middleware
 */
const requestLogger = (req, res, next) => {
  const startTime = Date.now();

  // Log request
  logger.info(`Incoming request`, {
    method: req.method,
    path: req.path,
    query: req.query,
    ip: req.ip || req.connection.remoteAddress,
    userAgent: req.get('User-Agent'),
    userId: req.user?.id,
  });

  // Log response when finished
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logLevel = res.statusCode >= 400 ? 'warn' : 'info';

    logger[logLevel](`Request completed`, {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      userId: req.user?.id,
    });
  });

  next();
};

/**
 * Correlation ID middleware
 * Adds a unique ID to each request for tracing
 */
const correlationId = (req, res, next) => {
  const id = req.headers['x-correlation-id'] || generateCorrelationId();
  req.correlationId = id;
  res.setHeader('X-Correlation-ID', id);
  next();
};

/**
 * Generate a simple correlation ID
 */
const generateCorrelationId = () => {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
};

module.exports = {
  requestLogger,
  correlationId,
};
