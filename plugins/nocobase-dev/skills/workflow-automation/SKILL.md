---
name: workflow-automation
description: |
  NocoBase workflow engine — triggers, nodes, executions, jobs, revisions, and approval inbox — across MCP, CLI, and HTTP transports. Use when:
  - "create a workflow"
  - "add workflow nodes"
  - "monitor executions"
  - "set up triggers"
  - "manage workflow versions"
  - "automate business processes"
  - "workflows_execute"
  - "workflows_revision"
  - "flow_nodes_update"
  - "executions_cancel"
  - "jobs_resume"
  - "approval workflow NocoBase"
  - "workflow node types"
  - "workflow trigger types"
---

# Workflow Automation

Manage NocoBase workflows across three transports — create and configure workflows, attach processing nodes, monitor executions, handle versioning, and run manual-node tasks.

## MCP tools

### Workflow CRUD + execute
| Task | MCP tool |
|------|----------|
| List workflows | `workflows_list` |
| Get one with nodes | `workflows_get` |
| Create | `workflows_create` |
| Update | `workflows_update` |
| Delete | `workflows_destroy` |
| **Execute manually** | `workflows_execute` (`filterByTk` + body → `{ execution, newVersionId? }`) |
| Sync across envs | `workflows_sync` |
| Create new revision | `workflows_revision` |
| Create a node in a workflow | `workflows_nodes_create` |

### Nodes (inside a workflow)
| Task | MCP tool |
|------|----------|
| Get one node | `flow_nodes_get` |
| Update node config | `flow_nodes_update` |
| Delete node | `flow_nodes_destroy` |
| Delete node + downstream branch | `flow_nodes_destroy_branch` |
| Duplicate | `flow_nodes_duplicate` |
| Reorder | `flow_nodes_move` |
| Test with sample input | `flow_nodes_test` |

### Executions (historical runs)
| Task | MCP tool |
|------|----------|
| List | `executions_list` |
| Get one with job tree | `executions_get` |
| Cancel running | `executions_cancel` |
| Delete history | `executions_destroy` |

### Background jobs (long-running tasks outside the workflow engine)
| Task | MCP tool |
|------|----------|
| List | `jobs_list` |
| Get one | `jobs_get` |
| Resume paused | `jobs_resume` |

### Approval inbox
| Task | MCP tool |
|------|----------|
| List manual-node tasks assigned to me | `user_workflow_tasks_list_mine` |

## Node and trigger reference library

Full upstream node/trigger reference tree lives in `references/workflow/`:

- `references/workflow/nodes/` — per-node reference files: aggregate, approval, calculation, cc, condition, create, delay, destroy, end, json-query, json-variable-mapping, loop, mailer, manual, multi-conditions, notification, output, parallel, query, request, response-message, script, sql, subflow, update, webhook-response
- `references/workflow/triggers/` — per-trigger reference files: action, approval, collection, custom-action, request-interception, schedule, webhook
- `references/workflow/conventions/index.md` — workflow authoring conventions, variable system, error handling, context shape
- `references/workflow/modeling/` — data model for workflows, nodes, executions, jobs
- `references/workflow/http-api/` — HTTP endpoint reference for each resource

### Node picker

| Intent | Node |
|--------|------|
| Branch on condition | `condition.md` |
| Compute a value | `calculation.md` |
| Iterate a list | `loop.md` |
| Run in parallel | `parallel.md` |
| Call a database-write | `create.md` / `update.md` / `destroy.md` |
| Query for records | `query.md` / `aggregate.md` |
| Call an external HTTP API | `request.md` |
| Wait for a user | `manual.md` / `approval.md` |
| Send email | `mailer.md` |
| Send notification | `notification.md` |
| Run raw SQL | `sql.md` |
| Run custom JS | `script.md` |
| Call another workflow | `subflow.md` |
| Wait N seconds | `delay.md` |
| Finish the workflow with output | `end.md` / `output.md` |
| Respond to HTTP trigger | `response-message.md` / `webhook-response.md` |
| Query a JSON value | `json-query.md` |
| Map JSON variables | `json-variable-mapping.md` |
| CC someone | `cc.md` |
| Multi-branch conditions | `multi-conditions.md` |

### Trigger picker

| Intent | Trigger |
|--------|---------|
| Fire on record create/update/destroy | `collection.md` |
| Fire on a button click | `action.md` / `custom-action.md` |
| Fire on schedule (cron) | `schedule.md` |
| Fire via webhook | `webhook.md` |
| Fire on approval step | `approval.md` |
| Intercept an HTTP request | `request-interception.md` |

## Authentication (HTTP path)

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

## Action Trigger (Button Click)

Fires when a user clicks a workflow-bound action button in the UI.

```json
{
  "type": "action",
  "title": "Submit for Approval",
  "config": {
    "collection": "purchase_requests",
    "appends": []
  }
}
```

```bash
curl -X POST "${NOCOBASE_URL}/api/workflows:create" \
  -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "action",
    "title": "Submit for Approval",
    "enabled": false,
    "config": {
      "collection": "purchase_requests"
    }
  }'
```

Action triggers are useful for manual approval workflows, batch processing, and any user-initiated automation.

## Variable System

### Context Variables

| Variable | Description |
|----------|-------------|
| `$context.data` | Trigger record data (all fields) |
| `$context.data.id` | Record ID |
| `$context.data.fieldName` | Specific field value |
| `$context.user` | Current user who triggered the workflow |
| `$context.params` | Action parameters (for action triggers) |

### Job Variables

| Variable | Description |
|----------|-------------|
| `$jobsData.nodeKey` | Output from a specific node |
| `$jobsData.queryResult` | Result of Query node |
| `$jobsData.calculationResult` | Result of Calculation node |

### System Functions

| Function | Description |
|----------|-------------|
| `NOW()` | Current datetime |
| `DATEADD(date, n, unit)` | Add time to date |
| `DATEDIFF(date1, date2, unit)` | Difference between dates |

### Variable Passing Between Nodes

Access trigger record:
```
{{$context.data.id}}          → Record ID
{{$context.data.status}}      → Field value
{{$context.data.createdBy}}   → Creator reference
```

Access output from previous nodes:
```
{{$jobsData.queryNodeKey}}              → Full query result
{{$jobsData.queryNodeKey[0].name}}      → First result's name field
{{$jobsData.calculationNodeKey}}        → Calculation result
```

## Execution Modes

| Mode | Description | Use When |
|------|-------------|----------|
| Sync | Blocks until complete | Before-event validation, data must be ready |
| Async | Non-blocking (recommended) | After-event notifications, heavy processing |

## Error Handling Patterns

### HTTP Request Retry

```
Trigger: orders.afterCreate
1. Request: POST to external API
2. Condition: Check request result
   - Success → Continue normal flow
   - Failure → Create: Log error to error_logs
              → Delay: 5 minutes
              → Request: Retry the original request
```

### Missing Data Guard

```
Trigger: contacts.afterCreate
1. Condition: {{$context.data.email != null}}
   - True → Request: Send welcome email
   - False → Create: Log "missing email" to audit_logs
```

### Cascading Update Safety

```
Trigger: orders.afterUpdate
1. Query: Get related order_items
2. Condition: {{$jobsData.queryResult.length > 0}}
   - True → Loop: Update each item
   - False → (skip, no items to update)
```

### Chaining Multiple Conditions

```
Trigger: deals.afterUpdate
1. Condition: status changed?
   Yes:
     2. Condition: new status == "Won"?
        Yes:
          3. Calculate: commission = amount * 0.05
          4. Create: commission_record
          5. Request: Notify sales team
        No:
          2b. Condition: new status == "Lost"?
              Yes:
                3b. Create: lost_reason_record
                4b. Request: Notify manager
              No: (skip)
   No: (skip)
```

## Best Practices

1. **Start disabled** — create workflows with `enabled: false` and test before activating.
2. **Use revisions** — create revisions before making changes to preserve the working version.
3. **Monitor executions** — regularly check `executions:list` for failed runs.
4. **Filter triggers** — add conditions to collection triggers to avoid unnecessary executions.
5. **Test nodes individually** — use `flow_nodes:test` to verify node logic before running the full workflow.
6. **Clean up executions** — destroy old execution records to keep the database clean.
7. **Resume stuck jobs** — check `userWorkflowTasks:listMine` for pending approvals.
8. **Use async mode** — unless you need to block the user operation (before-event validation).
9. **Guard against nulls** — always check query results are not empty before accessing fields.
10. **Retry HTTP requests** — for external calls, add retry logic with delay nodes.
11. **Log important events** — create audit trail records in critical workflows.
12. **Use parallel branches** — for independent actions (notify + log simultaneously).

## See also

- `mcp-patterns` — transport conventions
- `record-operations` — data CRUD from inside query/create/update/destroy nodes
- `auth-and-users` — role permissions that gate what a workflow can do
- `system-admin` — jobs, app-level status, restart
- `troubleshoot` — execution failure debugging
