# NocoBase API — Workflows, Nodes, Executions & Jobs

All endpoints use base URL `${NOCOBASE_URL}/api/` with header `Authorization: Bearer ${NOCOBASE_API_KEY}`.

---

## Workflows (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows:list` | List all workflows |
| GET | `/api/workflows:get?filterByTk={id}` | Get workflow details |
| POST | `/api/workflows:create` | Create a new workflow |
| POST | `/api/workflows:update?filterByTk={id}` | Update workflow configuration |
| POST | `/api/workflows:destroy?filterByTk={id}` | Delete a workflow |
| POST | `/api/workflows:execute?filterByTk={id}` | Manually trigger a workflow execution |
| POST | `/api/workflows:revision?filterByTk={id}` | Create a new revision (version) of a workflow |
| POST | `/api/workflows:sync` | Sync workflow definitions (multi-app) |

### List Workflows

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:list?page=1&pageSize=50&sort=[-updatedAt]"
```

**Query parameters:** `filter`, `sort`, `page`, `pageSize`, `fields`, `appends`

### Get Workflow

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:get?filterByTk=1&appends=[nodes,executions]"
```

Use `appends=[nodes]` to include all workflow nodes in the response.

### Create Workflow

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:create" \
  -d '{
    "title": "Order Notification",
    "description": "Send notification when new order is created",
    "type": "collection",
    "enabled": false,
    "config": {
      "collection": "orders",
      "mode": 1,
      "changed": []
    }
  }'
```

**Required body fields:**
- `title` (string) — Workflow display name
- `type` (string) — Trigger type

**Common trigger types:**

| Type | Description | Key Config Fields |
|------|-------------|-------------------|
| `collection` | Triggered by collection events | `collection`, `mode` (1=create, 2=update, 3=delete, 7=all), `changed` |
| `schedule` | Triggered on a schedule/cron | `mode` (0=cron, 1=date field), `cron`, `startsOn`, `endsOn` |
| `action` | Triggered by a custom action button | `collection` |
| `approval` | Triggered by approval submission | `collection` |
| `form` | Triggered by form submission | `collection` |

**Optional body fields:**
- `description` (string) — Workflow description
- `enabled` (boolean) — Whether the workflow is active (default: false)
- `config` (object) — Trigger-specific configuration
- `options` (object) — Additional workflow options

### Update Workflow

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:update?filterByTk=1" \
  -d '{ "enabled": true, "title": "Order Notification v2" }'
```

### Destroy Workflow

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:destroy?filterByTk=1"
```

### Execute Workflow Manually

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows:execute?filterByTk=1" \
  -d '{
    "context": { "data": { "orderId": 42 } }
  }'
```

**Body fields:** `context` (object) — Data passed to the workflow trigger context.

### Create Workflow Revision

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:revision?filterByTk=1"
```

Creates a copy of the current workflow as a new version. The original remains unchanged.

### Sync Workflows

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:sync"
```

Used in multi-app setups to synchronize workflow definitions across instances.

---

## Workflow Nodes (8 endpoints)

Nodes are the individual steps within a workflow. They use a nested resource pattern for creation and a flat resource for other operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflows/{workflowId}/nodes:create` | Create a node in a workflow |
| GET | `/api/flow_nodes:get?filterByTk={nodeId}` | Get node details |
| POST | `/api/flow_nodes:update?filterByTk={nodeId}` | Update node configuration |
| POST | `/api/flow_nodes:destroy?filterByTk={nodeId}` | Delete a node |
| POST | `/api/flow_nodes:duplicate?filterByTk={nodeId}` | Duplicate a node |
| POST | `/api/flow_nodes:move` | Reorder nodes |
| POST | `/api/flow_nodes:test?filterByTk={nodeId}` | Test a node with sample data |
| POST | `/api/flow_nodes:destroyBranch?filterByTk={nodeId}` | Delete a branch from a condition/parallel node |

### Create Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/workflows/1/nodes:create" \
  -d '{
    "type": "query",
    "title": "Find Order",
    "config": {
      "collection": "orders",
      "params": {
        "filter": { "id": "{{$context.data.orderId}}" }
      }
    }
  }'
```

**Required body fields:**
- `type` (string) — Node type
- `title` (string) — Node display name

**Common node types:**

| Type | Description |
|------|-------------|
| `query` | Query records from a collection |
| `create` | Create a record in a collection |
| `update` | Update records in a collection |
| `destroy` | Delete records from a collection |
| `condition` | Branch logic (if/else) |
| `parallel` | Run multiple branches simultaneously |
| `calculation` | Evaluate an expression |
| `request` | Make an HTTP request to external service |
| `sql` | Execute raw SQL |
| `manual` | Pause for manual/human intervention |
| `delay` | Wait for a specified duration |
| `aggregate` | Aggregate data (count, sum, avg, etc.) |
| `loop` | Iterate over a list |

**Optional body fields:**
- `config` (object) — Node-type-specific configuration
- `upstreamId` (integer) — ID of the upstream (previous) node
- `branchIndex` (integer) — Branch index for condition/parallel nodes

### Get Node

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flow_nodes:get?filterByTk=5"
```

### Update Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flow_nodes:update?filterByTk=5" \
  -d '{
    "title": "Find Active Order",
    "config": {
      "collection": "orders",
      "params": {
        "filter": {
          "$and": [
            { "id": "{{$context.data.orderId}}" },
            { "status": "active" }
          ]
        }
      }
    }
  }'
```

### Destroy Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flow_nodes:destroy?filterByTk=5"
```

### Duplicate Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flow_nodes:duplicate?filterByTk=5"
```

Creates a copy of the node including its configuration.

### Move Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flow_nodes:move" \
  -d '{
    "sourceId": 5,
    "targetId": 3,
    "method": "insertAfter"
  }'
```

### Test Node

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/flow_nodes:test?filterByTk=5" \
  -d '{ "context": { "data": { "orderId": 42 } } }'
```

Tests the node in isolation with provided context data.

### Destroy Branch

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flow_nodes:destroyBranch?filterByTk=5"
```

Removes a specific branch from a condition or parallel node, including all child nodes.

---

## Executions (4 endpoints)

Executions are individual runs of a workflow.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/executions:list` | List workflow executions |
| GET | `/api/executions:get?filterByTk={id}` | Get execution details |
| POST | `/api/executions:cancel?filterByTk={id}` | Cancel a running execution |
| POST | `/api/executions:destroy?filterByTk={id}` | Delete an execution record |

### List Executions

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:list?filter={\"workflowId\":{\"$eq\":1}}&sort=[-createdAt]&page=1&pageSize=20"
```

**Common filter fields:** `workflowId`, `status`, `createdAt`

**Execution statuses:**

| Status | Value | Description |
|--------|-------|-------------|
| Started | 0 | Execution is running |
| Resolved | 1 | Completed successfully |
| Rejected | -1 | Failed with error |
| Canceled | -2 | Manually canceled |

### Get Execution

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:get?filterByTk=100&appends=[jobs]"
```

Use `appends=[jobs]` to include all job results within the execution.

### Cancel Execution

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:cancel?filterByTk=100"
```

### Destroy Execution

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:destroy?filterByTk=100"
```

---

## Jobs (3 endpoints)

Jobs represent the result of individual node executions within a workflow execution.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs:list` | List jobs (optionally filter by execution) |
| GET | `/api/jobs:get?filterByTk={id}` | Get job details and result |
| POST | `/api/jobs:resume?filterByTk={id}` | Resume a paused job (manual node) |

### List Jobs

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/jobs:list?filter={\"executionId\":{\"$eq\":100}}"
```

### Get Job

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/jobs:get?filterByTk=500"
```

**Response includes:** `id`, `nodeId`, `executionId`, `status`, `result`, `createdAt`, `updatedAt`

### Resume Job

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/jobs:resume?filterByTk=500" \
  -d '{ "result": { "approved": true, "comment": "Looks good" } }'
```

Used to continue execution after a `manual` node has paused the workflow. The `result` is passed as the node's output.

---

## User Workflow Tasks (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/userWorkflowTasks:listMine` | List pending workflow tasks for the current user |

### List My Tasks

```bash
curl -g -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/userWorkflowTasks:listMine?page=1&pageSize=20&sort=[-createdAt]"
```

Returns tasks that require the current user's action (e.g., approval, manual input).
