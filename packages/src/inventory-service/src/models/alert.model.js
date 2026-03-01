const db = require('../config/database');

const AlertModel = {
  /**
   * Find all alerts with pagination and filtering
   */
  async findAll({ limit, offset, status, priority, sortBy, order }) {
    let query = `
      SELECT a.id, a.item_id, a.type, a.priority, a.message, a.status,
             a.threshold, a.current_quantity, a.created_at, a.acknowledged_at, a.acknowledged_by,
             i.name as item_name, i.sku as item_sku
      FROM inventory_alerts a
      LEFT JOIN inventory_items i ON a.item_id = i.id
      WHERE 1=1
    `;
    const params = [];
    let paramIndex = 1;

    if (status) {
      query += ` AND a.status = $${paramIndex}`;
      params.push(status);
      paramIndex++;
    }

    if (priority) {
      query += ` AND a.priority = $${paramIndex}`;
      params.push(priority);
      paramIndex++;
    }

    const validSortColumns = ['created_at', 'priority', 'type'];
    const sortColumn = validSortColumns.includes(sortBy) ? `a.${sortBy}` : 'a.created_at';
    const sortOrder = order.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';

    query += ` ORDER BY ${sortColumn} ${sortOrder}`;
    query += ` LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);

    const result = await db.query(query, params);
    return result.rows;
  },

  /**
   * Count alerts with filtering
   */
  async count({ status, priority }) {
    let query = 'SELECT COUNT(*) as total FROM inventory_alerts WHERE 1=1';
    const params = [];
    let paramIndex = 1;

    if (status) {
      query += ` AND status = $${paramIndex}`;
      params.push(status);
      paramIndex++;
    }

    if (priority) {
      query += ` AND priority = $${paramIndex}`;
      params.push(priority);
      paramIndex++;
    }

    const result = await db.query(query, params);
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Find alert by ID
   */
  async findById(id) {
    const result = await db.query(
      `SELECT a.*, i.name as item_name, i.sku as item_sku
       FROM inventory_alerts a
       LEFT JOIN inventory_items i ON a.item_id = i.id
       WHERE a.id = $1`,
      [id]
    );
    return result.rows[0] || null;
  },

  /**
   * Create a new alert
   */
  async create(alertData) {
    const { item_id, type, priority, message, threshold, current_quantity, created_by } = alertData;
    
    const result = await db.query(
      `INSERT INTO inventory_alerts (item_id, type, priority, message, status, threshold, current_quantity, created_by)
       VALUES ($1, $2, $3, $4, 'ACTIVE', $5, $6, $7)
       RETURNING id, item_id, type, priority, message, status, threshold, current_quantity, created_at`,
      [item_id, type, priority || 'MEDIUM', message, threshold, current_quantity, created_by]
    );
    return result.rows[0];
  },

  /**
   * Update an alert
   */
  async update(id, updateData) {
    const fields = [];
    const values = [];
    let paramIndex = 1;

    const allowedFields = ['status', 'priority', 'message', 'acknowledged_by', 'acknowledged_at', 'updated_by'];
    
    for (const [key, value] of Object.entries(updateData)) {
      if (allowedFields.includes(key) && value !== undefined) {
        fields.push(`${key} = $${paramIndex}`);
        values.push(value);
        paramIndex++;
      }
    }

    if (fields.length === 0) return null;

    fields.push(`updated_at = NOW()`);
    values.push(id);

    const result = await db.query(
      `UPDATE inventory_alerts SET ${fields.join(', ')} WHERE id = $${paramIndex}
       RETURNING id, item_id, type, priority, message, status, acknowledged_at, updated_at`,
      values
    );
    return result.rows[0] || null;
  },

  /**
   * Delete an alert
   */
  async delete(id) {
    const result = await db.query(
      'DELETE FROM inventory_alerts WHERE id = $1 RETURNING id',
      [id]
    );
    return result.rowCount > 0;
  },

  /**
   * Find active alerts
   */
  async findActive({ limit, offset }) {
    const result = await db.query(
      `SELECT a.*, i.name as item_name, i.sku as item_sku
       FROM inventory_alerts a
       LEFT JOIN inventory_items i ON a.item_id = i.id
       WHERE a.status = 'ACTIVE'
       ORDER BY 
         CASE a.priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
         a.created_at DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );
    return result.rows;
  },

  /**
   * Count active alerts
   */
  async countActive() {
    const result = await db.query(
      "SELECT COUNT(*) as total FROM inventory_alerts WHERE status = 'ACTIVE'"
    );
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Find active alert by item ID
   */
  async findActiveByItemId(itemId) {
    const result = await db.query(
      "SELECT * FROM inventory_alerts WHERE item_id = $1 AND status = 'ACTIVE' ORDER BY created_at DESC LIMIT 1",
      [itemId]
    );
    return result.rows[0] || null;
  },

  /**
   * Get alert statistics
   */
  async getStats() {
    const result = await db.query(`
      SELECT 
        status,
        priority,
        COUNT(*) as count
      FROM inventory_alerts
      GROUP BY status, priority
    `);
    return result.rows;
  },
};

module.exports = AlertModel;
