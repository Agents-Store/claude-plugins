# MCP Tool Patterns

Common patterns for using Trigger.dev MCP tools effectively.

## General Parameters

Most tools share these optional parameters:

| Parameter | Description |
|-----------|-------------|
| `projectRef` | Project ref (proj_xxx), auto-detected from trigger.config.ts |
| `configPath` | Path to trigger.config.ts (for monorepos) |
| `environment` | dev, staging, prod, preview |
| `branch` | Branch name (only for preview environment) |

## Project Discovery Pattern

```
1. tds-list_orgs()
   -> [{slug: "my-org", id: "org_xxx"}]

2. tds-list_projects()
   -> [{name: "My Jobs", ref: "proj_xxx", org: "my-org"}]

3. tds-get_current_worker(projectRef="proj_xxx", environment="dev")
   -> {version: "20250225.1", tasks: [{id: "hello-world", ...}]}
```

## Task Execution Pattern

```
1. Get task list and schemas:
   tds-get_current_worker(environment="dev")
   -> tasks: [{
        id: "process-order",
        payloadSchema: {
          type: "object",
          properties: {
            orderId: {type: "string"},
            items: {type: "array", items: {type: "string"}}
          },
          required: ["orderId"]
        }
      }]

2. Trigger with matching payload:
   tds-trigger_task(
     taskId="process-order",
     payload={"orderId": "ORD-123", "items": ["item-1"]},
     environment="dev"
   )
   -> {id: "run_abc123", status: "QUEUED"}

3. Monitor:
   tds-wait_for_run_to_complete(runId="run_abc123", timeoutInSeconds=120)
   -> {status: "COMPLETED", output: {...}}
```

## Run Investigation Pattern

```
1. Find problematic runs:
   tds-list_runs(status="FAILED", period="24h", limit=10)
   -> [{id: "run_fail1", taskIdentifier: "process-order", ...}]

2. Get details:
   tds-get_run_details(runId="run_fail1", maxTraceLines=500)
   -> {status: "FAILED", error: "...", trace: [...]}

3. If stuck, cancel:
   tds-cancel_run(runId="run_stuck1")
```

## Deployment Pattern

```
1. Deploy:
   tds-deploy(environment="staging")
   -> {status: "DEPLOYED", version: "20250225.2"}

2. Verify:
   tds-list_deploys(environment="staging", limit=1)
   -> [{status: "DEPLOYED", version: "20250225.2"}]

3. Check tasks:
   tds-get_current_worker(environment="staging")
   -> {version: "20250225.2", tasks: [...]}
```

## Preview Branch Pattern

```
1. List existing previews:
   tds-list_preview_branches()
   -> [{branch: "feature/new-task", ...}]

2. Deploy new preview:
   tds-deploy(environment="preview", branch="feature/new-task")

3. Trigger in preview:
   tds-trigger_task(
     taskId="my-task",
     payload={...},
     environment="preview",
     branch="feature/new-task"
   )

4. Monitor in preview:
   tds-list_runs(environment="preview", branch="feature/new-task")
```

## Documentation Search Pattern

```
For coding questions:
  tds-search_docs(query="how to use wait.for with token")

For configuration:
  tds-search_docs(query="trigger.config.ts build extensions prisma")

For API reference:
  tds-search_docs(query="triggerAndWait batch trigger API")

For deployment:
  tds-search_docs(query="deploy staging production preview environments")
```

## Error Handling

| Scenario | Action |
|----------|--------|
| Task not found | Use tds-get_current_worker to list available tasks |
| Run not found | Verify runId format (starts with run_) and environment |
| Deploy fails | Check tds-list_deploys with status="FAILED" for details |
| Timeout waiting | Increase timeoutInSeconds or check run with tds-get_run_details |
| Project not found | Use tds-list_projects to find correct projectRef |
