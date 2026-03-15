# Slack Service

This service receives Slack events, stores message events in Postgres, and can send messages back to Slack.

## What it does

- Exposes Slack-facing and internal HTTP endpoints under `/api/slack`
- Verifies Slack request signatures on the events endpoint
- Stores incoming Slack message events in the `slack_messages` table
- Sends outbound messages with the Slack Web API

## Prerequisites

- Node.js 18+
- PostgreSQL
- A Slack app with:
  - a bot token for `SLACK_BOT_TOKEN`
  - a signing secret for `SLACK_SIGNING_SECRET`

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
PORT=8002
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
DATABASE_URL=postgresql://user:password@localhost:5432/helio_slack
```

Notes:

- `DATABASE_URL` must point to a reachable Postgres database.
- On startup, the service creates the `slack_messages` table if it does not already exist.
- `SLACK_BOT_TOKEN` is required for the `/api/slack/send` endpoint.
- `SLACK_SIGNING_SECRET` is required for the `/api/slack/events` endpoint.

## Install Dependencies

```bash
npm install
```

## Run the Service

Development mode:

```bash
npm run dev
```

Production mode:

```bash
npm start
```

The service starts on `http://localhost:8002` unless `PORT` is overridden.

## Available Endpoints

- `GET /api/slack/health`
- `GET /api/slack/messages`
- `POST /api/slack/send`
- `POST /api/slack/events`

## How to Test

This package does not currently define an automated `test` script in `package.json`, so testing is manual.

### 1. Verify the service starts

Start the service and confirm you see:

```text
Database initialized: slack_messages table ready
Slack service running on port 8002
```

Then call the health endpoint:

PowerShell:

```powershell
Invoke-RestMethod -Method Get http://localhost:8002/api/slack/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### 2. Test outbound Slack messaging

This verifies that `SLACK_BOT_TOKEN` is valid and the service can call Slack.

PowerShell:

```powershell
$body = @{ channel = "C0123456789"; text = "Hello from slack-service" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8002/api/slack/send -ContentType "application/json" -Body $body
```

Expected response shape:

```json
{
  "ok": true,
  "ts": "1730000000.000100"
}
```

If this fails, verify the bot token and that the bot has permission to post to the target channel.

### 3. Test message retrieval from Postgres

PowerShell:

```powershell
Invoke-RestMethod -Method Get http://localhost:8002/api/slack/messages
```

Expected response shape:

```json
{
  "messages": []
}
```

After Slack events are processed, this endpoint should return saved rows ordered by `created_at` descending.

### 4. Test Slack event ingestion locally

The `/api/slack/events` route requires Slack signature headers, so a plain POST without signing will be rejected.

You have two practical options:

#### Option A: Test with a real Slack app

1. Expose your local service with a tunneling tool such as ngrok.
2. Configure the Slack app event request URL to:

```text
https://<your-public-url>/api/slack/events
```

3. Subscribe to message events in Slack.
4. Post a message in a subscribed channel.
5. Confirm the event is stored by calling `GET /api/slack/messages`.

This is the most realistic end-to-end test because Slack generates valid request signatures automatically.

#### Option B: Send a signed local test request manually

Use the Slack signing secret to generate the `X-Slack-Signature` header.

PowerShell example:

```powershell
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$rawBody = '{"type":"event_callback","event":{"type":"message","ts":"1730000000.000100","channel":"C0123456789","user":"U0123456789","text":"Local signed test"}}'
$baseString = "v0:$timestamp:$rawBody"
$secret = $env:SLACK_SIGNING_SECRET
$hmac = [System.Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($secret))
$hashBytes = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($baseString))
$signature = "v0=" + (($hashBytes | ForEach-Object { $_.ToString('x2') }) -join '')

Invoke-RestMethod \
  -Method Post \
  -Uri http://localhost:8002/api/slack/events \
  -Headers @{ "X-Slack-Request-Timestamp" = "$timestamp"; "X-Slack-Signature" = $signature } \
  -ContentType "application/json" \
  -Body $rawBody
```

Expected behavior:

- The endpoint returns HTTP `200` immediately.
- The message event is processed asynchronously.
- A follow-up `GET /api/slack/messages` call should show the stored message.

### 5. Test Slack URL verification

Slack sends a `url_verification` payload when validating the events endpoint.

Example body:

```json
{
  "type": "url_verification",
  "challenge": "test-challenge"
}
```

When the request is signed correctly, the service responds with:

```json
{
  "challenge": "test-challenge"
}
```