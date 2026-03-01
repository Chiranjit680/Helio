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

const MIGRATIONS_DIR = path.join(__dirname, '..', 'migrations');

/*
 * Create migrations tracking table if it doesn't exist
 */
async function createMigrationsTable() {
  const sql = `
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id SERIAL PRIMARY KEY,
      filename VARCHAR(255) NOT NULL UNIQUE,
      applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
  `;
  await pool.query(sql);
  console.log('✓ Migrations table ready');
}

/**
 * Get list of already applied migrations
 */
async function getAppliedMigrations() {
  const result = await pool.query(
    'SELECT filename FROM schema_migrations ORDER BY filename'
  );
  return result.rows.map(row => row.filename);
}

/**
 * Get all migration files from migrations directory
 */
function getMigrationFiles() {
  const files = fs.readdirSync(MIGRATIONS_DIR)
    .filter(file => file.endsWith('.sql'))
    .sort();
  return files;
}

/**
 * Apply a single migration
 */
async function applyMigration(filename) {
  const filePath = path.join(MIGRATIONS_DIR, filename);
  const sql = fs.readFileSync(filePath, 'utf8');

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    
    // Execute the migration SQL
    await client.query(sql);
    
    // Record the migration
    await client.query(
      'INSERT INTO schema_migrations (filename) VALUES ($1)',
      [filename]
    );
    
    await client.query('COMMIT');
    console.log(`✓ Applied: ${filename}`);
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Run all pending migrations
 */
async function migrate() {
  console.log('\n🚀 Starting database migration...\n');
  console.log(`Database: ${config.database}@${config.host}:${config.port}\n`);

  try {
    // Ensure migrations table exists
    await createMigrationsTable();

    // Get applied and pending migrations
    const applied = await getAppliedMigrations();
    const allMigrations = getMigrationFiles();
    const pending = allMigrations.filter(m => !applied.includes(m));

    if (pending.length === 0) {
      console.log('\n✓ Database is up to date. No migrations to apply.\n');
      return;
    }

    console.log(`\nFound ${pending.length} pending migration(s):\n`);

    // Apply each pending migration
    for (const migration of pending) {
      await applyMigration(migration);
    }

    console.log('\n✓ All migrations applied successfully!\n');
  } catch (error) {
    console.error('\n✗ Migration failed:', error.message);
    console.error('\nStack trace:', error.stack);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

// Run migrations
migrate();
