# MCP Tools Reference

Complete parameter documentation for all Trigger.dev MCP tools.

## list_orgs

List all organizations you have access to.

```
Input: {}
Output: [{ slug: "my-org", id: "org_xxx" }]
```

## list_projects

List all projects in your account.

```
Input: {}
Output: [{ ref: "proj_xxx", name: "My Project" }]
```

## create_project_in_org

Create a new project in an organization.

```
Input: { "orgParam": "my-org-slug", "name": "My Background Jobs" }
Output: { ref: "proj_xxx", name: "My Background Jobs" }
```

## initialize_project

Initialize Trigger.dev in a directory.

```
Input: { "orgParam": "my-org", "projectName": "email-jobs", "cwd": "/path/to/project" }
Output: Creates trigger.config.ts, src/trigger/ directory, installs SDK
```

## get_current_worker

Get worker info, task list, and payload schemas for an environment.

```
Input: { "environment": "dev" }
Output: {
  version: "20250225.1",
  tasks: [{
    id: "hello-world",
    payloadSchema: { type: "object", properties: {...} },
    machine: "small-1x",
    queue: { name: "default", concurrencyLimit: 10 }
  }]
}
```

Always call this before triggering tasks to verify IDs and schemas.

## trigger_task

Trigger a task with payload.

```
Input: {
  "taskId": "process-order",
  "payload": { "orderId": "ORD-123" },
  "environment": "dev",
  "options": {
    "tags": ["priority"],
    "idempotencyKey": "order-ORD-123",
    "machine": "medium-1x",
    "maxAttempts": 5,
    "maxDuration": 300,
    "delay": "5m",
    "ttl": "30m",
    "queue": { "name": "high-priority" }
  }
}
Output: { id: "run_abc123", status: "QUEUED" }
```

### Trigger Options

| Option | Type | Description |
|--------|------|-------------|
| delay | string/datetime | "5m", "2h", or ISO datetime |
| tags | string[] | Up to 5, each < 128 chars |
| machine | enum | micro to large-2x |
| maxAttempts | integer | Max retry attempts |
| maxDuration | number | Max seconds |
| ttl | string/integer | Time-to-live |
| idempotencyKey | string | Prevent duplicates |
| queue | object | Override queue name |

## list_runs

List and filter runs.

```
Input: {
  "environment": "prod",
  "status": "FAILED",
  "taskIdentifier": "process-order",
  "tag": "vip-customer",
  "period": "7d",
  "limit": 20
}
```

### Filter Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | enum | QUEUED, EXECUTING, COMPLETED, FAILED, CRASHED, etc. |
| taskIdentifier | string | Filter by task ID |
| tag | string | Filter by tag |
| version | string | Filter by worker version |
| machine | enum | Filter by machine preset |
| period | string | "1d", "7d", "30d" |
| from / to | ISO datetime | Custom time range |
| limit | integer | Max 100 |
| cursor | string | Pagination cursor |

## get_run_details

Get run trace, logs, and output.

```
Input: { "runId": "run_abc123", "environment": "prod", "maxTraceLines": 500 }
Output: { status, error, trace: [...], output: {...} }
```

## wait_for_run_to_complete

Wait for a run to finish and return the result.

```
Input: { "runId": "run_abc123", "timeoutInSeconds": 120 }
Output: { status: "COMPLETED", output: { processed: true } }
```

## cancel_run

Cancel a running or queued run.

```
Input: { "runId": "run_abc123", "environment": "prod" }
```

## deploy

Deploy to an environment.

```
Input: { "environment": "prod", "skipPromotion": false }
Output: { status: "DEPLOYED", version: "20250225.3" }
```

## list_deploys

List deployments with filters.

```
Input: { "environment": "prod", "status": "DEPLOYED", "limit": 5 }
```

## list_preview_branches

List all preview branches.

```
Input: {}
Output: [{ branch: "feature/new-task", ... }]
```

Not available in `--dev-only` mode.

## search_docs

Search Trigger.dev documentation.

```
Input: { "query": "wait for token human in the loop" }
Output: Relevant documentation pages
```

---

## REST Management API

### Trigger a Task

```bash
POST /api/v1/tasks/{taskId}/trigger

curl -X POST "${TRIGGER_API_URL}/api/v1/tasks/process-order/trigger" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"orderId": "ORD-123"}, "options": {"tags": ["priority"]}}'
```

### Batch Trigger

```bash
POST /api/v1/tasks/{taskId}/batch

curl -X POST "${TRIGGER_API_URL}/api/v1/tasks/process-item/batch" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"payload": {"id": "1"}}, {"payload": {"id": "2"}}]}'
```

### Get Run Status

```bash
GET /api/v1/runs/{runId}

curl -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  "${TRIGGER_API_URL}/api/v1/runs/run_abc123"
```

### List Runs

```bash
GET /api/v1/runs?status=FAILED&limit=10&period=24h
```

### Cancel Run

```bash
POST /api/v1/runs/{runId}/cancel
```

### Complete Wait Token

```bash
POST /api/v1/waitpoints/tokens/{tokenId}/complete

curl -X POST "${TRIGGER_API_URL}/api/v1/waitpoints/tokens/${TOKEN_ID}/complete" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"approved": true}}'
```

### Set Environment Variables

```bash
POST /api/v1/projects/{projectRef}/envvars/{environment}

curl -X POST "${TRIGGER_API_URL}/api/v1/projects/proj_xxx/envvars/production" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"variables": {"DATABASE_URL": "postgres://...", "API_KEY": "sk-..."}}'
```

### Create Schedule

```bash
POST /api/v1/schedules

curl -X POST "${TRIGGER_API_URL}/api/v1/schedules" \
  -H "Authorization: Bearer ${TRIGGER_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"task": "daily-report", "cron": "0 9 * * *", "externalId": "report-daily"}'
```

### SDK Management API

```ts
import { configure, runs } from "@trigger.dev/sdk";

configure({ secretKey: process.env.TRIGGER_SECRET_KEY });

const result = await runs.list({ limit: 10, status: ["COMPLETED"] });
const run = await runs.retrieve(runId);
await runs.cancel(runId);
```
