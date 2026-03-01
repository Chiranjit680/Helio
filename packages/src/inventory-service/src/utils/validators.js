/**
 * Validate item data
 * @param {Object} data - Item data to validate
 * @returns {Object} Validation result with isValid and errors
 */
const validateItemData = (data) => {
  const errors = [];

  if (!data.sku || typeof data.sku !== 'string' || data.sku.trim().length === 0) {
    errors.push('SKU is required');
  }

  if (!data.name || typeof data.name !== 'string' || data.name.trim().length === 0) {
    errors.push('Name is required');
  }

  if (!data.category || typeof data.category !== 'string') {
    errors.push('Category is required');
  }

  if (data.quantity !== undefined && (typeof data.quantity !== 'number' || data.quantity < 0)) {
    errors.push('Quantity must be a non-negative number');
  }

  if (data.unit_price !== undefined && (typeof data.unit_price !== 'number' || data.unit_price < 0)) {
    errors.push('Unit price must be a non-negative number');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate transaction data
 * @param {Object} data - Transaction data to validate
 * @returns {Object} Validation result
 */
const validateTransactionData = (data) => {
  const errors = [];
  const validTypes = ['IN', 'OUT', 'ADJUSTMENT'];

  if (!data.item_id) {
    errors.push('Item ID is required');
  }

  if (!data.type || !validTypes.includes(data.type)) {
    errors.push('Valid transaction type is required (IN, OUT, ADJUSTMENT)');
  }

  if (data.quantity === undefined || typeof data.quantity !== 'number' || data.quantity <= 0) {
    errors.push('Quantity must be a positive number');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate alert data
 * @param {Object} data - Alert data to validate
 * @returns {Object} Validation result
 */
const validateAlertData = (data) => {
  const errors = [];
  const validTypes = ['LOW_STOCK', 'CRITICAL_STOCK', 'OUT_OF_STOCK', 'EXPIRING', 'CUSTOM'];
  const validPriorities = ['LOW', 'MEDIUM', 'HIGH'];

  if (!data.type || !validTypes.includes(data.type)) {
    errors.push('Valid alert type is required');
  }

  if (!data.message || typeof data.message !== 'string') {
    errors.push('Message is required');
  }

  if (data.priority && !validPriorities.includes(data.priority)) {
    errors.push('Priority must be LOW, MEDIUM, or HIGH');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate UUID format
 * @param {string} id - UUID to validate
 * @returns {boolean}
 */
const isValidUUID = (id) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
};

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Sanitize string input
 * @param {string} input - String to sanitize
 * @returns {string}
 */
const sanitizeString = (input) => {
  if (typeof input !== 'string') return '';
  return input.trim().replace(/[<>]/g, '');
};

/**
 * Validate pagination parameters
 * @param {Object} params - Pagination parameters
 * @returns {Object} Validated pagination
 */
const validatePagination = (params) => {
  const page = Math.max(1, parseInt(params.page, 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(params.limit, 10) || 20));
  
  return { page, limit, offset: (page - 1) * limit };
};

module.exports = {
  validateItemData,
  validateTransactionData,
  validateAlertData,
  isValidUUID,
  isValidEmail,
  sanitizeString,
  validatePagination,
};
