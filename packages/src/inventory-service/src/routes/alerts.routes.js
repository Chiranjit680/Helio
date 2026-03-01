const express = require('express');
const alertsController = require('../controllers/alerts.controller');
const { validateAlert, validateAlertUpdate } = require('../middleware/validation.middleware');
const authMiddleware = require('../middleware/auth.middleware');

const router = express.Router();

// Apply auth middleware to all routes
router.use(authMiddleware);

/*
*
 * @route   GET /api/inventory/alerts
 * @desc    Get all alerts with pagination and filtering
 * @access  Private
 */
router.get('/', alertsController.getAllAlerts);

/*
*
 * @route   GET /api/inventory/alerts/:id
 * @desc    Get a single alert by ID
 * @access  Private
 */
router.get('/:id', alertsController.getAlertById);

/*
*
 * @route   POST /api/inventory/alerts
 * @desc    Create a new alert
 * @access  Private
 */
router.post('/', validateAlert, alertsController.createAlert);

/*
*
 * @route   PUT /api/inventory/alerts/:id
 * @desc    Update an alert
 * @access  Private
 */
router.put('/:id', validateAlertUpdate, alertsController.updateAlert);

/*
*
 * @route   DELETE /api/inventory/alerts/:id
 * @desc    Delete an alert
 * @access  Private
 */
router.delete('/:id', alertsController.deleteAlert);

/*
*
 * @route   PATCH /api/inventory/alerts/:id/acknowledge
 * @desc    Acknowledge an alert
 * @access  Private
 */
router.patch('/:id/acknowledge', alertsController.acknowledgeAlert);

/*
*
 * @route   GET /api/inventory/alerts/active
 * @desc    Get all active (unacknowledged) alerts
 * @access  Private
 */
router.get('/active', alertsController.getActiveAlerts);

module.exports = router;
