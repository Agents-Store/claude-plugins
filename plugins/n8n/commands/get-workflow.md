---
description: Get n8n workflow details
allowed-tools: ["mcp__n8n__get_workflow"]
argument-hint: <workflow-id>
---

# Get Workflow

Get detailed information about an n8n workflow — nodes, connections, settings, and active status.

## Arguments
Format: `<workflow-id>`
- workflow-id: ID of the workflow (required)

Parse from "$ARGUMENTS".

## Process

1. **Get workflow:**
   Use `get_workflow` to fetch full workflow data.

2. **Present details:**
   - Workflow name and active status
   - List of nodes with types
   - Connection map
   - Trigger type
   - Tags and settings

## Example Usage
```
/get-workflow wf_abc123
```
