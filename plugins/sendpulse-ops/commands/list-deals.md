---
description: List CRM deals with optional pipeline filter
allowed-tools: mcp__sendpulse__crm_deals_list, mcp__sendpulse__crm_pipelines_list
argument-hint: [--pipeline <id>] [--limit <number>]
---

# List Deals

List CRM deals, optionally filtered by pipeline.

## Arguments
Format: `[--pipeline <id>] [--limit <number>]`
- --pipeline: Filter by pipeline ID (optional)
- --limit: Number of deals to return (default: 50)

Parse from "$ARGUMENTS".

## Process

1. **If pipeline filter requested but no ID, list pipelines:**
   ```
   crm_pipelines_list()
   ```
   Ask user to select.

2. **List deals:**
   ```
   crm_deals_list(limit=<limit>, offset=0)
   ```

3. **Display as table:**
   - Deal name
   - Amount
   - Pipeline stage
   - Contact
   - ID

## Example Usage
```
/list-deals
/list-deals --pipeline pipe_001
/list-deals --limit 10
```

## Notes
- Default limit is 50
- Shows deal name, amount, and current pipeline stage
