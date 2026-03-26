---
name: api-reference
description: This skill should be used when the user asks for "trigger.dev API endpoints", "trigger.dev REST API", "trigger.dev curl examples", "trigger.dev API documentation", "trigger.dev Management API", or needs specific HTTP endpoint details for Trigger.dev.
disable-model-invocation: true
---

# Trigger.dev REST API Reference

Curated Management API endpoints. For full docs, search via `tds-search_docs`.

## Authentication

Two authentication methods:

### Secret Key (per-environment)

```bash
curl -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/<endpoint>"
```

Key formats:
- `tr_dev_xxx` — Development environment
- `tr_prod_xxx` — Production environment

### Personal Access Token (for CI/CD and admin)

```bash
curl -H "Authorization: Bearer ${TRIGGER_ACCESS_TOKEN}" \
  "${TRIGGER_API_URL}/api/v1/<endpoint>"
```

Token format: `tr_pat_xxx`

### SDK Configuration

```typescript
import { configure, runs } from "@trigger.dev/sdk";

configure({
  secretKey: process.env.TRIGGER_SECRET_KEY,  // or set TRIGGER_SECRET_KEY env var
  baseURL: process.env.TRIGGER_API_URL,       // for self-hosted (default: https://api.trigger.dev)
  previewBranch: process.env.TRIGGER_PREVIEW_BRANCH,  // optional
});
```

## Trigger a Task

```bash
POST /api/v1/tasks/{taskId}/trigger

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"orderId": "ORD-123"},
    "options": {
      "tags": ["priority"],
      "idempotencyKey": "order-ORD-123",
      "queue": {"name": "orders"}
    }
  }' \
  "${TRIGGER_API_URL}/api/v1/tasks/process-order/trigger" | jq .
```

Response:
```json
{"id": "run_abc123", "status": "QUEUED"}
```

## Batch Trigger

```bash
POST /api/v1/tasks/{taskId}/batch

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"payload": {"id": "1"}},
      {"payload": {"id": "2"}}
    ]
  }' \
  "${TRIGGER_API_URL}/api/v1/tasks/process-item/batch" | jq .
```

## Get Run Status

```bash
GET /api/v1/runs/{runId}

curl -s -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/runs/run_abc123" | jq .
```

## List Runs

```bash
GET /api/v1/runs?status=FAILED&limit=10

curl -s -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/runs?status=FAILED&limit=10&period=24h" | jq .
```

Query parameters: `status`, `taskIdentifier`, `tag`, `period`, `limit`, `cursor`

## Cancel a Run

```bash
POST /api/v1/runs/{runId}/cancel

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/runs/run_abc123/cancel" | jq .
```

## Complete a Wait Token

```bash
POST /api/v1/tokens/{tokenId}/complete

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"approved": true}}' \
  "${TRIGGER_API_URL}/api/v1/tokens/${TOKEN_ID}/complete" | jq .
```

## List Projects

```bash
GET /api/v1/projects

curl -s -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/projects" | jq .
```

## Schedules

### Create Schedule

```bash
POST /api/v1/schedules

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "daily-report",
    "cron": "0 9 * * *",
    "externalId": "report-daily",
    "deduplicationKey": "report-daily"
  }' \
  "${TRIGGER_API_URL}/api/v1/schedules" | jq .
```

### List Schedules

```bash
GET /api/v1/schedules

curl -s -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/schedules" | jq .
```

## Environment Variables

### Set Env Vars

```bash
POST /api/v1/projects/{projectRef}/envvars/{environment}

curl -s -X POST \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "DATABASE_URL": "postgres://...",
      "API_KEY": "sk-..."
    }
  }' \
  "${TRIGGER_API_URL}/api/v1/projects/proj_xxx/envvars/production" | jq .
```

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid payload) |
| 401 | Invalid or missing secret key |
| 404 | Resource not found |
| 409 | Conflict (idempotencyKey already used) |
| 422 | Validation error |
| 429 | Rate limited |
| 500 | Server error |

## Realtime API

Realtime authentication uses **Public Access Tokens** or **Trigger Tokens** (not secret keys).

```bash
# Subscribe to run updates via Server-Sent Events
curl -N -H "Authorization: Bearer ${TRIGGER_PUBLIC_ACCESS_TOKEN}" \
  "${TRIGGER_API_URL}/api/v1/runs/run_abc123/subscribe"
```

For Realtime auth details: `tds-search_docs(query="realtime authentication public access tokens")`

## Management API via SDK

The Management API is available through `@trigger.dev/sdk` (no separate package):

```typescript
import { configure, runs } from "@trigger.dev/sdk";

configure({ secretKey: process.env.TRIGGER_SECRET_KEY });

// List runs
const result = await runs.list({ limit: 10, status: ["COMPLETED"] });

// Get run details
const run = await runs.retrieve(runId);

// Cancel a run
await runs.cancel(runId);
```
