---
description: Update an existing memory's content
allowed-tools: ["update_memory", "get_memory"]
argument-hint: <memory_id> "<new content>"
---

# Update Memory

Update the content of an existing memory.

## Process

1. **Show current content** (optional):
   ```
   get_memory({ memory_id: "<memory_id>" })
   ```

2. **Update memory:**
   ```
   update_memory({
     memory_id: "<memory_id>",
     data: "<new content>"
   })
   ```

3. **Confirm update** by showing the updated memory.

## Example Usage
```
/update-memory abc123-def456 "Updated: project now uses PostgreSQL 16"
```
