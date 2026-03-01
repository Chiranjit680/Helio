const express = require('express');
const transactionsController = require('../controllers/transactions.controller');
const { validateTransaction } = require('../middleware/validation.middleware');
const authMiddleware = require('../middleware/auth.middleware');

const router = express.Router();

// Apply auth middleware to all routes
router.use(authMiddleware);

/*
*
 * @route   GET /api/inventory/transactions
 * @desc    Get all transactions with pagination and filtering
 * @access  Private
 */
router.get('/', transactionsController.getAllTransactions);

/*
*
 * @route   GET /api/inventory/transactions/:id
 * @desc    Get a single transaction by ID
 * @access  Private
 */
router.get('/:id', transactionsController.getTransactionById);

/*
*
 * @route   POST /api/inventory/transactions
 * @desc    Create a new transaction (stock in/out)
 * @access  Private
 */
router.post('/', validateTransaction, transactionsController.createTransaction);

/*
*
 * @route   GET /api/inventory/transactions/item/:itemId
 * @desc    Get all transactions for a specific item
 * @access  Private
 */
router.get('/item/:itemId', transactionsController.getTransactionsByItem);

/*
*
 * @route   GET /api/inventory/transactions/type/:type
 * @desc    Get transactions by type (IN, OUT, ADJUSTMENT)
 * @access  Private
 */
router.get('/type/:type', transactionsController.getTransactionsByType);

module.exports = router;
