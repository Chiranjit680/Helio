require('dotenv').config();

const config = {
  // Server configuration
  server: {
    port: parseInt(process.env.PORT, 10) || 3001,
    env: process.env.NODE_ENV || 'development',
  },

  // Database configuration
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT, 10) || 5432,
    name: process.env.DB_NAME || 'inventory_db',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
    poolSize: parseInt(process.env.DB_POOL_SIZE, 10) || 10,
  },

  // JWT configuration
  jwt: {
    secret: process.env.JWT_SECRET || 'your-secret-key',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
  },

  // Logging configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
  },

  // Alert thresholds
  alerts: {
    lowStockThreshold: parseInt(process.env.LOW_STOCK_THRESHOLD, 10) || 10,
    criticalStockThreshold: parseInt(process.env.CRITICAL_STOCK_THRESHOLD, 10) || 5,
  },

  // API Gateway URL
  apiGateway: {
    url: process.env.API_GATEWAY_URL || 'http://localhost:3000',
  },
};

module.exports = config;
