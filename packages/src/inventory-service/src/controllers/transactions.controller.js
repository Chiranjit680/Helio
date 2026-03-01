const transactionService = require('../services/transaction.service');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

/**
 * Get all transactions
 */
const getAllTransactions = async (req, res, next) => {
  try {
    const { 
      page = 1, 
      limit = 20, 
      startDate, 
      endDate, 
      type,
      sortBy = 'created_at', 
      order = 'desc' 
    } = req.query;

    const result = await transactionService.getAllTransactions({
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
      startDate,
      endDate,
      type,
      sortBy,
      order,
    });

    res.json({
      success: true,
      data: result.transactions,
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
 * Get a single transaction by ID
 */
const getTransactionById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const transaction = await transactionService.getTransactionById(id);

    if (!transaction) {
      throw new AppError('Transaction not found', 404);
    }

    res.json({
      success: true,
      data: transaction,
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Create a new transaction
 */
const createTransaction = async (req, res, next) => {
  try {
    const transactionData = req.body;
    const userId = req.user?.id;

    const newTransaction = await transactionService.createTransaction(transactionData, userId);

    logger.info(`Transaction created: ${newTransaction.id}`, { 
      userId, 
      type: transactionData.type,
      itemId: transactionData.item_id 
    });

    res.status(201).json({
      success: true,
      data: newTransaction,
      message: 'Transaction created successfully',
    });
  } catch (error) {
    next(error);
  }
};

/**
 * Get transactions for a specific item
 */
const getTransactionsByItem = async (req, res, next) => {
  try {
    const { itemId } = req.params;
    const { page = 1, limit = 20 } = req.query;

    const result = await transactionService.getTransactionsByItem(itemId, {
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
    });

    res.json({
      success: true,
      data: result.transactions,
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
 * Get transactions by type
 */
const getTransactionsByType = async (req, res, next) => {
  try {
    const { type } = req.params;
    const { page = 1, limit = 20 } = req.query;

    const validTypes = ['IN', 'OUT', 'ADJUSTMENT'];
    if (!validTypes.includes(type.toUpperCase())) {
      throw new AppError('Invalid transaction type. Must be IN, OUT, or ADJUSTMENT', 400);
    }

    const result = await transactionService.getTransactionsByType(type.toUpperCase(), {
      page: parseInt(page, 10),
      limit: parseInt(limit, 10),
    });

    res.json({
      success: true,
      data: result.transactions,
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
  getAllTransactions,
  getTransactionById,
  createTransaction,
  getTransactionsByItem,
  getTransactionsByType,
};
