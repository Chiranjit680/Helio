const alertService = require('../services/alert.service');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get all alerts
 */
const getAllAlerts = async (req, res, next) => {
  try {
    const { 
      page = 1, 
      limit = 20, 
      status,
      priority,
      sortBy = 'created_at', 
      order = 'desc' 
    } = req.query;

    const result = await alertService.getAllAlerts({
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
      status,
      priority,
      sortBy,
      order,
    });

    res.json({
      success: true,
      data: result.alerts,
      pagination: {
        page: parseInt(page, 10),
        limit: parseInt(limit, 10),
        total: result.total,
        totalPages: Math.ceil(result.total / limit),
      },
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get a single alert by ID
 */
const getAlertById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const alert = await alertService.getAlertById(id);

    if (!alert) {
      throw new AppError('Alert not found', 404);
    }

    res.json({
      success: true,
      data: alert,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Create a new alert
 */
const createAlert = async (req, res, next) => {
  try {
    const alertData = req.body;
    const userId = req.user?.id;

    const newAlert = await alertService.createAlert(alertData, userId);

    logger.info(`Alert created: ${newAlert.id}`, { userId, type: alertData.type });

    res.status(201).json({
      success: true,
      data: newAlert,
      message: 'Alert created successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Update an alert
 */
const updateAlert = async (req, res, next) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    const userId = req.user?.id;

    const updatedAlert = await alertService.updateAlert(id, updateData, userId);

    if (!updatedAlert) {
      throw new AppError('Alert not found', 404);
    }

    logger.info(`Alert updated: ${id}`, { userId });

    res.json({
      success: true,
      data: updatedAlert,
      message: 'Alert updated successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Delete an alert
 */
const deleteAlert = async (req, res, next) => {
  try {
    const { id } = req.params;
    const userId = req.user?.id;

    const deleted = await alertService.deleteAlert(id);

    if (!deleted) {
      throw new AppError('Alert not found', 404);
    }

    logger.info(`Alert deleted: ${id}`, { userId });

    res.json({
      success: true,
      message: 'Alert deleted successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Acknowledge an alert
 */
const acknowledgeAlert = async (req, res, next) => {
  try {
    const { id } = req.params;
    const userId = req.user?.id;

    const updatedAlert = await alertService.acknowledgeAlert(id, userId);

    if (!updatedAlert) {
      throw new AppError('Alert not found', 404);
    }

    logger.info(`Alert acknowledged: ${id}`, { userId });

    res.json({
      success: true,
      data: updatedAlert,
      message: 'Alert acknowledged successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get active (unacknowledged) alerts
 */
const getActiveAlerts = async (req, res, next) => {
  try {
    const { page = 1, limit = 20 } = req.query;

    const result = await alertService.getActiveAlerts({
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
    });

    res.json({
      success: true,
      data: result.alerts,
      pagination: {
        page: parseInt(page, 10),
        limit: parseInt(limit, 10),
        total: result.total,
      },
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getAllAlerts,
  getAlertById,
  createAlert,
  updateAlert,
  deleteAlert,
  acknowledgeAlert,
  getActiveAlerts,
};
