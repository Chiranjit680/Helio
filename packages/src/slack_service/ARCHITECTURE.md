# SLACK SERVICE ARCHITECTURE - pgvector Implementation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SLACK WORKSPACE                             │
│                  (Messages, Channels, Users)                        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Events API
                           │ (Webhook)
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      SLACK SERVICE (Node.js)                        │
│                      Port: 8002                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  API LAYER (Express.js)                                      │   │
│  │  • 9 REST endpoints                                          │   │
│  │  • CORS enabled                                              │   │
│  │  • Request signature verification                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  CONTROLLERS                                                 │   │
│  │  • handleEvent (webhook)                                     │   │
│  │  • semanticSearch                                            │   │
│  │  • broadcastMessage                                          │   │
│  │  • adminBootstrapChannels                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  SERVICES                                                    │   │
│  │  • slack.service (event processing)                          │   │
│  │  • broadcastServices (smart routing)                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  KNOWLEDGE BASE                                              │   │
│  │  • embeddings.js (MiniLM-L6-v2)                              │   │
│  │  • slack.knowledgeBase.js (vector search)                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MODELS                                                      │   │
│  │  • slackMessage.model (data access)                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                           ↓                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            │ pg client
                            │ pgvector
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL + pgvector                            │
│  • slack_messages (384D embeddings, HNSW index)                     │
│  • slack_channels (384D embeddings, HNSW index)                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Message Ingestion Pipeline

```
┌──────────────┐
│ Slack Message│
│ Posted       │
└──────┬───────┘
       │
       ↓ Webhook
┌──────────────────────┐
│ POST /api/slack/     │
│ events               │
└──────┬───────────────┘
       │
       ↓ Verify Signature
┌──────────────────────┐
│ verifySlackSignature │
│ middleware           │
└──────┬───────────────┘
       │
       ↓ Process Event
┌──────────────────────┐
│ slack.service.       │
│ processEvent()       │
└──────┬───────────────┘
       │
       ├─────────────────────────┐
       │                         │
       ↓ Resolve Names           ↓ Generate Context
┌──────────────────────┐    ┌────────────────────┐
│ slack.connector      │    │ "Channel: X |      │
│ • resolveChannelName │    │  User: Y |         │
│ • resolveUsername    │    │  Message"          │
└──────┬───────────────┘    └────────┬───────────┘
       │                             │
       └─────────────────┬───────────┘
                         │
                         ↓ Generate Embedding
                   ┌─────────────────────┐
                   │ embeddings.js       │
                   │ MiniLM-L6-v2        │
                   │ → 384D vector       │
                   └──────┬──────────────┘
                          │
                          ↓ Save to DB
                   ┌─────────────────────┐
                   │ slackMessage.model  │
                   │ .save()             │
                   └──────┬──────────────┘
                          │
                          ↓ toSql(embedding)
                   ┌─────────────────────┐
                   │ PostgreSQL          │
                   │ INSERT with vector  │
                   │ (HNSW indexed)      │
                   └─────────────────────┘
```

---

### 2. Semantic Search Flow

```
┌──────────────────────────┐
│ User Query               │
│ "deployment issues"      │
└────────┬─────────────────┘
         │
         ↓ GET /api/slack/search
┌─────────────────────────────┐
│ slack.controller            │
│ .semanticSearch()           │
└────────┬────────────────────┘
         │
         ↓ Generate Query Embedding
┌─────────────────────────────┐
│ slack.knowledgeBase         │
│ .searchMessages()           │
│   └→ generateEmbedding()    │
└────────┬────────────────────┘
         │
         ↓ 384D Query Vector
┌─────────────────────────────┐
│ PostgreSQL + pgvector       │
│ SELECT ... ORDER BY         │
│ embedding <=> $1::vector    │
│ (Cosine Distance)           │
└────────┬────────────────────┘
         │
         ↓ HNSW Index Search
┌─────────────────────────────┐
│ Fast Approximate Search     │
│ • m=16 (connections)        │
│ • ef=64 (search quality)    │
│ • Returns top-K neighbors   │
└────────┬────────────────────┘
         │
         ↓ Filter by Similarity
┌─────────────────────────────┐
│ 1 - distance >= 0.35        │
│ (Convert distance to        │
│  similarity score)          │
└────────┬────────────────────┘
         │
         ↓ Return Results
┌─────────────────────────────┐
│ JSON Response               │
│ {                           │
│   query: "...",             │
│   count: 5,                 │
│   results: [...]            │
│ }                           │
└─────────────────────────────┘
```

---

### 3. Smart Broadcast Flow

```
┌──────────────────────────┐
│ Admin Intent             │
│ "infrastructure updates" │
└────────┬─────────────────┘
         │
         ↓ POST /api/slack/broadcast
┌─────────────────────────────┐
│ slack.controller            │
│ .broadcastMessage()         │
│ (Accepts message/messageBody)│
└────────┬────────────────────┘
         │
         ↓ Generate Intent Embedding
┌─────────────────────────────┐
│ broadcastServices           │
│ .smartBroadcast()           │
│   └→ generateEmbedding()    │
│   Uses: actualMessage       │
└────────┬────────────────────┘
         │
         ↓ 384D Intent Vector
┌─────────────────────────────┐
│ PostgreSQL                  │
│ SELECT from slack_channels  │
│ ORDER BY                    │
│ embedding <=> $1::vector    │
└────────┬────────────────────┘
         │
         ↓ Top-K Channels (e.g., 5)
┌────────────────────────────┐
│ Ranked by Similarity       │
│ • #devops (0.78)           │
│ • #engineering (0.72)      │
│ • #infrastructure (0.65)   │
│ • #tech (0.52)             │
│ • #general (0.41)          │
└────────┬───────────────────┘
         │
         ↓ Filter by Threshold (0.45)
┌────────────────────────────┐
│ Keep channels with         │
│ similarity >= 0.45         │
│ • #devops ✓                │
│ • #engineering ✓           │
│ • #infrastructure ✓        │
│ • #tech ✓                  │
│ • #general ✗ (skipped)     │
└────────┬───────────────────┘
         │
         ↓ Post Messages
┌─────────────────────────────┐
│ Slack Web API               │
│ chat.postMessage()          │
│ • With relevance footer     │
│ • Track success/failure     │
└────────┬────────────────────┘
         │
         ↓ Return Results
┌─────────────────────────────┐
│ {                           │
│   sent_to: [4 channels],    │
│   failed: [],               │
│   skipped: [1 channel],     │
│   total_sent: 4             │
│ }                           │
└─────────────────────────────┘
```

---

## Component Interactions

### Database Schema

```
┌────────────────────────────────────────────────┐
│              slack_messages                    │
├────────────────────────────────────────────────┤
│ id                  SERIAL PRIMARY KEY         │
│ message_ts          TEXT UNIQUE NOT NULL       │
│ channel_id          TEXT NOT NULL              │
│ channel_name        TEXT                       │
│ user_id             TEXT                       │
│ username            TEXT                       │
│ text                TEXT NOT NULL              │
│ embedding           vector(384)                │
│ created_at          TIMESTAMP                  │
│ importance_score    INTEGER                    │
│ category            TEXT                       │
├────────────────────────────────────────────────┤
│ INDEXES:                                       │
│ • idx_messages_embedding (HNSW, cosine)        │
│ • idx_channel_id (B-tree)                      │
│ • idx_user_id (B-tree)                         │
│ • idx_created_at (B-tree DESC)                 │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              slack_channels                    │
├────────────────────────────────────────────────┤
│ id                  SERIAL PRIMARY KEY         │
│ channel_id          TEXT UNIQUE NOT NULL       │
│ channel_name        TEXT NOT NULL              │
│ topic               TEXT                       │
│ purpose             TEXT                       │
│ is_private          BOOLEAN                    │
│ embedding           vector(384)                │
│ updated_at          TIMESTAMP                  │
├────────────────────────────────────────────────┤
│ INDEXES:                                       │
│ • idx_channels_embedding (HNSW, cosine)        │
└────────────────────────────────────────────────┘
```

---

## Technology Layers

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                         │
│  • REST API (Express.js)                                    │
│  • JSON request/response                                    │
│  • CORS, body parsing                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SECURITY LAYER                                             │
│  • Slack signature verification (HMAC SHA256)               │
│  • Timing-safe comparison                                   │
│  • 5-minute replay window                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER                                       │
│  • Event processing                                         │
│  • Message enrichment                                       │
│  • Smart broadcasting                                       │
│  • Channel indexing                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  EMBEDDING LAYER                                            │
│  • MiniLM-L6-v2 Transformer                                 │
│  • Mean pooling + normalization                             │
│  • 384-dimensional vectors                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DATA ACCESS LAYER                                          │
│  • pg client (PostgreSQL driver)                            │
│  • pgvector adapter                                         │
│  • Parameterized queries                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PERSISTENCE LAYER                                          │
│  • PostgreSQL 12+                                           │
│  • pgvector extension                                       │
│  • HNSW vector indexes                                      │
│  • B-tree metadata indexes                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

### HNSW Index Configuration

```
Parameter          Value    Purpose
─────────────────────────────────────────────────────
m                  16       Connections per layer
                            (higher = better recall,
                             more memory)

ef_construction    64       Build-time search width
                            (higher = better quality,
                             slower build)

Distance Metric    Cosine   Best for normalized
                            embeddings (0-1 range)
```

### Expected Query Times

```
Dataset Size     Search Time    Notes
────────────────────────────────────────────────
1K messages      < 5ms          Almost instant
10K messages     < 10ms         Very fast
100K messages    < 50ms         Fast
1M messages      < 200ms        Acceptable
10M messages     < 500ms        Good (with tuning)
```

---

## Error Handling Strategy

```
┌──────────────────┐
│ API Request      │
└────────┬─────────┘
         │
         ↓ try {
┌─────────────────────────┐
│ Controller Logic        │
└────────┬────────────────┘
 }       │
         ↓ try {
┌─────────────────────────┐
│ Service Logic           │
└────────┬────────────────┘
         │
}        ↓ try {
┌─────────────────────────┐
│ Database Operation      │
└────────┬────────────────┘
         │
         ↓
    } catch (err)
         ↓
┌─────────────────────────┐
│ Log Error               │
│ console.error()         │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│ Return 500 with message │
│ { error: "...",         │
│   details: err.message }│
└─────────────────────────┘
```

---

## Security Model

```
┌─────────────────────────────────────────────┐
│ Slack Event                                 │
└────────┬────────────────────────────────────┘
         │ Headers:
         │ • X-Slack-Request-Timestamp
         │ • X-Slack-Signature
         ↓
┌─────────────────────────────────────────────┐
│ verifySlackSignature Middleware             │
│                                             │
│ 1. Check timestamp (< 5 min old)            │
│ 2. Rebuild signature:                       │
│    HMAC-SHA256(                             │
│      "v0:{timestamp}:{body}",               │
│      SLACK_SIGNING_SECRET                   │
│    )                                        │
│ 3. Compare with timing-safe method          │
└────────┬────────────────────────────────────┘
         │
         ↓ If valid
┌─────────────────────────────────────────────┐
│ Process Event                               │
└─────────────────────────────────────────────┘
         │
         ↓ If invalid
┌─────────────────────────────────────────────┐
│ Return 403 Forbidden                        │
└─────────────────────────────────────────────┘
```

---

**Architecture Document**  
**Version**: 1.0  
**Last Updated**: April 4, 2026  
**Status**: ✅ Implemented and Tested
