---
description: Activate or deactivate an n8n workflow
allowed-tools: ["mcp__n8n__activate_workflow", "mcp__n8n__deactivate_workflow", "mcp__n8n__list_workflows"]
argument-hint: <workflow> [--off]
---

# Activate Workflow

Activate a workflow (or deactivate with --off flag).

## Arguments
Format: `<workflow> [--off]`
- workflow: Workflow name or ID (required)
- --off: Deactivate instead of activate (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve workflow:**
   ```
   list_workflows()
   ```

2. **Toggle activation:**
   ```
   activate_workflow(workflow_id)   // or deactivate_workflow if --off
   ```

3. **Confirm status change.**

## Example Usage
```
/activate-workflow "Data Sync"
/activate-workflow "API Handler" --off
```
