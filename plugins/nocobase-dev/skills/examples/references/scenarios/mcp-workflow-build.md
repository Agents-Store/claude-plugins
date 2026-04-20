# Scenario 6 — MCP-Driven Workflow Build

Create a collection-triggered workflow that sends a welcome email when a customer is created. Uses `workflows_create`, `workflows_nodes_create`, and `flow_nodes_update` entirely via MCP.

## Prerequisites

- `nc-mcp` connected
- `customers` collection exists
- Mailer plugin enabled (`nocobase-plugin-mailer` or similar)
- Role has `create`/`update` on `workflows` and `flow_nodes`

## Step 1 — Bulk-load schemas

```
ToolSearch(query: "nc-mcp", max_results: 30)
```

## Step 2 — Create the workflow (disabled initially)

```
workflows_create({
  values: {
    title: "Customer Welcome Email",
    type: "collection",
    enabled: false,
    config: {
      mode: 1,
      collection: "customers",
      changed: [],
      condition: {}
    }
  }
})
```

Returns `{ data: { id: <workflowId>, ... } }`. Save `workflowId`.

## Step 3 — Add a condition node (only for email-present records)

```
workflows_nodes_create({
  filterByTk: <workflowId>,
  values: {
    type: "condition",
    title: "Email is present",
    config: {
      calculation: {
        group: {
          type: "and",
          calculations: [
            { calculator: "!=", operands: ["{{$context.data.email}}", ""] }
          ]
        }
      }
    }
  }
})
```

Returns the node with its `id` and `key`. Save the condition node id.

## Step 4 — Add a mailer node inside the condition's "true" branch

```
workflows_nodes_create({
  filterByTk: <workflowId>,
  values: {
    type: "mail",
    upstreamId: <conditionNodeId>,
    branchIndex: 0,
    title: "Send welcome email",
    config: {
      to: ["{{$context.data.email}}"],
      subject: "Welcome to {{$env.APP_NAME}}!",
      content: "Hi {{$context.data.name}}, thanks for signing up."
    }
  }
})
```

## Step 5 — Enable the workflow

```
workflows_update({
  filterByTk: <workflowId>,
  values: { enabled: true }
})
```

## Step 6 — Test

Create a customer via MCP:

```
resource_create({
  resource: "customers",
  values: {
    name: "Test User",
    email: "test@example.com",
    status: "active"
  }
})
```

## Step 7 — Inspect execution

```
executions_list({
  filter: { workflowId: { $eq: <workflowId> } },
  sort: ["-createdAt"],
  pageSize: 1
})

executions_get({
  filterByTk: <executionId>,
  appends: ["jobs"]
})
```

Check each job's status. If the mailer job failed, the error body has the SMTP response.

## Step 8 — Version the workflow (optional, before changes)

```
workflows_revision({
  filterByTk: <workflowId>
})
```

Returns `{ data: { newVersionId } }`. The old version continues to run past executions; new triggers go to the new version.

## Contrast with HTTP fallback

Same steps via HTTP:
- `POST /api/workflows:create` → workflow
- `POST /api/flow_nodes:create` × 2 → condition + mailer nodes
- `POST /api/workflows:update?filterByTk=<id>` → enable
- `POST /api/customers:create` → trigger
- `GET /api/executions:list?filter=...` → inspect

MCP path is structurally the same but returns typed responses and handles auth via the transport.

## See also

- `workflow-automation` — full MCP tool catalog, node reference library
- `mcp-patterns` — transport conventions and fallback chain
- `record-operations` — `resource_create` and filter syntax
- `troubleshoot` — execution failure diagnosis
