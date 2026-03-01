const config = require('../config/config');

/**
 * Log levels
 */
const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
};

/**
 * Get current log level threshold
 */
const getCurrentLevel = () => {
  return LOG_LEVELS[config.logging.level] || LOG_LEVELS.info;
};

/**
 * Format log message
 * @param {string} level - Log level
 * @param {string} message - Log message
 * @param {Object} meta - Additional metadata
 * @returns {string} Formatted log message
 */
const formatMessage = (level, message, meta = {}) => {
  const timestamp = new Date().toISOString();
  const metaStr = Object.keys(meta).length > 0 ? ` ${JSON.stringify(meta)}` : '';
  return `[${timestamp}] [${level.toUpperCase()}] ${message}${metaStr}`;
};

/**
 * Log error message
 * @param {string} message - Log message
 * @param {Object} meta - Additional metadata
 */
const error = (message, meta = {}) => {
  if (getCurrentLevel() >= LOG_LEVELS.error) {
    console.error(formatMessage('error', message, meta));
  }
};

/**
 * Log warning message
 * @param {string} message - Log message
 * @param {Object} meta - Additional metadata
 */
const warn = (message, meta = {}) => {
  if (getCurrentLevel() >= LOG_LEVELS.warn) {
    console.warn(formatMessage('warn', message, meta));
  }
};

/**
 * Log info message
 * @param {string} message - Log message
 * @param {Object} meta - Additional metadata
 */
const info = (message, meta = {}) => {
  if (getCurrentLevel() >= LOG_LEVELS.info) {
    console.log(formatMessage('info', message, meta));
  }
};

/**
 * Log debug message
 * @param {string} message - Log message
 * @param {Object} meta - Additional metadata
 */
const debug = (message, meta = {}) => {
  if (getCurrentLevel() >= LOG_LEVELS.debug) {
    console.log(formatMessage('debug', message, meta));
  }
};

/**
 * Create a child logger with preset metadata
 * @param {Object} defaultMeta - Default metadata for all logs
 * @returns {Object} Logger instance with preset metadata
 */
const child = (defaultMeta = {}) => {
  return {
    error: (msg, meta = {}) => error(msg, { ...defaultMeta, ...meta }),
    warn: (msg, meta = {}) => warn(msg, { ...defaultMeta, ...meta }),
    info: (msg, meta = {}) => info(msg, { ...defaultMeta, ...meta }),
    debug: (msg, meta = {}) => debug(msg, { ...defaultMeta, ...meta }),
  };
};

module.exports = {
  error,
  warn,
  info,
  debug,
  child,
  LOG_LEVELS,
};
