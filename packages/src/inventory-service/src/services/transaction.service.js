const TransactionModel = require('../models/transaction.model');
const ItemModel = require('../models/item.model');
const alertService = require('./alert.service');
const { AppError } = require('../utils/errors');
const db = require('../config/database');

/**
 * Get all transactions with pagination and filtering
 */
const getAllTransactions = async ({ page, limit, startDate, endDate, type, sortBy, order }) => {
  const offset = (page - 1) * limit;
  
  const transactions = await TransactionModel.findAll({
    limit,
    offset,
    startDate,
    endDate,
    type,
    sortBy,
    order,
  });

  const total = await TransactionModel.count({ startDate, endDate, type });

  return { transactions, total };
};

/**
 * Get a single transaction by ID
 */
const getTransactionById = async (id) => {
  return await TransactionModel.findById(id);
};

/**
 * Create a new transaction and update inventory
 */
const createTransaction = async (transactionData, userId) => {
  const { item_id, type, quantity, notes } = transactionData;

  // Verify item exists
  const item = await ItemModel.findById(item_id);
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
        throw new AppError('Insufficient stock for this transaction', 400);
      }
      newQuantity = item.quantity - quantity;
      break;
    case 'ADJUSTMENT':
      newQuantity = quantity;
      break;
    default:
      throw new AppError('Invalid transaction type. Must be IN, OUT, or ADJUSTMENT', 400);
  }

  // Use transaction to ensure atomicity
  const result = await db.transaction(async (client) => {
    // Create transaction record
    const transaction = await TransactionModel.create({
      item_id,
      type,
      quantity,
      previous_quantity: item.quantity,
      new_quantity: newQuantity,
      notes,
      created_by: userId,
    }, client);

    // Update item quantity
    await ItemModel.updateQuantity(item_id, newQuantity, client);

    return transaction;
  });

  // Check for low stock alert after transaction
  const updatedItem = await ItemModel.findById(item_id);
  await alertService.checkAndCreateLowStockAlert(updatedItem);

  return result;
};

/**
 * Get transactions for a specific item
 */
const getTransactionsByItem = async (itemId, { page, limit }) => {
  const offset = (page - 1) * limit;
  
  // Verify item exists
  const item = await ItemModel.findById(itemId);
  if (!item) {
    throw new AppError('Item not found', 404);
  }

  const transactions = await TransactionModel.findByItemId(itemId, { limit, offset });
  const total = await TransactionModel.countByItemId(itemId);

  return { transactions, total };
};

/**
 * Get transactions by type
 */
const getTransactionsByType = async (type, { page, limit }) => {
  const offset = (page - 1) * limit;
  
  const transactions = await TransactionModel.findByType(type, { limit, offset });
  const total = await TransactionModel.countByType(type);

  return { transactions, total };
};

/**
 * Get transaction summary for a date range
 */
const getTransactionSummary = async (startDate, endDate) => {
  return await TransactionModel.getSummary(startDate, endDate);
};

module.exports = {
  getAllTransactions,
  getTransactionById,
  createTransaction,
  getTransactionsByItem,
  getTransactionsByType,
  getTransactionSummary,
};
