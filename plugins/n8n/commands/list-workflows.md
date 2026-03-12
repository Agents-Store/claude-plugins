---
description: List all n8n workflows
allowed-tools: ["mcp__n8n__list_workflows"]
argument-hint: "[--active] [--tag <tag>]"
---

# List Workflows

List all workflows in the n8n instance.

## Arguments
Format: `[--active] [--tag <tag>]`
- --active: Show only active workflows (optional)
- --tag: Filter by tag name (optional)

Parse from "$ARGUMENTS".

## Process

1. **List workflows:**
   ```
   list_workflows()
   ```

2. **Display results:**
   Show ID, name, active status, and tags for each workflow. Filter by arguments if provided.

## Example Usage
```
/list-workflows
/list-workflows --active
/list-workflows --tag "production"
```
