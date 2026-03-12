---
description: List recent workflow executions
allowed-tools: ["mcp__n8n__list_executions", "mcp__n8n__list_workflows"]
argument-hint: "[--workflow <name>] [--status <success|error|waiting>] [--limit <n>]"
---

# List Executions

List recent workflow executions with optional filters.

## Arguments
Format: `[--workflow <name>] [--status <success|error|waiting>] [--limit <n>]`
- --workflow: Filter by workflow name or ID (optional)
- --status: Filter by status — success, error, waiting (optional)
- --limit: Max results, default 20 (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve workflow if specified:**
   ```
   list_workflows()
   ```

2. **List executions:**
   ```
   list_executions({
     workflow_id: <id or empty>,
     status: <status or empty>,
     limit: <limit or 20>
   })
   ```

3. **Display results:**
   Show execution ID, workflow name, status, start time, and duration.

## Example Usage
```
/list-executions
/list-executions --workflow "Data Sync" --status error
/list-executions --limit 50
```
