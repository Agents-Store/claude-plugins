---
description: Debug a failed n8n workflow execution
allowed-tools: ["mcp__n8n__list_executions", "mcp__n8n__get_execution", "mcp__n8n__get_workflow"]
argument-hint: <workflow-id> [--execution <execution-id>]
---

# Debug Workflow

Debug a failed n8n workflow execution — find the failing node, error message, and suggest fixes.

## Arguments
Format: `<workflow-id> [--execution <execution-id>]`
- workflow-id: ID of the workflow to debug (required)
- --execution: Specific execution ID to debug (optional, defaults to last failed)

Parse from "$ARGUMENTS".

## Process

1. **Find failed executions:**
   Use `list_executions` with status="error" to find recent failures.

2. **Get execution details:**
   Use `get_execution` to see node-by-node data and identify the failing node.

3. **Get workflow structure:**
   Use `get_workflow` to understand the workflow configuration.

4. **Diagnose:**
   - Identify which node failed
   - What error message was returned
   - What input data the failing node received
   - Suggest fixes

## Example Usage
```
/debug-workflow wf_abc123
/debug-workflow wf_abc123 --execution exec_xyz789
```
