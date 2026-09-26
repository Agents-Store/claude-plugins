---
description: List all stored memories with optional pagination
allowed-tools: ["get_all_memories"]
argument-hint: [--user <user_id>] [--limit <n>] [--page <n>]
---

# List Memories

List all stored memories with pagination support.

## Process

1. **Get all memories:**
   ```
   get_all_memories({
     user_id: "<user_id if provided>",
     limit: <limit or 20>,
     page: <page or 1>,
     page_size: <limit or 20>
   })
   ```

2. **Display results** in a table with ID, content summary, and creation date.

## Example Usage
```
/list-memories
/list-memories --user project-alpha --limit 50
/list-memories --page 2
```
