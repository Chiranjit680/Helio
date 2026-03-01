require('dotenv').config();

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

const config = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT, 10) || 5432,
  database: process.env.DB_NAME || 'inventory_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
};

const pool = new Pool(config);

/**
 * Rollback definitions - maps migration files to their rollback SQL
 */
const rollbacks = {
  '003_create_alerts.sql': `
    DROP TRIGGER IF EXISTS update_inventory_alerts_updated_at ON inventory_alerts;
    DROP TABLE IF EXISTS inventory_alerts CASCADE;
  `,
  '002_create_transactions.sql': `
    DROP TABLE IF EXISTS inventory_transactions CASCADE;
  `,
  '001_create_inventory_items.sql': `
    DROP TRIGGER IF EXISTS update_inventory_items_updated_at ON inventory_items;
    DROP FUNCTION IF EXISTS update_updated_at_column();
    DROP TABLE IF EXISTS inventory_items CASCADE;
    DROP EXTENSION IF EXISTS "uuid-ossp";
  `,
};

/**
 * Get the last applied migration
 */
async function getLastMigration() {
  try {
    const result = await pool.query(
      'SELECT filename FROM schema_migrations ORDER BY applied_at DESC LIMIT 1'
    );
    return result.rows[0]?.filename || null;
  } catch (error) {
    // Table doesn't exist
    if (error.code === '42P01') {
      return null;
    }
    throw error;
  }
}

/**
 * Rollback a single migration
 */
async function rollbackMigration(filename) {
  const rollbackSql = rollbacks[filename];
  
  if (!rollbackSql) {
    throw new Error(`No rollback defined for migration: ${filename}`);
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    
    // Execute the rollback SQL
    await client.query(rollbackSql);
    
    // Remove migration record
    await client.query(
      'DELETE FROM schema_migrations WHERE filename = $1',
      [filename]
    );
    
    await client.query('COMMIT');
    console.log(`✓ Rolled back: ${filename}`);
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Rollback the last migration (or all if --all flag is passed)
 */
async function rollback() {
  const rollbackAll = process.argv.includes('--all');
  
  console.log('\n🔄 Starting database rollback...\n');
  console.log(`Database: ${config.database}@${config.host}:${config.port}\n`);

  try {
    if (rollbackAll) {
      console.log('Rolling back ALL migrations...\n');
      
      // Get all applied migrations in reverse order
      const result = await pool.query(
        'SELECT filename FROM schema_migrations ORDER BY applied_at DESC'
      );
      
      if (result.rows.length === 0) {
        console.log('No migrations to rollback.\n');
        return;
      }

      for (const row of result.rows) {
        await rollbackMigration(row.filename);
      }
      
      console.log('\n✓ All migrations rolled back!\n');
    } else {
      // Rollback only the last migration
      const lastMigration = await getLastMigration();
      
      if (!lastMigration) {
        console.log('No migrations to rollback.\n');
        return;
      }

      console.log(`Rolling back last migration: ${lastMigration}\n`);
      await rollbackMigration(lastMigration);
      console.log('\n✓ Rollback complete!\n');
    }
  } catch (error) {
    console.error('\n✗ Rollback failed:', error.message);
    console.error('\nStack trace:', error.stack);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

// Show usage if --help flag
if (process.argv.includes('--help')) {
  console.log(`
Usage: npm run migrate:rollback [options]

Options:
  --all     Rollback all migrations
  --help    Show this help message

Examples:
  npm run migrate:rollback        # Rollback last migration only
  npm run migrate:rollback --all  # Rollback all migrations
`);
  process.exit(0);
}

// Run rollback
rollback();
