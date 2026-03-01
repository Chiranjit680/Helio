const ItemModel = require('../models/item.model');
const TransactionModel = require('../models/transaction.model');
const alertService = require('./alert.service');
const config = require('../config/config');
const { AppError } = require('../utils/errors');
const db = require('../config/database');

/**
 * Get all inventory items with pagination and filtering
 */
const getAllItems = async ({ page, limit, category, sortBy, order }) => {
  const offset = (page - 1) * limit;
  
  const items = await ItemModel.findAll({
    limit,
    offset,
    category,
    sortBy,
    order,
  });

  const total = await ItemModel.count({ category });

  return { items, total };
};

/**
 * Get a single item by ID
 */
const getItemById = async (id) => {
  return await ItemModel.findById(id);
};

/**
 * Create a new inventory item
 */
const createItem = async (itemData, userId) => {
  const existingItem = await ItemModel.findBySku(itemData.sku);
  if (existingItem) {
    throw new AppError('Item with this SKU already exists', 409);
  }

  const newItem = await ItemModel.create({
    ...itemData,
    created_by: userId,
  });

  // Check if initial stock is low and create alert
  if (itemData.quantity <= config.alerts.lowStockThreshold) {
    await alertService.checkAndCreateLowStockAlert(newItem);
  }

  return newItem;
};

/**
 * Update an inventory item
 */
const updateItem = async (id, updateData, userId) => {
  const existingItem = await ItemModel.findById(id);
  if (!existingItem) {
    return null;
  }

  // Check if SKU is being changed and if new SKU exists
  if (updateData.sku && updateData.sku !== existingItem.sku) {
    const skuExists = await ItemModel.findBySku(updateData.sku);
    if (skuExists) {
      throw new AppError('Item with this SKU already exists', 409);
    }
  }

  return await ItemModel.update(id, {
    ...updateData,
    updated_by: userId,
  });
};

/**
 * Delete an inventory item
 */
const deleteItem = async (id) => {
  const existingItem = await ItemModel.findById(id);
  if (!existingItem) {
    return false;
  }

  await ItemModel.delete(id);
  return true;
};

/**
 * Update stock quantity with transaction recording
 */
const updateStock = async (id, quantity, type, notes, userId) => {
  const item = await ItemModel.findById(id);
  if (!item) {
    throw new AppError('Item not found', 404);
  }

  let newQuantity;
  switch (type) {
    case 'IN':
      newQuantity = item.quantity + quantity;
      break;
    case 'OUT':
      if (item.quantity < quantity) {
        throw new AppError('Insufficient stock', 400);
      }
      newQuantity = item.quantity - quantity;
      break;
    case 'ADJUSTMENT':
      newQuantity = quantity;
      break;
    default:
      throw new AppError('Invalid transaction type', 400);
  }

  // Use transaction to ensure atomicity
  const result = await db.transaction(async (client) => {
    // Update item quantity
    const updatedItem = await ItemModel.updateQuantity(id, newQuantity, client);

    // Record transaction
    await TransactionModel.create({
      item_id: id,
      type,
      quantity,
      previous_quantity: item.quantity,
      new_quantity: newQuantity,
      notes,
      created_by: userId,
    }, client);

    return updatedItem;
  });

  // Check for low stock alert
  await alertService.checkAndCreateLowStockAlert(result);

  return result;
};

/**
 * Search items by name, SKU, or category
 */
const searchItems = async (query, { page, limit }) => {
  const offset = (page - 1) * limit;
  
  const items = await ItemModel.search(query, { limit, offset });
  const total = await ItemModel.searchCount(query);

  return { items, total };
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
