const db = require('../config/database');
const config = require('../config/config');

/**
 * Get inventory overview statistics
 */
const getOverview = async () => {
  const result = await db.query(`
    SELECT 
      COUNT(*) as total_items,
      COALESCE(SUM(quantity), 0) as total_stock,
      COUNT(CASE WHEN quantity <= $1 THEN 1 END) as low_stock_items,
      COUNT(CASE WHEN quantity <= $2 THEN 1 END) as critical_stock_items,
      COUNT(CASE WHEN quantity = 0 THEN 1 END) as out_of_stock_items,
      COUNT(DISTINCT category) as total_categories
    FROM inventory_items
    WHERE deleted_at IS NULL
  `, [config.alerts.lowStockThreshold, config.alerts.criticalStockThreshold]);

  return result.rows[0];
};

/**
 * Get stock level distribution
 */
const getStockLevels = async () => {
  const result = await db.query(`
    SELECT 
      CASE 
        WHEN quantity = 0 THEN 'out_of_stock'
        WHEN quantity <= $1 THEN 'critical'
        WHEN quantity <= $2 THEN 'low'
        WHEN quantity <= 50 THEN 'medium'
        ELSE 'healthy'
      END as level,
      COUNT(*) as count
    FROM inventory_items
    WHERE deleted_at IS NULL
    GROUP BY 
      CASE 
        WHEN quantity = 0 THEN 'out_of_stock'
        WHEN quantity <= $1 THEN 'critical'
        WHEN quantity <= $2 THEN 'low'
        WHEN quantity <= 50 THEN 'medium'
        ELSE 'healthy'
      END
  `, [config.alerts.criticalStockThreshold, config.alerts.lowStockThreshold]);

  return result.rows;
};

/**
 * Get stock movement trends over time
 */
const getStockMovement = async ({ startDate, endDate, interval }) => {
  let dateFormat;
  switch (interval) {
    case 'week':
      dateFormat = 'YYYY-WW';
      break;
    case 'month':
      dateFormat = 'YYYY-MM';
      break;
    default:
      dateFormat = 'YYYY-MM-DD';
  }

  let query = `
    SELECT 
      TO_CHAR(created_at, $1) as period,
      type,
      COUNT(*) as transaction_count,
      SUM(quantity) as total_quantity
    FROM inventory_transactions
    WHERE 1=1
  `;

  const params = [dateFormat];
  let paramIndex = 2;

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

  query += `
    GROUP BY TO_CHAR(created_at, $1), type
    ORDER BY period DESC
  `;

  const result = await db.query(query, params);
  return result.rows;
};

/**
 * Get top items by transaction volume
 */
const getTopItems = async ({ limit, period }) => {
  let dateFilter = '';
  const params = [limit];

  if (period) {
    const days = parseInt(period.replace('d', ''), 10) || 30;
    dateFilter = `AND t.created_at >= NOW() - INTERVAL '${days} days'`;
  }

  const result = await db.query(`
    SELECT 
      i.id,
      i.name,
      i.sku,
      i.category,
      COUNT(t.id) as transaction_count,
      SUM(CASE WHEN t.type = 'IN' THEN t.quantity ELSE 0 END) as total_in,
      SUM(CASE WHEN t.type = 'OUT' THEN t.quantity ELSE 0 END) as total_out
    FROM inventory_items i
    LEFT JOIN inventory_transactions t ON i.id = t.item_id ${dateFilter}
    WHERE i.deleted_at IS NULL
    GROUP BY i.id, i.name, i.sku, i.category
    ORDER BY transaction_count DESC
    LIMIT $1
  `, params);

  return result.rows;
};

/**
 * Get items with low stock
 */
const getLowStockItems = async ({ threshold, page, limit }) => {
  const stockThreshold = threshold || config.alerts.lowStockThreshold;
  const offset = (page - 1) * limit;

  const result = await db.query(`
    SELECT 
      id, name, sku, category, quantity, min_quantity, unit_price
    FROM inventory_items
    WHERE quantity <= $1 AND deleted_at IS NULL
    ORDER BY quantity ASC
    LIMIT $2 OFFSET $3
  `, [stockThreshold, limit, offset]);

  const countResult = await db.query(`
    SELECT COUNT(*) as total
    FROM inventory_items
    WHERE quantity <= $1 AND deleted_at IS NULL
  `, [stockThreshold]);

  return {
    items: result.rows,
    total: parseInt(countResult.rows[0].total, 10),
  };
};

/**
 * Get total inventory value
 */
const getInventoryValue = async ({ groupBy }) => {
  let query;
  
  if (groupBy === 'category') {
    query = `
      SELECT 
        category,
        SUM(quantity * unit_price) as total_value,
        COUNT(*) as item_count,
        SUM(quantity) as total_quantity
      FROM inventory_items
      WHERE deleted_at IS NULL
      GROUP BY category
      ORDER BY total_value DESC
    `;
  } else {
    query = `
      SELECT 
        SUM(quantity * unit_price) as total_value,
        COUNT(*) as item_count,
        SUM(quantity) as total_quantity
      FROM inventory_items
      WHERE deleted_at IS NULL
    `;
  }

  const result = await db.query(query);
  return groupBy === 'category' ? result.rows : result.rows[0];
};

/**
 * Get category breakdown
 */
const getCategoryBreakdown = async () => {
  const result = await db.query(`
    SELECT 
      category,
      COUNT(*) as item_count,
      SUM(quantity) as total_quantity,
      AVG(quantity) as avg_quantity,
      SUM(quantity * unit_price) as total_value
    FROM inventory_items
    WHERE deleted_at IS NULL
    GROUP BY category
    ORDER BY item_count DESC
  `);

  return result.rows;
};

module.exports = {
  getOverview,
  getStockLevels,
  getStockMovement,
  getTopItems,
  getLowStockItems,
  getInventoryValue,
  getCategoryBreakdown,
};
