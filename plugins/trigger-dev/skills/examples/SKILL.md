---
name: examples
description: Trigger.dev code examples, end-to-end workflow templates, MCP tool usage patterns, and scenario walkthroughs. Use when the user asks for "trigger.dev examples", "task templates", "MCP tool patterns", "trigger.dev workflow examples", or needs reference implementations.
---

# Examples & Patterns

Ready-to-use examples and complete workflow scenarios.

## MCP Tool Examples

| File | Description |
|------|-------------|
| @references/mcp/tool-patterns.md | Common MCP tool call patterns and workflows |

## Scenario Walkthroughs

| File | Description |
|------|-------------|
| @references/scenarios/webhook-processor.md | Complete webhook processing task with queue and retry |
| @references/scenarios/ai-pipeline.md | AI agent pipeline with chaining, tools, and streaming |
| @references/scenarios/cron-data-sync.md | Scheduled data sync with batch processing |

## Quick Reference Patterns

### Initialize New Project

```
1. list_orgs() → pick org
2. initialize_project(orgParam, projectName, cwd)
3. get_current_worker(environment="dev") → verify
```

### Trigger and Monitor

```
1. get_current_worker() → find task + schema
2. trigger_task(taskId, payload) → get run ID
3. wait_for_run_to_complete(runId) → get result
```

### Debug Failures

```
1. list_runs(status="FAILED", period="1d")
2. get_run_details(runId) → read trace
3. Fix code, redeploy
4. trigger_task(taskId, payload) → retry
```

### Deploy to Production

```
1. deploy(environment="staging") → test first
2. trigger_task(environment="staging") → verify
3. deploy(environment="prod") → ship it
4. list_deploys(environment="prod", limit=1) → confirm
```
