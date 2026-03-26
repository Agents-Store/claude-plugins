---
name: mcp-patterns
description: This skill should be used when the user asks about "trigger.dev MCP tools", "which trigger.dev tools are available", "how to use trigger.dev MCP", "trigger.dev tool parameters", "tds tools", or needs to know which MCP operations are available for Trigger.dev and how to use them correctly.
---

# Trigger.dev MCP Tool Patterns

Reference for all 14 available MCP tools, their parameters, and usage patterns.

## Shared Parameters

Most tools accept these optional parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `projectRef` | Project ref (proj_xxx), auto-detected from trigger.config.ts | Auto |
| `configPath` | Path to trigger.config.ts (for monorepos) | Auto |
| `environment` | dev, staging, prod, preview | dev |
| `branch` | Branch name (required with preview environment) | — |

## Project & Organization Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-list_orgs` | List your organizations | — |
| `tds-list_projects` | List your projects | — |
| `tds-create_project_in_org` | Create a new project | `orgParam`, `name` (required) |
| `tds-initialize_project` | Init Trigger.dev in a directory | `orgParam`, `projectName`, `cwd` (required) |

### List Organizations

```
Tool: tds-list_orgs
Input: {}
→ [{slug: "my-org", id: "org_xxx"}]
```

### Create Project

```
Tool: tds-create_project_in_org
Input: {
  "orgParam": "my-org-slug",
  "name": "My Background Jobs"
}
→ {ref: "proj_xxx", name: "My Background Jobs"}
```

### Initialize in Directory

```
Tool: tds-initialize_project
Input: {
  "orgParam": "my-org",
  "projectName": "email-jobs",
  "cwd": "/path/to/your/project"
}
→ Creates trigger.config.ts, src/trigger/ directory, installs SDK
```

## Worker & Task Discovery

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-get_current_worker` | Get worker info, task list, payload schemas | `environment` |

### Get Current Worker

```
Tool: tds-get_current_worker
Input: {"environment": "dev"}
→ {
    version: "20250225.1",
    tasks: [{
      id: "hello-world",
      payloadSchema: {type: "object", properties: {...}},
      machine: "small-1x",
      queue: {name: "default", concurrencyLimit: 10}
    }]
  }
```

Always call this before triggering tasks to verify task IDs and payload schemas.

## Task Execution Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-trigger_task` | Trigger a task with payload | `taskId`, `payload` (required) |
| `tds-wait_for_run_to_complete` | Wait for a run to finish | `runId` (required), `timeoutInSeconds` |
| `tds-cancel_run` | Cancel a running/queued run | `runId` (required) |

### Trigger a Task

```
Tool: tds-trigger_task
Input: {
  "taskId": "process-order",
  "payload": {"orderId": "ORD-123", "items": ["item-1"]},
  "environment": "prod",
  "options": {
    "tags": ["priority", "vip"],
    "idempotencyKey": "order-ORD-123",
    "machine": "medium-1x",
    "maxAttempts": 5,
    "maxDuration": 300,
    "delay": "5m",
    "ttl": "30m",
    "queue": {"name": "high-priority"}
  }
}
→ {id: "run_abc123", status: "QUEUED"}
```

### Trigger Options Reference

| Option | Type | Description |
|--------|------|-------------|
| `delay` | string/datetime | Delay before execution ("5m", "2h", ISO datetime) |
| `tags` | string[] | Up to 5 tags, each < 128 chars |
| `machine` | enum | Machine preset (micro to large-2x) |
| `maxAttempts` | integer | Max retry attempts |
| `maxDuration` | number | Max run duration in seconds |
| `ttl` | string/integer | Time-to-live before auto-cancel (default "10m") |
| `idempotencyKey` | string | Prevent duplicate runs |
| `queue` | object | Override queue `{name: "..."}` |

### Wait for Completion

```
Tool: tds-wait_for_run_to_complete
Input: {
  "runId": "run_abc123",
  "timeoutInSeconds": 120
}
→ {status: "COMPLETED", output: {processed: true}}
```

### Cancel a Run

```
Tool: tds-cancel_run
Input: {
  "runId": "run_abc123",
  "environment": "prod"
}
```

## Run Monitoring Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-list_runs` | List and filter runs | `status`, `taskIdentifier`, `tag`, `period` |
| `tds-get_run_details` | Get run trace, logs, output | `runId` (required), `maxTraceLines` |

### List Runs with Filters

```
Tool: tds-list_runs
Input: {
  "environment": "prod",
  "status": "FAILED",
  "taskIdentifier": "process-order",
  "period": "7d",
  "limit": 20
}
```

### Run Filters Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | enum | QUEUED, EXECUTING, COMPLETED, FAILED, CRASHED, etc. |
| `taskIdentifier` | string | Filter by task ID |
| `tag` | string | Filter by tag |
| `version` | string | Filter by worker version |
| `machine` | enum | Filter by machine preset |
| `period` | string | "1d", "7d", "30d" |
| `from` / `to` | ISO datetime | Custom time range |
| `limit` | integer | Max 100 |
| `cursor` | string | Pagination cursor (run_xxx) |

### Get Run Details

```
Tool: tds-get_run_details
Input: {
  "runId": "run_abc123",
  "environment": "prod",
  "maxTraceLines": 500
}
→ {status, error, trace: [...], output: {...}}
```

## Deployment Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-deploy` | Deploy to environment | `environment` (required) |
| `tds-list_deploys` | List deployments | `environment`, `status`, `period` |
| `tds-list_preview_branches` | List preview branches | — |

### Deploy

```
Tool: tds-deploy
Input: {
  "environment": "prod",
  "skipPromotion": false
}
→ {status: "DEPLOYED", version: "20250225.3"}
```

### List Deployments

```
Tool: tds-list_deploys
Input: {
  "environment": "prod",
  "status": "DEPLOYED",
  "limit": 5
}
```

## Documentation

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `tds-search_docs` | Search Trigger.dev documentation | `query` (required) |

```
Tool: tds-search_docs
Input: {"query": "wait for token human in the loop"}
```

## Common Patterns

### Trigger → Wait → Report

```
1. tds-get_current_worker(environment) → find task + schema
2. tds-trigger_task(taskId, payload) → get run_xxx
3. tds-wait_for_run_to_complete(runId) → get result
```

### Debug Failures

```
1. tds-list_runs(status="FAILED", period="1d")
2. tds-get_run_details(runId, maxTraceLines=500)
3. tds-search_docs(query="<error topic>")
```

### Deploy Flow

```
1. tds-deploy(environment="staging")
2. tds-trigger_task(environment="staging") → test
3. tds-deploy(environment="prod")
4. tds-list_deploys(environment="prod", limit=1) → verify
```

## Best Practices

- Always check task schemas with `tds-get_current_worker` before triggering
- Use `limit` and `period` to avoid fetching too many runs
- Use `idempotencyKey` to prevent duplicate runs
- Use `tags` for filtering and organizing runs
- Default to dev environment for safety
- For monorepos, always pass `configPath`
