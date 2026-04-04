# Quick Testing Guide - Slack Service

This guide walks you through testing your Slack service step-by-step. You'll verify that messages sent in Slack are stored in your database and that your service can send messages back to Slack.

---

## PART 1: ONE-TIME SETUP

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name your app (e.g., "Helio Bot")
4. Select your workspace
5. Click **"Create App"**

### Step 2: Configure Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add these scopes:
   - `chat:write` - Send messages
   - `channels:history` - Read public channel messages
   - `groups:history` - Read private channel messages
   - `im:history` - Read DM messages
   - `mpim:history` - Read group DMs

### Step 3: Install App and Get Bot Token

1. Scroll up to **"OAuth Tokens for Your Workspace"** section
2. Click **"Install to Workspace"**
3. Review and authorize the permissions
4. After installation, copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
5. **Save this token** - you'll need it in Step 5

### Step 4: Get Signing Secret

1. In the left sidebar, click **"Basic Information"**
2. Scroll to **"App Credentials"** section
3. Find **"Signing Secret"**
4. Click **"Show"** and copy it
5. **Save this secret** - you'll need it in Step 5

### Step 5: Configure Environment Variables

1. Navigate to your slack_service directory:
   ```bash
   cd c:\Users\apurv\Desktop\Coding\Helio\packages\src\slack_service
   ```

2. Copy `.env.example` to create `.env`:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file and fill in your credentials:
   ```env
   PORT=8002
   SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-FROM-STEP-3
   SLACK_SIGNING_SECRET=YOUR-SECRET-FROM-STEP-4
   DATABASE_URL=postgresql://user:password@localhost:5432/helio_slack
   ```

4. Update `DATABASE_URL` with your PostgreSQL credentials

### Step 6: Start PostgreSQL Database

**Option A - Using existing PostgreSQL:**
- Ensure PostgreSQL is running on port 5432
- Or update the port in `DATABASE_URL`

**Option B - Using Docker:**
```bash
docker run --name helio-slack-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=helio_slack \
  -e POSTGRES_USER=user \
  -p 5432:5432 \
  -d postgres:15
```

### Step 7: Install Dependencies and Start Service

```bash
# Install packages (first time only)
npm install

# Start service in development mode
npm run dev
```

**Expected output:**
```
Database initialized: slack_messages table ready
Slack service running on port 8002
```

**Verify service is healthy:**
```bash
curl http://localhost:8002/api/slack/health
```

**Expected response:** `{"status":"ok"}`

---

## PART 2: CONNECT SLACK TO YOUR SERVICE

### Step 8: Install and Start ngrok

ngrok exposes your local service to the internet so Slack can send events to it.

**Download and install:**
1. Go to https://ngrok.com/download
2. Download for your operating system
3. Extract and install it

**Start ngrok tunnel:**
```bash
ngrok http 8002
```

**You'll see output like:**
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8002
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

**IMPORTANT:** Keep ngrok running! If you restart it, the URL changes and you'll need to update Slack.

### Step 9: Configure Slack Event Subscriptions

1. Go back to https://api.slack.com/apps
2. Click on your app
3. In the left sidebar, click **"Event Subscriptions"**
4. Toggle **"Enable Events"** to **ON**
5. In the **"Request URL"** field, enter:
   ```
   https://YOUR-NGROK-URL/api/slack/events
   ```
   Example: `https://abc123.ngrok.io/api/slack/events`

6. Wait for Slack to verify the URL (you should see a green **"Verified"** checkmark)
7. Scroll down to **"Subscribe to bot events"**
8. Click **"Add Bot User Event"** and add these events:
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`
9. Click **"Save Changes"** at the bottom

---

## PART 3: TEST RECEIVING MESSAGES (Slack → Your Service)

**What you're testing:** When you send a message in Slack, it gets stored in your PostgreSQL database.

### Step 10: Invite Bot to a Channel

1. Open your Slack workspace
2. Go to any channel (or create one like `#helio-test`)
3. Type: `/invite @YourBotName` (replace with your actual bot name)
4. Press Enter

### Step 11: Send a Test Message

In the same channel, type and send:
```
Hello from Slack! Testing Helio service 🚀
```

### Step 12: Check Service Logs

- Look at your terminal where `npm run dev` is running
- You should see console output showing the event was processed

### Step 13: Verify Message in Database (Method 1: API)

**Using curl:**
```bash
curl http://localhost:8002/api/slack/messages
```

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8002/api/slack/messages
```

**Expected response:**
```json
{
  "messages": [
    {
      "id": 1,
      "message_ts": "1234567890.123456",
      "channel_id": "C1234567890",
      "user_id": "U1234567890",
      "text": "Hello from Slack! Testing Helio service 🚀",
      "created_at": "2026-03-19T10:30:00.000Z"
    }
  ]
}
```

**What to verify:**
- ✅ Your message text appears exactly as sent
- ✅ `user_id` shows Slack user ID (format: `U` + numbers/letters)
- ✅ `channel_id` shows channel ID (format: `C` + numbers/letters)
- ✅ `message_ts` shows Slack timestamp
- ✅ `created_at` shows when it was stored in your database

### Step 14: Verify Message in Database (Method 2: Direct SQL)

**Connect to PostgreSQL:**
```bash
# If using local PostgreSQL
psql postgresql://user:password@localhost:5432/helio_slack

# If using Docker
docker exec -it helio-slack-db psql -U user -d helio_slack
```

**Query messages:**
```sql
SELECT * FROM slack_messages ORDER BY created_at DESC LIMIT 5;
```

You should see the same data as the API response.

### Step 15: Identify Sender Name

The service stores `user_id` (e.g., `U1234567890`), not the display name. To find out who sent it:

**Method 1 - In Slack UI:**
1. Right-click on the message sender's name/avatar
2. Click **"View profile"**
3. The User ID will be shown at the bottom

**Method 2 - Check your own User ID:**
1. In Slack, click your profile picture (top right)
2. Click **"Profile"**
3. Click **"..."** → **"Copy member ID"**
4. Compare with `user_id` in database

**Note:** The service currently doesn't fetch user display names. It only stores the `user_id`. To get names, you'd need to call the Slack Users API (out of scope for this test).

---

## PART 4: TEST SENDING MESSAGES (Your Service → Slack)

**What you're testing:** Your service can send messages to Slack channels.

### Step 16: Get Channel ID

**Method 1 - From Slack UI:**
1. Right-click on the channel name in sidebar
2. Click **"View channel details"**
3. Scroll down to find the **Channel ID** at the bottom
4. Copy it (format: `C1234567890`)

**Method 2 - Use channel name:**
- You can also use the channel name like `#helio-test`

### Step 17: Send Message via Your Service

**Using curl:**
```bash
curl -X POST http://localhost:8002/api/slack/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"C1234567890","text":"Hello from Helio service! 🤖"}'
```

**Using PowerShell:**
```powershell
$body = @{
  channel = "C1234567890"
  text = "Hello from Helio service! 🤖"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8002/api/slack/send `
  -ContentType "application/json" -Body $body
```

**⚠️ Replace `C1234567890` with your actual channel ID!**

**Expected response:**
```json
{
  "ok": true,
  "ts": "1234567890.123456"
}
```

### Step 18: Verify in Slack

1. Check your Slack channel
2. You should see the message posted by your bot
3. It will show your bot's name as the sender

---

## PART 5: TEST MESSAGE FILTERING & CLASSIFICATION

### Test 19: Bot Messages Are Ignored

**What to test:** Bot messages should NOT be stored in database

**Steps:**
1. Send a message from your service (like in Step 17)
2. Query all messages: `curl http://localhost:8002/api/slack/messages`
3. Check the stored messages:
   - ✅ User messages have `user_id` like `U1234...`
   - ✅ Bot messages should NOT appear (they're filtered by the service)

**Why:** The service checks for `event.bot_id` and ignores bot messages to avoid infinite loops.

### Test 20: Message Edits Are Ignored

**What to test:** When you edit a message, the edit should NOT create a new database entry

**Steps:**
1. Send a message in Slack: `Original message`
2. Check database - it should be stored
3. Edit the message to: `Edited message`
4. Check database again
5. ✅ Verify: Still only ONE entry with the ORIGINAL text

**Why:** Message edit events have `subtype: "message_changed"` which the service ignores.

### Test 21: Message Deletes Are Ignored

**What to test:** Deleting a message doesn't update the database

**Steps:**
1. Send a message in Slack
2. Verify it's stored in database
3. Delete the message in Slack
4. Check database again
5. ✅ Verify: Message still exists in database (deletion is ignored)

**Why:** Delete events have `subtype: "message_deleted"` which the service ignores.

### Test 22: Multiple Messages

**Steps:**
1. Send 3 different messages in Slack:
   - `Test message 1`
   - `Test message 2`
   - `Test message 3`
2. Query API: `curl http://localhost:8002/api/slack/messages`
3. ✅ Verify:
   - All 3 messages appear
   - Ordered by newest first (`created_at DESC`)
   - Each has unique `message_ts`

---

## PART 6: TROUBLESHOOTING

### Problem: Messages not appearing in database

**Check:**
- [ ] Is ngrok still running? (If you restart it, update Slack Event URL)
- [ ] Is your service running? (`npm run dev`)
- [ ] Check service logs for errors
- [ ] Is bot invited to the channel? (Do `/invite @BotName`)
- [ ] Are event subscriptions saved in Slack app settings?
- [ ] Is Slack Event URL verified (green checkmark)?

**Debug:**
```bash
# Check service health
curl http://localhost:8002/api/slack/health

# Check ngrok is forwarding
curl https://your-ngrok-url/api/slack/health
```

### Problem: Can't send messages

**Check:**
- [ ] Is `SLACK_BOT_TOKEN` in `.env` correct?
- [ ] Did you restart service after updating `.env`?
- [ ] Does bot have `chat:write` permission?
- [ ] Is channel ID correct?

**Debug:**
```bash
# Check for error response (verbose mode)
curl -X POST http://localhost:8002/api/slack/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"C123","text":"test"}' \
  -v
```

### Problem: "Invalid signature" or "Request too old" errors

**Check:**
- [ ] Is `SLACK_SIGNING_SECRET` in `.env` correct?
- [ ] Did you restart service after changing `.env`?
- [ ] Is system clock accurate? (Slack rejects requests >5 minutes old)

### Problem: Port 8002 already in use

**Solutions:**

Option 1: Use different port
```bash
PORT=8003 npm run dev
# Then update ngrok: ngrok http 8003
```

Option 2: Find and kill process on port 8002

Windows:
```bash
netstat -ano | findstr :8002
taskkill /PID <PID> /F
```

Linux/Mac:
```bash
lsof -i :8002
kill -9 <PID>
```

### Problem: Database connection error

**Check:**
- [ ] Is PostgreSQL running?
- [ ] Is `DATABASE_URL` in `.env` correct?
- [ ] Can you connect manually?

**Test connection:**
```bash
psql postgresql://user:password@localhost:5432/helio_slack
```

---

## QUICK COMMAND REFERENCE

### Service Health
```bash
curl http://localhost:8002/api/slack/health
```

### Get All Messages
```bash
curl http://localhost:8002/api/slack/messages | jq
```

### Send Message
```bash
curl -X POST http://localhost:8002/api/slack/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"CHANNEL_ID","text":"Your message here"}'
```

### Database Queries

```sql
-- View all messages
SELECT * FROM slack_messages ORDER BY created_at DESC;

-- Count messages
SELECT COUNT(*) FROM slack_messages;

-- Messages from specific user
SELECT * FROM slack_messages WHERE user_id = 'U1234567890';

-- Recent messages (last 10)
SELECT id, text, user_id, created_at
FROM slack_messages
ORDER BY created_at DESC
LIMIT 10;
```

### Restart Service
```bash
# Stop: Ctrl+C
# Start:
npm run dev
```

---

## TEST CHECKLIST

Complete this checklist to verify everything works:

### Setup
- [ ] Slack app created
- [ ] Bot token obtained
- [ ] Signing secret obtained
- [ ] `.env` file configured
- [ ] PostgreSQL running
- [ ] Service starts successfully
- [ ] Health endpoint responds
- [ ] ngrok tunnel established
- [ ] Slack Event Subscriptions configured and verified

### Core Functionality
- [ ] Bot invited to channel
- [ ] Message sent in Slack appears in database
- [ ] Message retrieved via GET /api/slack/messages
- [ ] Message has correct text, user_id, channel_id
- [ ] Can send message from service to Slack
- [ ] Message appears in Slack channel

### Filtering
- [ ] Bot messages NOT stored in database
- [ ] Message edits NOT creating new entries
- [ ] Multiple messages all stored correctly
- [ ] Messages ordered by newest first

**Once all checkmarks are complete, your Slack service integration is working correctly! 🎉**
