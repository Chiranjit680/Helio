const jwt = require('jsonwebtoken');
const config = require('../config/config');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Authentication middleware
 * Verifies JWT token and attaches user to request
 */
const authMiddleware = (req, res, next) => {
  try {
    // Get token from header
    const authHeader = req.headers.authorization;
    
    if (!authHeader) {
      throw new AppError('No authorization header provided', 401);
    }

    // Check Bearer token format
    if (!authHeader.startsWith('Bearer ')) {
      throw new AppError('Invalid authorization format. Use Bearer token', 401);
    }

    const token = authHeader.substring(7);

    if (!token) {
      throw new AppError('No token provided', 401);
    }

    // Verify token
    const decoded = jwt.verify(token, config.jwt.secret);
    
    // Attach user info to request
    req.user = {
      id: decoded.id || decoded.sub,
      email: decoded.email,
      role: decoded.role,
    };

    logger.debug('User authenticated', { userId: req.user.id });
    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      next(new AppError('Invalid token', 401));
    } else if (error.name === 'TokenExpiredError') {
      next(new AppError('Token expired', 401));
    } else {
      next(error);
    }
  }
};

/**
 * Optional authentication middleware
 * Attaches user if token is valid, but doesn't fail if no token
 */
const optionalAuth = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const decoded = jwt.verify(token, config.jwt.secret);
      req.user = {
        id: decoded.id || decoded.sub,
        email: decoded.email,
        role: decoded.role,
      };
    }
    
    next();
  } catch (error) {
    // Continue without user for optional auth
    next();
  }
};

/**
 * Role-based authorization middleware
 * @param {string[]} allowedRoles - Array of allowed roles
 */
const authorize = (...allowedRoles) => {
  return (req, res, next) => {
    if (!req.user) {
      return next(new AppError('Authentication required', 401));
    }

    if (!allowedRoles.includes(req.user.role)) {
      return next(new AppError('You do not have permission to perform this action', 403));
    }

    next();
  };
};

module.exports = authMiddleware;
module.exports.optionalAuth = optionalAuth;
module.exports.authorize = authorize;
