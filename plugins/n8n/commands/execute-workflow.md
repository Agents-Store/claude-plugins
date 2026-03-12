---
description: Execute an n8n workflow
allowed-tools: ["mcp__n8n__execute_workflow", "mcp__n8n__list_workflows", "mcp__n8n__get_execution"]
argument-hint: <workflow> [--data <json>]
---

# Execute Workflow

Execute a workflow manually with optional input data.

## Arguments
Format: `<workflow> [--data <json>]`
- workflow: Workflow name or ID (required)
- --data: JSON input data for the trigger node (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve workflow:**
   ```
   list_workflows()
   ```
   Find workflow by name or ID.

2. **Execute:**
   ```
   execute_workflow({
     workflow_id: <resolved_id>,
     data: <parsed JSON or empty>
   })
   ```

3. **Get execution result:**
   ```
   get_execution(execution_id)
   ```
   Show execution status, duration, and node outputs.

## Example Usage
```
/execute-workflow "Data Sync"
/execute-workflow "API Handler" --data '{"name": "test", "value": 42}'
```
