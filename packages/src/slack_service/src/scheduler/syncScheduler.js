// src/scheduler/syncScheduler.js

const cron = require("node-cron");
const { syncPostgresToChroma } = require("../knowledgeBase/slack.knowledgeBase");

/**
 * Start the background sync scheduler
 * Runs every 5 minutes to keep ChromaDB in sync with PostgreSQL
 */
const startScheduler = () => {
  console.log("🕐 Starting sync scheduler...");

  // Schedule the sync job
  cron.schedule("*/5 * * * *", async () => {
    try {
      const timestamp = new Date().toISOString();
      console.log(`\n[Scheduler ${timestamp}] Running ChromaDB sync...`);
      
      const result = await syncPostgresToChroma();
      
      console.log(`[Scheduler ${timestamp}] ✅ Sync completed: ${result.synced} messages\n`);
    } catch (error) {
      console.error(`[Scheduler] ❌ Sync failed:`, error.message);
      // Don't crash the server if sync fails
      // Just log and continue
    }
  });

  console.log("✅ Scheduler started: Syncing every 5 minutes");
  console.log("   Next sync will run in ~5 minutes");
};

/**
 * Run an immediate sync (useful for testing)
 * You can call this manually from server.js during development
 */
const runImmediateSync = async () => {
  console.log("🔄 Running immediate sync...");
  try {
    const result = await syncPostgresToChroma();
    console.log(`✅ Immediate sync completed: ${result.synced} messages`);
    return result;
  } catch (error) {
    console.error("❌ Immediate sync failed:", error);
    throw error;
  }
};

module.exports = {
  startScheduler,
  runImmediateSync
};