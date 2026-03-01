const express = require('express');
const itemsRoutes = require('./items.routes');
const transactionsRoutes = require('./transactions.routes');
const alertsRoutes = require('./alerts.routes');
const analyticsRoutes = require('./analytics.routes');

const router = express.Router();

// Health check endpoint
router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'inventory-service', timestamp: new Date().toISOString() });
});

// Mount routes
router.use('/items', itemsRoutes);
router.use('/transactions', transactionsRoutes);
router.use('/alerts', alertsRoutes);
router.use('/analytics', analyticsRoutes);

module.exports = router;
