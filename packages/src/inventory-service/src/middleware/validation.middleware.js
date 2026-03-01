const { AppError } = require('../utils/errors');
const { validateItemData, validateTransactionData, validateAlertData } = require('../utils/validators');

/**
 * Validate item creation request
 */
const validateItem = (req, res, next) => {
  const { sku, name, category } = req.body;

  const errors = [];

  if (!sku || typeof sku !== 'string' || sku.trim().length === 0) {
    errors.push('SKU is required and must be a non-empty string');
  } else if (sku.length > 50) {
    errors.push('SKU must not exceed 50 characters');
  }

  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    errors.push('Name is required and must be a non-empty string');
  } else if (name.length > 255) {
    errors.push('Name must not exceed 255 characters');
  }

  if (!category || typeof category !== 'string' || category.trim().length === 0) {
    errors.push('Category is required');
  }

  if (req.body.quantity !== undefined) {
    const quantity = Number(req.body.quantity);
    if (isNaN(quantity) || quantity < 0) {
      errors.push('Quantity must be a non-negative number');
    }
  }

  if (req.body.unit_price !== undefined) {
    const price = Number(req.body.unit_price);
    if (isNaN(price) || price < 0) {
      errors.push('Unit price must be a non-negative number');
    }
  }

  if (req.body.min_quantity !== undefined) {
    const minQty = Number(req.body.min_quantity);
    if (isNaN(minQty) || minQty < 0) {
      errors.push('Minimum quantity must be a non-negative number');
    }
  }

  if (errors.length > 0) {
    return next(new AppError(errors.join('; '), 400));
  }

  // Sanitize input
  req.body.sku = sku.trim();
  req.body.name = name.trim();
  req.body.category = category.trim();
  if (req.body.description) req.body.description = req.body.description.trim();
  if (req.body.location) req.body.location = req.body.location.trim();

  next();
};

/**
 * Validate item update request
 */
const validateItemUpdate = (req, res, next) => {
  const errors = [];

  if (req.body.sku !== undefined) {
    if (typeof req.body.sku !== 'string' || req.body.sku.trim().length === 0) {
      errors.push('SKU must be a non-empty string');
    } else if (req.body.sku.length > 50) {
      errors.push('SKU must not exceed 50 characters');
    }
  }

  if (req.body.name !== undefined) {
    if (typeof req.body.name !== 'string' || req.body.name.trim().length === 0) {
      errors.push('Name must be a non-empty string');
    } else if (req.body.name.length > 255) {
      errors.push('Name must not exceed 255 characters');
    }
  }

  if (req.body.unit_price !== undefined) {
    const price = Number(req.body.unit_price);
    if (isNaN(price) || price < 0) {
      errors.push('Unit price must be a non-negative number');
    }
  }

  if (req.body.min_quantity !== undefined) {
    const minQty = Number(req.body.min_quantity);
    if (isNaN(minQty) || minQty < 0) {
      errors.push('Minimum quantity must be a non-negative number');
    }
  }

  if (errors.length > 0) {
    return next(new AppError(errors.join('; '), 400));
  }

  // Sanitize input
  if (req.body.sku) req.body.sku = req.body.sku.trim();
  if (req.body.name) req.body.name = req.body.name.trim();
  if (req.body.category) req.body.category = req.body.category.trim();
  if (req.body.description) req.body.description = req.body.description.trim();
  if (req.body.location) req.body.location = req.body.location.trim();

  next();
};

/**
 * Validate transaction request
 */
const validateTransaction = (req, res, next) => {
  const { item_id, type, quantity } = req.body;

  const errors = [];

  if (!item_id) {
    errors.push('Item ID is required');
  }

  if (!type) {
    errors.push('Transaction type is required');
  } else {
    const validTypes = ['IN', 'OUT', 'ADJUSTMENT'];
    if (!validTypes.includes(type.toUpperCase())) {
      errors.push('Transaction type must be IN, OUT, or ADJUSTMENT');
    }
  }

  if (quantity === undefined || quantity === null) {
    errors.push('Quantity is required');
  } else {
    const qty = Number(quantity);
    if (isNaN(qty) || qty <= 0) {
      errors.push('Quantity must be a positive number');
    }
  }

  if (errors.length > 0) {
    return next(new AppError(errors.join('; '), 400));
  }

  // Normalize type
  req.body.type = type.toUpperCase();
  if (req.body.notes) req.body.notes = req.body.notes.trim();

  next();
};

/**
 * Validate alert creation request
 */
const validateAlert = (req, res, next) => {
  const { type, message } = req.body;

  const errors = [];

  if (!type) {
    errors.push('Alert type is required');
  } else {
    const validTypes = ['LOW_STOCK', 'CRITICAL_STOCK', 'OUT_OF_STOCK', 'EXPIRING', 'CUSTOM'];
    if (!validTypes.includes(type)) {
      errors.push('Invalid alert type');
    }
  }

  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    errors.push('Message is required');
  }

  if (req.body.priority) {
    const validPriorities = ['LOW', 'MEDIUM', 'HIGH'];
    if (!validPriorities.includes(req.body.priority)) {
      errors.push('Priority must be LOW, MEDIUM, or HIGH');
    }
  }

  if (errors.length > 0) {
    return next(new AppError(errors.join('; '), 400));
  }

  req.body.message = message.trim();
  next();
};

/**
 * Validate alert update request
 */
const validateAlertUpdate = (req, res, next) => {
  const errors = [];

  if (req.body.status) {
    const validStatuses = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'];
    if (!validStatuses.includes(req.body.status)) {
      errors.push('Status must be ACTIVE, ACKNOWLEDGED, or RESOLVED');
    }
  }

  if (req.body.priority) {
    const validPriorities = ['LOW', 'MEDIUM', 'HIGH'];
    if (!validPriorities.includes(req.body.priority)) {
      errors.push('Priority must be LOW, MEDIUM, or HIGH');
    }
  }

  if (errors.length > 0) {
    return next(new AppError(errors.join('; '), 400));
  }

  if (req.body.message) req.body.message = req.body.message.trim();
  next();
};

module.exports = {
  validateItem,
  validateItemUpdate,
  validateTransaction,
  validateAlert,
  validateAlertUpdate,
};
