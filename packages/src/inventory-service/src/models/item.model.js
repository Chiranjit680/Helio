const db = require('../config/database');

const ItemModel = {
  /**
   * Find all items with pagination and filtering
   */
  async findAll({ limit, offset, category, sortBy, order }) {
    let query = `
      SELECT id, sku, name, description, category, quantity, min_quantity, 
             unit_price, location, created_at, updated_at
      FROM inventory_items
      WHERE deleted_at IS NULL
    `;
    const params = [];
    let paramIndex = 1;

    if (category) {
      query += ` AND category = $${paramIndex}`;
      params.push(category);
      paramIndex++;
    }

    const validSortColumns = ['name', 'sku', 'quantity', 'unit_price', 'created_at', 'updated_at'];
    const sortColumn = validSortColumns.includes(sortBy) ? sortBy : 'created_at';
    const sortOrder = order.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';

    query += ` ORDER BY ${sortColumn} ${sortOrder}`;
    query += ` LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);

    const result = await db.query(query, params);
    return result.rows;
  },

  /**
   * Count items with optional category filter
   */
  async count({ category }) {
    let query = 'SELECT COUNT(*) as total FROM inventory_items WHERE deleted_at IS NULL';
    const params = [];

    if (category) {
      query += ' AND category = $1';
      params.push(category);
    }

    const result = await db.query(query, params);
    return parseInt(result.rows[0].total, 10);
  },

  /**
   * Find item by ID
   */
  async findById(id) {
    const result = await db.query(
      `SELECT id, sku, name, description, category, quantity, min_quantity,
              unit_price, location, created_at, updated_at, created_by
       FROM inventory_items WHERE id = $1 AND deleted_at IS NULL`,
      [id]
    );
    return result.rows[0] || null;
  },

  /**
   * Find item by SKU
   */
  async findBySku(sku) {
    const result = await db.query(
      'SELECT id, sku, name FROM inventory_items WHERE sku = $1 AND deleted_at IS NULL',
      [sku]
    );
    return result.rows[0] || null;
  },

  /**
   * Create a new item
   */
  async create(itemData) {
    const { sku, name, description, category, quantity, min_quantity, unit_price, location, created_by } = itemData;
    
    const result = await db.query(
      `INSERT INTO inventory_items (sku, name, description, category, quantity, min_quantity, unit_price, location, created_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       RETURNING id, sku, name, description, category, quantity, min_quantity, unit_price, location, created_at`,
      [sku, name, description, category, quantity || 0, min_quantity || 0, unit_price || 0, location, created_by]
    );
    return result.rows[0];
  },

  /**
   * Update an item
   */
  async update(id, updateData) {
    const fields = [];
    const values = [];
    let paramIndex = 1;

    const allowedFields = ['sku', 'name', 'description', 'category', 'min_quantity', 'unit_price', 'location', 'updated_by'];
    
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
      `UPDATE inventory_items SET ${fields.join(', ')} WHERE id = $${paramIndex} AND deleted_at IS NULL
       RETURNING id, sku, name, description, category, quantity, min_quantity, unit_price, location, updated_at`,
      values
    );
    return result.rows[0] || null;
  },

  /**
   * Update item quantity
   */
  async updateQuantity(id, newQuantity, client = null) {
    const queryFn = client ? client.query.bind(client) : db.query;
    const result = await queryFn(
      `UPDATE inventory_items SET quantity = $1, updated_at = NOW() WHERE id = $2 AND deleted_at IS NULL
       RETURNING id, sku, name, quantity`,
      [newQuantity, id]
    );
    return result.rows[0] || null;
  },

  /**
   * Soft delete an item
   */
  async delete(id) {
    const result = await db.query(
      'UPDATE inventory_items SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL RETURNING id',
      [id]
    );
    return result.rowCount > 0;
  },

  /**
   * Search items by name, SKU, or category
   */
  async search(query, { limit, offset }) {
    const searchPattern = `%${query}%`;
    const result = await db.query(
      `SELECT id, sku, name, description, category, quantity, unit_price
       FROM inventory_items
       WHERE deleted_at IS NULL
         AND (name ILIKE $1 OR sku ILIKE $1 OR category ILIKE $1 OR description ILIKE $1)
       ORDER BY name ASC
       LIMIT $2 OFFSET $3`,
      [searchPattern, limit, offset]
    );
    return result.rows;
  },

  /**
   * Count search results
   */
  async searchCount(query) {
    const searchPattern = `%${query}%`;
    const result = await db.query(
      `SELECT COUNT(*) as total FROM inventory_items
       WHERE deleted_at IS NULL
         AND (name ILIKE $1 OR sku ILIKE $1 OR category ILIKE $1 OR description ILIKE $1)`,
      [searchPattern]
    );
    return parseInt(result.rows[0].total, 10);
  },
};

module.exports = ItemModel;
