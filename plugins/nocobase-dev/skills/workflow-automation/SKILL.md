---
name: workflow-automation
description: Workflow engine — triggers, nodes, executions, jobs, versioning. This skill should be used when the user asks to "create a workflow", "add workflow nodes", "monitor executions", "set up triggers", "manage workflow versions", or "automate business processes" in NocoBase.
---

# Workflow Automation

Manage NocoBase V2 workflows through the HTTP API — create and configure workflows, attach processing nodes, monitor executions, and handle versioning.

## Authentication

All requests require the API key header:

```
Authorization: Bearer ${NOCOBASE_API_KEY}
```

Base URL for all endpoints: `${NOCOBASE_URL}/api/`

## Workflow CRUD

### List Workflows

```bash
curl -X GET "${NOCOBASE_URL}/api/workflows:list?page=1&pageSize=20" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Supports query parameters:
- `filter` — JSON filter object (e.g., `{"enabled": true}`)
- `sort` — field to sort by, prefix with `-` for descending (e.g., `-createdAt`)
- `page` / `pageSize` — pagination
- `appends` — include related data (e.g., `nodes`, `executions`)

### Get Single Workflow

```bash
curl -X GET "${NOCOBASE_URL}/api/workflows:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Create Workflow

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "collection",
    "title": "Order Notification",
    "description": "Send notification when a new order is created",
    "enabled": false,
    "config": {
      "collection": "orders",
      "mode": 1,
      "condition": {
        "$and": []
      }
    }
  }'
```

Fields:
- `type` (required) — trigger type: `"collection"` (data events) or `"schedule"` (cron-based)
- `title` (required) — human-readable name
- `description` — optional explanation
- `enabled` — `true` to activate immediately, `false` (default) to keep draft
- `config` — trigger-specific configuration object

### Update Workflow

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Order Notification v2",
    "enabled": true
  }'
```

Send only the fields to change.

### Destroy Workflow

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Execute Workflow (Manual Trigger)

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:execute?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "data": { "id": 42, "title": "Test Order" }
    }
  }'
```

Manually triggers a workflow execution. Pass context data matching what the trigger would normally provide.

### Revision (Version Management)

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:revision?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Create a new revision of the workflow. The current workflow is duplicated with a new version number under the same `key`. Only one version per key can be the current active version.

### Sync Workflow

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:sync?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Synchronize workflow configuration, useful after external modifications.

## Trigger Types

### Collection Trigger (Data Events)

Fires when records in a collection are created, updated, or deleted.

```json
{
  "type": "collection",
  "config": {
    "collection": "orders",
    "mode": 1,
    "condition": {
      "$and": [
        { "status": "confirmed" }
      ]
    }
  }
}
```

Mode values:
- `1` — after record created
- `2` — after record updated
- `3` — after record created or updated
- `4` — after record deleted
- `5` — after record created, updated, or deleted

The `condition` field uses NocoBase filter syntax to restrict which records trigger the workflow.

### Schedule Trigger (Cron)

Fires on a recurring schedule.

```json
{
  "type": "schedule",
  "config": {
    "mode": 0,
    "cron": "0 9 * * 1-5",
    "limit": 0,
    "startsOn": "",
    "endsOn": ""
  }
}
```

- `mode` — `0` for cron-based scheduling
- `cron` — standard cron expression (minute hour day month weekday)
- `limit` — max number of executions (`0` = unlimited)
- `startsOn` / `endsOn` — optional date bounds

Common cron patterns:
- Every hour: `0 * * * *`
- Daily at 9 AM: `0 9 * * *`
- Weekdays at 9 AM: `0 9 * * 1-5`
- First of each month: `0 0 1 * *`

## Workflow Nodes

Nodes are the processing steps within a workflow. Attach them to a workflow to define the execution logic.

### Create a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "calculation",
    "title": "Calculate Total",
    "config": {
      "engine": "math.js",
      "expression": "{{$context.data.price}} * {{$context.data.quantity}}"
    }
  }'
```

Replace `1` in the URL with the workflow ID. The `type` and `config` fields vary by node type.

### Get a Node

```bash
curl -X GET "${NOCOBASE_URL}/api/flow_nodes:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Update a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:update?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Node Title",
    "config": {
      "engine": "math.js",
      "expression": "{{$context.data.price}} * {{$context.data.quantity}} * 1.2"
    }
  }'
```

### Destroy a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Duplicate a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:duplicate?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Move a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:move?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "targetId": 5,
    "position": "after"
  }'
```

### Test a Node

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:test?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Destroy Branch

```bash
curl -X POST "${NOCOBASE_URL}/api/flow_nodes:destroyBranch?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Remove an entire branch from a condition or parallel node.

For detailed node type configurations, see `references/workflow-nodes.md`.

## Execution Monitoring

### List Executions

```bash
curl -X GET "${NOCOBASE_URL}/api/executions:list?page=1&pageSize=20" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Filter by workflow: `?filter={"workflowId": 1}`
Filter by status: `?filter={"status": 1}` (1 = resolved, 0 = pending, -1 = failed, -2 = cancelled)

### Get Execution Details

```bash
curl -X GET "${NOCOBASE_URL}/api/executions:get?filterByTk=1&appends=jobs" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

Use `appends=jobs` to include all job details for the execution.

### Cancel Execution

```bash
curl -X POST "${NOCOBASE_URL}/api/executions:cancel?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Destroy Execution

```bash
curl -X POST "${NOCOBASE_URL}/api/executions:destroy?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Jobs

Jobs represent individual node execution results within an execution.

### List Jobs

```bash
curl -X GET "${NOCOBASE_URL}/api/jobs:list?filter={\"executionId\": 1}" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Get Job Details

```bash
curl -X GET "${NOCOBASE_URL}/api/jobs:get?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

### Resume Job

```bash
curl -X POST "${NOCOBASE_URL}/api/jobs:resume?filterByTk=1" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "result": {
      "action": "approve"
    }
  }'
```

Resume a paused job, typically a manual/approval node waiting for user input.

## User Workflow Tasks

List pending tasks assigned to the current user (from manual/approval nodes).

```bash
curl -X GET "${NOCOBASE_URL}/api/userWorkflowTasks:listMine" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}"
```

## Workflow Versioning

NocoBase uses a `key` field to group workflow versions:
- All revisions of a workflow share the same `key`.
- Only one revision per key can be the current (enabled) version.
- Use `workflows:revision` to create a new version from the current one.
- Previous versions are kept for history but are not active.

Workflow pattern for safe updates:
1. Get the current workflow to inspect its configuration.
2. Create a revision with `workflows:revision`.
3. Update the new revision with changes.
4. Enable the new revision and disable the old one.

## Common Automation Patterns

### Record Create Notification

```
1. Create workflow with type "collection", mode 1 (afterCreate)
2. Add a "request" node to POST to a webhook URL
3. Enable the workflow
```

### Scheduled Data Cleanup

```
1. Create workflow with type "schedule", cron "0 2 * * *" (daily at 2 AM)
2. Add a "query" node to find stale records
3. Add a "destroy" node to delete them
4. Enable the workflow
```

### Approval Flow

```
1. Create workflow with type "collection" or manual trigger
2. Add a "condition" node to check amount thresholds
3. Add "manual" nodes for approval gates
4. Add "update" nodes to set status based on approval result
5. Add a "request" node to send notifications
```

## Best Practices

1. **Start disabled** — create workflows with `enabled: false` and test before activating.
2. **Use revisions** — create revisions before making changes to preserve the working version.
3. **Monitor executions** — regularly check `executions:list` for failed runs.
4. **Filter triggers** — add conditions to collection triggers to avoid unnecessary executions.
5. **Test nodes individually** — use `flow_nodes:test` to verify node logic before running the full workflow.
6. **Clean up executions** — destroy old execution records to keep the database clean.
7. **Resume stuck jobs** — check `userWorkflowTasks:listMine` for pending approvals.
