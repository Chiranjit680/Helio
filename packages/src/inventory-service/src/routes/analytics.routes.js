const express = require('express');
const analyticsController = require('../controllers/analytics.controller');
const authMiddleware = require('../middleware/auth.middleware');

const router = express.Router();

// Apply auth middleware to all routes
router.use(authMiddleware);

/*
*
 * @route   GET /api/inventory/analytics/overview
 * @desc    Get inventory overview statistics
 * @access  Private
 */
router.get('/overview', analyticsController.getOverview);

/*
 *
 * @route   GET /api/inventory/analytics/stock-levels
 * @desc    Get stock level distribution
 * @access  Private
 */
router.get('/stock-levels', analyticsController.getStockLevels);

/*
*
 * @route   GET /api/inventory/analytics/movement
 * @desc    Get stock movement trends over time
 * @access  Private
 */
router.get('/movement', analyticsController.getStockMovement);

/*
*
 * @route   GET /api/inventory/analytics/top-items
 * @desc    Get top items by transaction volume
 * @access  Private
 */
router.get('/top-items', analyticsController.getTopItems);

/*
*
 * @route   GET /api/inventory/analytics/low-stock
 * @desc    Get items with low stock
 * @access  Private
 */
router.get('/low-stock', analyticsController.getLowStockItems);

/*
*
 * @route   GET /api/inventory/analytics/value
 * @desc    Get total inventory value
 * @access  Private
 */
router.get('/value', analyticsController.getInventoryValue);

module.exports = router;
