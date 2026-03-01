const express = require('express');
const itemsController = require('../controllers/items.controller');
const { validateItem, validateItemUpdate } = require('../middleware/validation.middleware');
const authMiddleware = require('../middleware/auth.middleware');

const router = express.Router();

// Apply auth middleware to all routes
router.use(authMiddleware);

/*
*
 * @route   GET /api/inventory/items
 * @desc    Get all inventory items with pagination and filtering
 * @access  Private
 */
router.get('/', itemsController.getAllItems);

/*
*
 * @route   GET /api/inventory/items/:id
 * @desc    Get a single item by ID
 * @access  Private
 */
router.get('/:id', itemsController.getItemById);

/*
*
 * @route   POST /api/inventory/items
 * @desc    Create a new inventory item
 * @access  Private
 */
router.post('/', validateItem, itemsController.createItem);

/*
*
 * @route   PUT /api/inventory/items/:id
 * @desc    Update an inventory item
 * @access  Private
 */
router.put('/:id', validateItemUpdate, itemsController.updateItem);

/*
*
 * @route   DELETE /api/inventory/items/:id
 * @desc    Delete an inventory item
 * @access  Private
 */
router.delete('/:id', itemsController.deleteItem);

/*
*
 * @route   PATCH /api/inventory/items/:id/stock
 * @desc    Update stock quantity
 * @access  Private
 */
router.patch('/:id/stock', itemsController.updateStock);

/*
*
 * @route   GET /api/inventory/items/search
 * @desc    Search items by name, SKU, or category
 * @access  Private
 */
router.get('/search', itemsController.searchItems);

module.exports = router;
