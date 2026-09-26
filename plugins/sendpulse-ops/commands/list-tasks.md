---
description: List CRM tasks
allowed-tools: mcp__sendpulse__crm_tasks_list
argument-hint: [--limit <number>]
---

# List Tasks

List CRM tasks from all boards.

## Arguments
Format: `[--limit <number>]`
- --limit: Number of tasks to return (default: 50)

Parse from "$ARGUMENTS".

## Process

1. **List tasks:**
   ```
   crm_tasks_list(limit=<limit>, offset=0)
   ```

2. **Display as table:**
   - Task name
   - Status/step
   - Due date
   - ID

## Example Usage
```
/list-tasks
/list-tasks --limit 20
```

## Notes
- Shows tasks from all boards
- Default limit is 50
