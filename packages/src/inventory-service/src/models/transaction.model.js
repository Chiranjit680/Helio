const db = require('../config/database');

const TransactionModel = {
  /**
   * Find all transactions with pagination and filtering
   */
  async findAll({ limit, offset, startDate, endDate, type, sortBy, order }) {
    let query = `
      SELECT t.id, t.item_id, t.type, t.quantity, t.previous_quantity, t.new_quantity,
             t.notes, t.created_at, t.created_by,
             i.name as item_name, i.sku as item_sku
      FROM inventory_transactions t
      JOIN inventory_items i ON t.item_id = i.id
      WHERE 1=1
    `;
    const params = [];
    let paramIndex = 1;

    if (type) {
      query += ` AND t.type = $${paramIndex}`;
      params.push(type);
      paramIndex++;
    }

    if (startDate) {
      query += ` AND t.created_at >= $${paramIndex}`;
      params.push(startDate);
      paramIndex++;
    }

    if (endDate) {
      query += ` AND t.created_at <= $${paramIndex}`;
      params.push(endDate);
      paramIndex++;
    }

    const validSortColumns = ['created_at', 'quantity', 'type'];
    const sortColumn = validSortColumns.includes(sortBy) ? `t.${sortBy}` : 't.created_at';
    const sortOrder = order.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';

    query += ` ORDER BY ${sortColumn} ${sortOrder}`;
    query += ` LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);

    const result = await db.query(query, params);
    return result.rows;
  },

  /**
   * Count transactions with filtering
   */
  async count({ startDate, endDate, type }) {
    let query = 'SELECT COUNT(*) as total FROM inventory_transactions WHERE 1=1';
    const params = [];
    let paramIndex = 1;

    if (type) {
      query += ` AND type = $${paramIndex}`;
      params.push(type);
      paramIndex++;
    }

    if (startDate) {
      query += ` AND created_at >= $${paramIndex}`;
      params.push(startDate);
      paramIndex++;
    }

    if (endDate) {
      query += ` AND created_at <= $${paramIndex}`;
      params.push(endDate);
      paramIndex++;
    }

    const result = await db.query(query, params);
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Find transaction by ID
   */
  async findById(id) {
    const result = await db.query(
      `SELECT t.*, i.name as item_name, i.sku as item_sku
       FROM inventory_transactions t
       JOIN inventory_items i ON t.item_id = i.id
       WHERE t.id = $1`,
      [id]
    );
    return result.rows[0] || null;
  },

  /**
   * Create a new transaction
   */
  async create(transactionData, client = null) {
    const { item_id, type, quantity, previous_quantity, new_quantity, notes, created_by } = transactionData;
    
    const queryFn = client ? client.query.bind(client) : db.query;
    const result = await queryFn(
      `INSERT INTO inventory_transactions (item_id, type, quantity, previous_quantity, new_quantity, notes, created_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING id, item_id, type, quantity, previous_quantity, new_quantity, notes, created_at`,
      [item_id, type, quantity, previous_quantity, new_quantity, notes, created_by]
    );
    return result.rows[0];
  },

  /**
   * Find transactions by item ID
   */
  async findByItemId(itemId, { limit, offset }) {
    const result = await db.query(
      `SELECT id, type, quantity, previous_quantity, new_quantity, notes, created_at, created_by
       FROM inventory_transactions
       WHERE item_id = $1
       ORDER BY created_at DESC
       LIMIT $2 OFFSET $3`,
      [itemId, limit, offset]
    );
    return result.rows;
  },

  /**
   * Count transactions for an item
   */
  async countByItemId(itemId) {
    const result = await db.query(
      'SELECT COUNT(*) as total FROM inventory_transactions WHERE item_id = $1',
      [itemId]
    );
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Find transactions by type
   */
  async findByType(type, { limit, offset }) {
    const result = await db.query(
      `SELECT t.*, i.name as item_name, i.sku as item_sku
       FROM inventory_transactions t
       JOIN inventory_items i ON t.item_id = i.id
       WHERE t.type = $1
       ORDER BY t.created_at DESC
       LIMIT $2 OFFSET $3`,
      [type, limit, offset]
    );
    return result.rows;
  },

  /**
   * Count transactions by type
   */
  async countByType(type) {
    const result = await db.query(
      'SELECT COUNT(*) as total FROM inventory_transactions WHERE type = $1',
      [type]
    );
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Get transaction summary for a date range
   */
  async getSummary(startDate, endDate) {
    const result = await db.query(
      `SELECT 
         type,
         COUNT(*) as count,
         SUM(quantity) as total_quantity
       FROM inventory_transactions
       WHERE created_at BETWEEN $1 AND $2
       GROUP BY type`,
      [startDate, endDate]
    );
    return result.rows;
  },
};

module.exports = TransactionModel;
