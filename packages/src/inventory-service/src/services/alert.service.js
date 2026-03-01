const AlertModel = require('../models/alert.model');
const config = require('../config/config');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get all alerts with pagination and filtering
 */
const getAllAlerts = async ({ page, limit, status, priority, sortBy, order }) => {
  const offset = (page - 1) * limit;
  
  const alerts = await AlertModel.findAll({
    limit,
    offset,
    status,
    priority,
    sortBy,
    order,
  });

  const total = await AlertModel.count({ status, priority });

  return { alerts, total };
};

/**
 * Get a single alert by ID
 */
const getAlertById = async (id) => {
  return await AlertModel.findById(id);
};

/**
 * Create a new alert
 */
const createAlert = async (alertData, userId) => {
  const newAlert = await AlertModel.create({
    ...alertData,
    created_by: userId,
  });

  logger.info(`Alert created: ${newAlert.type} for item ${alertData.item_id}`);

  return newAlert;
};

/**
 * Update an alert
 */
const updateAlert = async (id, updateData, userId) => {
  const existingAlert = await AlertModel.findById(id);
  if (!existingAlert) {
    return null;
  }

  return await AlertModel.update(id, {
    ...updateData,
    updated_by: userId,
  });
};

/**
 * Delete an alert
 */
const deleteAlert = async (id) => {
  const existingAlert = await AlertModel.findById(id);
  if (!existingAlert) {
    return false;
  }

  await AlertModel.delete(id);
  return true;
};

/**
 * Acknowledge an alert
 */
const acknowledgeAlert = async (id, userId) => {
  const existingAlert = await AlertModel.findById(id);
  if (!existingAlert) {
    return null;
  }

  return await AlertModel.update(id, {
    status: 'ACKNOWLEDGED',
    acknowledged_by: userId,
    acknowledged_at: new Date(),
  });
};

/**
 * Get active (unacknowledged) alerts
 */
const getActiveAlerts = async ({ page, limit }) => {
  const offset = (page - 1) * limit;
  
  const alerts = await AlertModel.findActive({ limit, offset });
  const total = await AlertModel.countActive();

  return { alerts, total };
};

/**
 * Check stock level and create alert if needed
 * Uses item's min_quantity for low stock threshold, with critical at 50% of min_quantity
 * Falls back to global config thresholds if item has no min_quantity set
 */
const checkAndCreateLowStockAlert = async (item) => {
  const { lowStockThreshold: globalLowThreshold, criticalStockThreshold: globalCriticalThreshold } = config.alerts;

  // Use item's min_quantity if set, otherwise fall back to global threshold
  const lowStockThreshold = item.min_quantity > 0 ? item.min_quantity : globalLowThreshold;
  // Critical threshold is 50% of low stock threshold (or at least 1)
  const criticalStockThreshold = item.min_quantity > 0 
    ? Math.max(1, Math.floor(item.min_quantity / 2)) 
    : globalCriticalThreshold;

  // Check for existing active alert for this item
  const existingAlert = await AlertModel.findActiveByItemId(item.id);

  if (item.quantity <= criticalStockThreshold) {
    if (!existingAlert || existingAlert.type !== 'CRITICAL_STOCK') {
      // Resolve existing low stock alert if any
      if (existingAlert && existingAlert.type === 'LOW_STOCK') {
        await AlertModel.update(existingAlert.id, { status: 'RESOLVED' });
      }

      // Create critical stock alert
      await AlertModel.create({
        item_id: item.id,
        type: 'CRITICAL_STOCK',
        priority: 'HIGH',
        message: `Critical stock level: ${item.name} has only ${item.quantity} units remaining (threshold: ${criticalStockThreshold})`,
        threshold: criticalStockThreshold,
        current_quantity: item.quantity,
      });

      logger.warn(`Critical stock alert created for item ${item.id}: ${item.name}`);
    }
  } else if (item.quantity <= lowStockThreshold) {
    if (!existingAlert) {
      // Create low stock alert
      await AlertModel.create({
        item_id: item.id,
        type: 'LOW_STOCK',
        priority: 'MEDIUM',
        message: `Low stock warning: ${item.name} has only ${item.quantity} units remaining (threshold: ${lowStockThreshold})`,
        threshold: lowStockThreshold,
        current_quantity: item.quantity,
      });

      logger.info(`Low stock alert created for item ${item.id}: ${item.name}`);
    }
  } else if (existingAlert && existingAlert.status === 'ACTIVE') {
    // Stock is back to normal, resolve alert
    await AlertModel.update(existingAlert.id, { status: 'RESOLVED' });
    logger.info(`Alert resolved for item ${item.id}: ${item.name} - stock replenished`);
  }
};

/**
 * Get alert statistics
 */
const getAlertStats = async () => {
  return await AlertModel.getStats();
};

module.exports = {
  getAllAlerts,
  getAlertById,
  createAlert,
  updateAlert,
  deleteAlert,
  acknowledgeAlert,
  getActiveAlerts,
  checkAndCreateLowStockAlert,
  getAlertStats,
};
