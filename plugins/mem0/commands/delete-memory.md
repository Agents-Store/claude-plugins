---
description: Delete a memory by its ID
allowed-tools: ["delete_memory", "get_memory"]
argument-hint: <memory_id>
---

# Delete Memory

Delete a specific memory permanently.

## Process

1. **Show memory to be deleted:**
   ```
   get_memory({ memory_id: "<memory_id>" })
   ```

2. **Confirm with user** before deleting.

3. **Delete memory:**
   ```
   delete_memory({ memory_id: "<memory_id>" })
   ```

## Example Usage
```
/delete-memory abc123-def456
```
