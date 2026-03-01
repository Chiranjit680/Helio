const inventoryService = require('../services/inventory.service');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get all inventory items
 */
const getAllItems = async (req, res, next) => {
  try {
    const { page = 1, limit = 20, category, sortBy = 'created_at', order = 'desc' } = req.query;
    
    const result = await inventoryService.getAllItems({
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
      category,
      sortBy,
      order,
    });

    res.json({
      success: true,
      data: result.items,
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
 * Get a single item by ID
 */
const getItemById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const item = await inventoryService.getItemById(id);

    if (!item) {
      throw new AppError('Item not found', 404);
    }

    res.json({
      success: true,
      data: item,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Create a new inventory item
 */
const createItem = async (req, res, next) => {
  try {
    const itemData = req.body;
    const userId = req.user?.id;

    const newItem = await inventoryService.createItem(itemData, userId);

    logger.info(`Item created: ${newItem.id}`, { userId });

    res.status(201).json({
      success: true,
      data: newItem,
      message: 'Item created successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Update an inventory item
 */
const updateItem = async (req, res, next) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    const userId = req.user?.id;

    const updatedItem = await inventoryService.updateItem(id, updateData, userId);

    if (!updatedItem) {
      throw new AppError('Item not found', 404);
    }

    logger.info(`Item updated: ${id}`, { userId });

    res.json({
      success: true,
      data: updatedItem,
      message: 'Item updated successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Delete an inventory item
 */
const deleteItem = async (req, res, next) => {
  try {
    const { id } = req.params;
    const userId = req.user?.id;

    const deleted = await inventoryService.deleteItem(id);

    if (!deleted) {
      throw new AppError('Item not found', 404);
    }

    logger.info(`Item deleted: ${id}`, { userId });

    res.json({
      success: true,
      message: 'Item deleted successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Update stock quantity
 */
const updateStock = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { quantity, type, notes } = req.body;
    const userId = req.user?.id;

    const result = await inventoryService.updateStock(id, quantity, type, notes, userId);

    logger.info(`Stock updated for item ${id}: ${type} ${quantity}`, { userId });

    res.json({
      success: true,
      data: result,
      message: 'Stock updated successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Search items
 */
const searchItems = async (req, res, next) => {
  try {
    const { q, page = 1, limit = 20 } = req.query;

    if (!q) {
      throw new AppError('Search query is required', 400);
    }

    const result = await inventoryService.searchItems(q, {
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

module.exports = {
  getAllItems,
  getItemById,
  createItem,
  updateItem,
  deleteItem,
  updateStock,
  searchItems,
};
