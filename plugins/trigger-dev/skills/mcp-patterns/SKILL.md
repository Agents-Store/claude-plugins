---
name: mcp-patterns
description: Trigger.dev MCP tools reference — all available tools, parameters, usage patterns, and common workflows. Use when the user asks about "trigger.dev MCP tools", "which trigger.dev tools are available", "how to use trigger.dev MCP", "trigger task via MCP", "list runs MCP", or needs to know which MCP operations are available.
---

# Trigger.dev MCP Tool Patterns

Reference for all MCP tools provided by the official Trigger.dev MCP server.

> **Note:** This plugin provides MCP **knowledge**, not the MCP connection. Install the MCP server via `npx trigger.dev@latest mcp` or configure it manually in your project.

## Shared Parameters

Most tools accept these optional parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `projectRef` | Project ref (proj_xxx) | Auto-detected from trigger.config.ts |
| `configPath` | Path to trigger.config.ts | Auto |
| `environment` | dev, staging, prod, preview | dev |
| `branch` | Branch name (required with preview) | — |

## Project & Organization Tools

| Tool | Description |
|------|-------------|
| `list_orgs` | List your organizations |
| `list_projects` | List your projects |
| `create_project_in_org` | Create a new project in an org |
| `initialize_project` | Init Trigger.dev in a directory |

## Task Management Tools

| Tool | Description |
|------|-------------|
| `get_current_worker` | Get worker info, task list, payload schemas |
| `trigger_task` | Trigger a task with payload and options |

## Run Monitoring Tools

| Tool | Description |
|------|-------------|
| `list_runs` | List and filter runs by status, task, tag, period |
| `get_run_details` | Get run trace, logs, output |
| `wait_for_run_to_complete` | Wait for a run to finish |
| `cancel_run` | Cancel a running/queued run |

## Deployment Tools

| Tool | Description |
|------|-------------|
| `deploy` | Deploy to staging/production/preview |
| `list_deploys` | List deployments with filters |
| `list_preview_branches` | List preview branches |

## Documentation Tool

| Tool | Description |
|------|-------------|
| `search_docs` | Search Trigger.dev documentation |

## Common Patterns

### Trigger and Monitor

```
1. get_current_worker(environment="dev") → find task + schema
2. trigger_task(taskId, payload) → get run ID
3. wait_for_run_to_complete(runId) → get result
```

### Debug Failures

```
1. list_runs(status="FAILED", period="1d")
2. get_run_details(runId) → read error trace
3. search_docs(query="<error topic>")
```

### Deploy Flow

```
1. deploy(environment="staging")
2. trigger_task(environment="staging") → test
3. deploy(environment="prod")
4. list_deploys(environment="prod", limit=1) → verify
```

### Initialize Project

```
1. list_orgs() → pick org
2. initialize_project(orgParam, projectName, cwd)
3. get_current_worker(environment="dev") → verify
```

## Best Practices

- Always check task schemas with `get_current_worker` before triggering
- Use `limit` and `period` to avoid fetching too many runs
- Use `idempotencyKey` in trigger options to prevent duplicate runs
- Default to dev environment for safety
- For monorepos, always pass `configPath`

## Deeper Reference

- @references/mcp-tools-reference.md — complete parameter documentation + REST API
