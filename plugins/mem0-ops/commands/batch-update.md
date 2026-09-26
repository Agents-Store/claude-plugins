---
description: Batch update multiple memories at once (up to 100)
allowed-tools: ["batch_update_memories", "search_memories"]
argument-hint: <memory_id1>="<text>" <memory_id2>="<text>" ...
---

# Batch Update

Update multiple memories in a single operation (max 100).

## Process

1. **Parse memory ID and content pairs.**

2. **Execute batch update:**
   ```
   batch_update_memories({
     memories: [
       { "memory_id": "<id1>", "data": "<new content 1>" },
       { "memory_id": "<id2>", "data": "<new content 2>" }
     ]
   })
   ```

3. **Report results** with count of updated memories.

## Example Usage
```
/batch-update id1="Updated fact 1" id2="Updated fact 2"
```
