---
description: Create a new n8n workflow
allowed-tools: ["mcp__n8n__create_workflow"]
argument-hint: <name> [--trigger <webhook|schedule|manual>]
---

# Create Workflow

Create a new workflow in n8n.

## Arguments
Format: `<name> [--trigger <webhook|schedule|manual>]`
- name: Workflow name (required)
- --trigger: Trigger type — webhook, schedule, or manual (default: manual)

Parse from "$ARGUMENTS".

## Process

1. **Create workflow with trigger:**
   ```
   create_workflow({
     name: <name>,
     nodes: [<trigger_node based on type>],
     connections: {}
   })
   ```

2. **Display result:**
   Show workflow ID, name, and trigger configuration.

## Example Usage
```
/create-workflow "Data Sync"
/create-workflow "API Handler" --trigger webhook
/create-workflow "Daily Report" --trigger schedule
```
