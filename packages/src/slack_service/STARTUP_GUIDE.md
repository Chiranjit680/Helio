# Slack Service - Complete Setup & Resolution Guide

## ✅ ISSUES RESOLVED

All critical code issues have been fixed:

1. ✅ **Module Import Fixed**: Changed `chromadb-default-embed` → `chromadb`
2. ✅ **ChromaDB API Updated**: Now connects to ChromaDB server instead of embedded mode
3. ✅ **Duplicate Imports Removed**: Cleaned up controller imports
4. ✅ **Function Calls Fixed**: `searchKB` → `searchMessages`
5. ✅ **Environment Variables Added**: Added `CHROMADB_URL` to `.env`

---

## 🚀 COMPLETE STARTUP PROCEDURE

### **Step 1: Start ChromaDB Server**

ChromaDB v3.4.0 requires a server. Start it with Docker:

```bash
# Navigate to slack_service directory
cd c:\Users\apurv\Desktop\Coding\Helio\packages\src\slack_service

# Start ChromaDB server
docker-compose -f docker-compose.chromadb.yml up -d

# Verify it's running
curl http://localhost:8000/api/v1/heartbeat
```

**Expected output:** `{"nanosecond heartbeat":...}`

---

### **Step 2: Verify PostgreSQL Database**

```bash
# Test database connection
psql postgresql://postgres:helio_pass@localhost:5432/helio_slack -c "SELECT 1"
```

**If database doesn't exist:**
```bash
psql -U postgres -c "CREATE DATABASE helio_slack"
```

---

### **Step 3: Install Dependencies**

```bash
# Make sure all packages are installed
npm install
```

---

### **Step 4: Start Slack Service**

```bash
npm run dev
```

**Expected startup sequence:**
```
...Starting Slack Service...

[1/4] Initializing PostgreSQL... ✅
[2/4] Loading embedding model (this may take ~10 seconds first time)... ✅
[3/4] Initializing ChromaDB... ✅
[4/4] Starting background scheduler... ✅

✅ All systems initialized successfully!

🎉 Slack Service is READY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Server: http://localhost:8002
 Health: http://localhost:8002/api/slack/health
 Stats:  http://localhost:8002/api/slack/stats
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 TROUBLESHOOTING

### **Error: Cannot connect to Postgres**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If not running, start it
# Windows: Open Services → Start PostgreSQL
# Linux/Mac: sudo systemctl start postgresql
```

### **Error: ChromaDB connection failed**
```bash
# Check if ChromaDB is running
docker ps | grep chromadb

# If not running
docker-compose -f docker-compose.chromadb.yml up -d

# Check logs
docker-compose -f docker-compose.chromadb.yml logs
```

### **Error: Module not found**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

---

## 📊 VERIFY EVERYTHING WORKS

### **Test 1: Health Check**
```bash
curl http://localhost:8002/api/slack/health
```
Expected: `{"status":"ok"}`

### **Test 2: System Stats**
```bash
curl http://localhost:8002/api/slack/stats
```
Expected: JSON with postgres and chromadb statistics

### **Test 3: Semantic Search**
```bash
curl "http://localhost:8002/api/slack/search?query=test&limit=5"
```
Expected: Search results (may be empty if no messages yet)

---

## 🐳 SERVICES OVERVIEW

### **Service Ports:**
- **Slack Service**: http://localhost:8002
- **ChromaDB**: http://localhost:8000
- **PostgreSQL**: localhost:5432

### **Stop Services:**
```bash
# Stop Slack service: Ctrl+C in terminal

# Stop ChromaDB
docker-compose -f docker-compose.chromadb.yml down

# Stop PostgreSQL
# Windows: Services → Stop PostgreSQL
# Linux/Mac: sudo systemctl stop postgresql
```

---

## 🎯 QUICK START COMMANDS

```bash
# 1. Start ChromaDB
docker-compose -f docker-compose.chromadb.yml up -d

# 2. Start Slack Service
npm run dev

# 3. Test it works
curl http://localhost:8002/api/slack/health
```

---

## ⚠️ IMPORTANT NOTES

1. **ChromaDB must be running BEFORE starting Slack service**
2. **PostgreSQL must be running and database must exist**
3. **First startup will download embedding model (~50MB) - takes ~10 seconds**
4. **Data is persisted in `./chroma_data/` directory**
5. **Background sync runs every 5 minutes automatically**

---

## 🔍 WHAT WAS WRONG

### **Primary Issue:**
```javascript
// WRONG (line 3 in slack.knowledgeBase.js)
const chromadb = require("chromadb-default-embed");

// FIXED
const { ChromaClient } = require("chromadb");
```

### **Secondary Issue:**
ChromaDB v3.4.0 is a **client library**, not an embedded database. It requires:
- A ChromaDB server running (provided via Docker Compose)
- Correct connection URL (http://localhost:8000)

### **Other Issues Fixed:**
- Removed duplicate imports
- Fixed function name mismatches
- Added proper environment variables

---

## ✨ ARCHITECTURE

```
┌─────────────────────────────────────┐
│      Slack Service (Port 8002)      │
│  ┌──────────┐         ┌──────────┐  │
│  │  Express │◄───────►│  Routes  │  │
│  └─────┬────┘         └─────┬────┘  │
│        │                    │        │
│        ▼                    ▼        │
│  ┌──────────┐         ┌──────────┐  │
│  │Controller│         │ Services │  │
│  └─────┬────┘         └──────────┘  │
│        │                             │
│        ▼                             │
│  ┌──────────────────────────────┐   │
│  │   Knowledge Base Module      │   │
│  │  - Embeddings (MiniLM-L6-v2) │   │
│  │  - Sync Logic                │   │
│  └────┬──────────────────────┬──┘   │
│       │                      │      │
└───────┼──────────────────────┼──────┘
        │                      │
        ▼                      ▼
┌──────────────┐      ┌──────────────┐
│  PostgreSQL  │      │   ChromaDB   │
│  (Port 5432) │      │  (Port 8000) │
│              │      │              │
│ Raw Messages │      │Vector Search │
│ Sync Status  │      │  Embeddings  │
└──────────────┘      └──────────────┘
```

**Data Flow:**
1. Slack messages → PostgreSQL (raw storage)
2. Background scheduler (every 5 min) → syncs unsynced messages
3. For each message: Generate embedding → Store in ChromaDB
4. Semantic search: Query → Embedding → ChromaDB vector search → Results

---

## 🏁 YOU'RE ALL SET!

Run the Quick Start commands and your Slack service should be running perfectly! 🎉
