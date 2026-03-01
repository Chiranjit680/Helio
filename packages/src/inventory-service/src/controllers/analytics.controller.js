const analyticsService = require('../services/analytics.service');
const { AppError } = require('../utils/errors');

/*
 * Get inventory overview statistics
 */
const getOverview = async (req, res, next) => {
  try {
    const overview = await analyticsService.getOverview();

    res.json({
      success: true,
      data: overview,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get stock level distribution
 */
const getStockLevels = async (req, res, next) => {
  try {
    const stockLevels = await analyticsService.getStockLevels();

    res.json({
      success: true,
      data: stockLevels,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get stock movement trends
 */
const getStockMovement = async (req, res, next) => {
  try {
    const { startDate, endDate, interval = 'day' } = req.query;

    const validIntervals = ['day', 'week', 'month'];
    if (!validIntervals.includes(interval)) {
      throw new AppError('Invalid interval. Must be day, week, or month', 400);
    }

    const movement = await analyticsService.getStockMovement({
      startDate,
      endDate,
      interval,
    });

    res.json({
      success: true,
      data: movement,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get top items by transaction volume
 */
const getTopItems = async (req, res, next) => {
  try {
    const { limit = 10, period = '30d' } = req.query;

    const topItems = await analyticsService.getTopItems({
      limit: parseInt(limit, 10),
      period,
    });

    res.json({
      success: true,
      data: topItems,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get items with low stock
 */
const getLowStockItems = async (req, res, next) => {
  try {
    const { threshold, page = 1, limit = 20 } = req.query;

    const result = await analyticsService.getLowStockItems({
      threshold: threshold ? parseInt(threshold, 10) : undefined,
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
    });

    res.json({
      success: true,
      data: result.items,
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

/**
 * Get total inventory value
 */
const getInventoryValue = async (req, res, next) => {
  try {
    const { groupBy } = req.query;

    const value = await analyticsService.getInventoryValue({ groupBy });

    res.json({
      success: true,
      data: value,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getOverview,
  getStockLevels,
  getStockMovement,
  getTopItems,
  getLowStockItems,
  getInventoryValue,
};
