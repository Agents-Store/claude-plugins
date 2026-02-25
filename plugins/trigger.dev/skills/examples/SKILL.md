---
name: examples
description: MCP tool call patterns, end-to-end workflow examples, code templates, and configuration references. Use when you need reference implementations for Trigger.dev operations.
---

# Examples & Patterns Repository

This skill contains reusable examples and patterns for Trigger.dev MCP operations.

## Available Examples

### MCP Tool Examples
| File | Description |
|------|-------------|
| @references/mcp/tool-patterns.md | Common MCP tool call patterns and flows |
| @references/mcp/trigger-dev-examples.md | End-to-end workflow examples |

### Code Templates
| File | Description |
|------|-------------|
| @references/code/task-templates.md | Task code templates for common use cases |
| @references/code/trigger-config.md | trigger.config.ts configuration reference |

## Quick Reference Patterns

### Initialize New Project
```
1. tds-list_orgs() -> Pick org
2. tds-initialize_project(orgParam, projectName, cwd)
3. tds-get_current_worker(environment="dev") -> Verify
```

### Trigger and Monitor
```
1. tds-get_current_worker() -> Find task + schema
2. tds-trigger_task(taskId, payload) -> Get run ID
3. tds-wait_for_run_to_complete(runId) -> Get result
```

### Debug Failures
```
1. tds-list_runs(status="FAILED", period="1d")
2. tds-get_run_details(runId) -> Read trace
3. Fix code, redeploy
4. tds-trigger_task(taskId, payload) -> Retry
```

### Deploy to Production
```
1. tds-deploy(environment="staging") -> Test first
2. tds-trigger_task(environment="staging") -> Verify
3. tds-deploy(environment="prod") -> Ship it
4. tds-list_deploys(environment="prod", limit=1) -> Confirm
```

## Conventions

- All examples are copy-paste ready for MCP tool calls
- Use `tds-search_docs` when documentation is needed for context
- Environment defaults: dev for development, prod for production
- Run IDs start with `run_`, project refs start with `proj_`
