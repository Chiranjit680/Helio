const logger = require('../utils/logger');
const { AppError } = require('../utils/errors');

/**
 * Global error handling middleware
 */
const errorHandler = (err, req, res, next) => {
  // Log error
  logger.error('Error occurred', {
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.user?.id,
  });

  // Handle known operational errors
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      success: false,
      error: {
        message: err.message,
        code: err.code || 'ERROR',
      },
    });
  }

  // Handle PostgreSQL errors
  if (err.code) {
    switch (err.code) {
      case '23505': // Unique violation
        return res.status(409).json({
          success: false,
          error: {
            message: 'A record with this data already exists',
            code: 'DUPLICATE_ENTRY',
          },
        });
      case '23503': // Foreign key violation
        return res.status(400).json({
          success: false,
          error: {
            message: 'Referenced record does not exist',
            code: 'FOREIGN_KEY_VIOLATION',
          },
        });
      case '23502': // Not null violation
        return res.status(400).json({
          success: false,
          error: {
            message: 'Required field is missing',
            code: 'NULL_VIOLATION',
          },
        });
      case '22P02': // Invalid text representation
        return res.status(400).json({
          success: false,
          error: {
            message: 'Invalid input format',
            code: 'INVALID_INPUT',
          },
        });
    }
  }

  // Handle validation errors
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      success: false,
      error: {
        message: err.message,
        code: 'VALIDATION_ERROR',
      },
    });
  }

  // Handle JWT errors
  if (err.name === 'JsonWebTokenError' || err.name === 'TokenExpiredError') {
    return res.status(401).json({
      success: false,
      error: {
        message: 'Invalid or expired token',
        code: 'AUTH_ERROR',
      },
    });
  }

  // Default server error (don't expose internal details in production)
  const isProduction = process.env.NODE_ENV === 'production';
  
  res.status(500).json({
    success: false,
    error: {
      message: isProduction ? 'Internal server error' : err.message,
      code: 'INTERNAL_ERROR',
      ...(isProduction ? {} : { stack: err.stack }),
    },
  });
};

/**
 * 404 Not Found handler
 */
const notFoundHandler = (req, res) => {
  res.status(404).json({
    success: false,
    error: {
      message: `Route ${req.method} ${req.path} not found`,
      code: 'NOT_FOUND',
    },
  });
};

module.exports = {
  errorHandler,
  notFoundHandler,
};
