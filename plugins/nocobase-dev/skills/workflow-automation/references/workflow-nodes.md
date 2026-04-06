# Workflow Node Types Reference

Complete reference for all NocoBase V2 workflow node types, their type identifiers, required configuration fields, and example JSON payloads.

## Calculation Node

Evaluate expressions to compute values.

**Type identifier:** `calculation`

**Required config fields:**
- `engine` — expression engine (`"math.js"` or `"formula.js"`)
- `expression` — the expression string with variable placeholders

**Example:**

```json
{
  "type": "calculation",
  "title": "Calculate Order Total",
  "config": {
    "engine": "math.js",
    "expression": "{{$context.data.price}} * {{$context.data.quantity}} * (1 - {{$context.data.discount}} / 100)"
  }
}
```

Use `{{$context.data.fieldName}}` to reference trigger record fields and `{{$jobsData.nodeKey}}` to reference outputs from previous nodes.

## Condition Node

Branch execution based on logical conditions.

**Type identifier:** `condition`

**Required config fields:**
- `rejectOnFalse` — whether to stop the workflow if the condition is false (`true` or `false`)
- `engine` — expression engine for evaluating the condition
- `calculation` — the condition expression (evaluates to truthy/falsy)

**Example:**

```json
{
  "type": "condition",
  "title": "Check Order Amount",
  "config": {
    "rejectOnFalse": false,
    "engine": "math.js",
    "calculation": "{{$context.data.total}} > 10000"
  }
}
```

When `rejectOnFalse` is `false`, both true and false branches continue execution. When `true`, the workflow stops on the false branch.

The condition node creates two output branches:
- **True branch** — downstream nodes connected to output index 0
- **False branch** — downstream nodes connected to output index 1

## Query Node

Fetch records from a collection.

**Type identifier:** `query`

**Required config fields:**
- `collection` — target collection name
- `params` — query parameters including filter, sort, limit

**Example:**

```json
{
  "type": "query",
  "title": "Find Related Contact",
  "config": {
    "collection": "contacts",
    "multiple": false,
    "params": {
      "filter": {
        "$and": [
          { "email": "{{$context.data.contactEmail}}" }
        ]
      },
      "sort": ["-createdAt"],
      "limit": 1
    }
  }
}
```

- `multiple` — `false` returns a single record, `true` returns an array
- Access results in subsequent nodes via `{{$jobsData.nodeKey}}`

## Create Node

Create new records in a collection.

**Type identifier:** `create`

**Required config fields:**
- `collection` — target collection name
- `params` — object with `values` containing field-value pairs

**Example:**

```json
{
  "type": "create",
  "title": "Create Notification Record",
  "config": {
    "collection": "notifications",
    "params": {
      "values": {
        "title": "New order #{{$context.data.id}}",
        "message": "Order placed by {{$context.data.createdBy.nickname}}",
        "type": "order_created",
        "read": false
      }
    }
  }
}
```

## Update Node

Modify existing records in a collection.

**Type identifier:** `update`

**Required config fields:**
- `collection` — target collection name
- `params` — object with `filter` (which records to update) and `values` (fields to change)

**Example:**

```json
{
  "type": "update",
  "title": "Mark Order as Approved",
  "config": {
    "collection": "orders",
    "params": {
      "filter": {
        "$and": [
          { "id": "{{$context.data.id}}" }
        ]
      },
      "values": {
        "status": "approved",
        "approvedAt": "{{$date.now}}"
      }
    }
  }
}
```

- `individualHooks` — set to `true` to trigger other collection event workflows for each updated record

## Destroy Node

Delete records from a collection.

**Type identifier:** `destroy`

**Required config fields:**
- `collection` — target collection name
- `params` — object with `filter` to select records to delete

**Example:**

```json
{
  "type": "destroy",
  "title": "Remove Expired Sessions",
  "config": {
    "collection": "sessions",
    "params": {
      "filter": {
        "$and": [
          { "expiresAt": { "$lt": "{{$date.now}}" } }
        ]
      }
    }
  }
}
```

## Manual Node

Pause execution and wait for human input (approval, data entry).

**Type identifier:** `manual`

**Required config fields:**
- `assignees` — array of user IDs or expressions resolving to user IDs
- `forms` — form field definitions for user input (optional)

**Example:**

```json
{
  "type": "manual",
  "title": "Manager Approval",
  "config": {
    "assignees": [1],
    "forms": {
      "approval": {
        "actions": [
          { "key": "approve", "label": "Approve", "status": 1 },
          { "key": "reject", "label": "Reject", "status": -1 }
        ],
        "fields": [
          {
            "name": "comment",
            "type": "string",
            "title": "Comment",
            "required": false
          }
        ]
      }
    }
  }
}
```

- Pending manual tasks appear in `userWorkflowTasks:listMine` for assigned users
- Resume with `jobs:resume` passing the action result
- Status values: `1` = approved/resolved, `-1` = rejected

## Request Node

Make HTTP requests to external APIs.

**Type identifier:** `request`

**Required config fields:**
- `url` — the target URL
- `method` — HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`)

**Optional config fields:**
- `headers` — array of `{name, value}` pairs
- `params` — array of `{name, value}` pairs for query parameters
- `data` — request body (for POST/PUT/PATCH)
- `timeout` — request timeout in milliseconds
- `ignoreFail` — continue workflow even if the request fails

**Example:**

```json
{
  "type": "request",
  "title": "Send Slack Notification",
  "config": {
    "url": "https://hooks.slack.com/services/T00/B00/xxx",
    "method": "POST",
    "headers": [
      { "name": "Content-Type", "value": "application/json" }
    ],
    "data": {
      "text": "New order #{{$context.data.id}} created — total: ${{$context.data.total}}"
    },
    "timeout": 5000,
    "ignoreFail": false
  }
}
```

## Loop Node

Iterate over an array and execute downstream nodes for each item.

**Type identifier:** `loop`

**Config fields:**
- `target` — expression resolving to an array to iterate over

**Example:**

```json
{
  "type": "loop",
  "title": "Process Each Line Item",
  "config": {
    "target": "{{$jobsData.queryNodeKey}}"
  }
}
```

Within the loop body, use `{{$jobsData.loopNodeKey.item}}` to access the current iteration item and `{{$jobsData.loopNodeKey.index}}` for the current index.

## Parallel Branch Node

Execute multiple branches simultaneously.

**Type identifier:** `parallel`

**Config fields:**
- `mode` — `"all"` (wait for all branches) or `"any"` (continue when first completes)

**Example:**

```json
{
  "type": "parallel",
  "title": "Notify All Channels",
  "config": {
    "mode": "all"
  }
}
```

Attach downstream nodes to different output indices to create parallel branches.

## Delay Node

Pause workflow execution for a specified duration.

**Type identifier:** `delay`

**Config fields:**
- `duration` — delay duration value
- `unit` — time unit (`"seconds"`, `"minutes"`, `"hours"`, `"days"`)

**Example:**

```json
{
  "type": "delay",
  "title": "Wait 24 Hours",
  "config": {
    "duration": 24,
    "unit": "hours"
  }
}
```

## Aggregate Node

Perform aggregation operations on a collection or array.

**Type identifier:** `aggregate`

**Config fields:**
- `collection` — target collection name
- `aggregator` — aggregation function (`"count"`, `"sum"`, `"avg"`, `"min"`, `"max"`)
- `field` — field to aggregate on
- `params` — optional filter to scope the aggregation

**Example:**

```json
{
  "type": "aggregate",
  "title": "Count Open Orders",
  "config": {
    "collection": "orders",
    "aggregator": "count",
    "field": "id",
    "params": {
      "filter": {
        "$and": [
          { "status": "open" }
        ]
      }
    }
  }
}
```

## Variable System Reference

### Context Variables

| Variable | Description |
|----------|-------------|
| `{{$context.data}}` | Full trigger record |
| `{{$context.data.fieldName}}` | Specific field from trigger record |
| `{{$context.user}}` | User who triggered the workflow |

### Job Data Variables

| Variable | Description |
|----------|-------------|
| `{{$jobsData.nodeKey}}` | Output from a specific node (use the node's key, not title) |
| `{{$jobsData.nodeKey.fieldName}}` | Specific field from a node's output |

### System Variables

| Variable | Description |
|----------|-------------|
| `{{$date.now}}` | Current ISO datetime |
| `{{$system.now}}` | Current timestamp |

## Node Wiring Order

Nodes execute in the order they are created and linked. When creating a multi-step workflow:

1. Create the first node attached to the workflow.
2. Create subsequent nodes — they are appended in order.
3. Use `flow_nodes:move` to reorder if needed.
4. For branching (condition/parallel), downstream nodes are attached by output index.

The execution engine walks the node chain from the first node to the last, following branch paths as determined by condition results.
