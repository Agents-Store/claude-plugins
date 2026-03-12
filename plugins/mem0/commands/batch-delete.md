---
description: Batch delete multiple memories at once (up to 100)
allowed-tools: ["batch_delete_memories", "get_all_memories"]
argument-hint: <memory_id1> <memory_id2> ...
---

# Batch Delete

Delete multiple memories in a single operation (max 100).

## Process

1. **Parse memory IDs** from arguments.

2. **Confirm with user** before deleting.

3. **Execute batch delete:**
   ```
   batch_delete_memories({
     memory_ids: ["<id1>", "<id2>", "<id3>"]
   })
   ```

4. **Report results** with count of deleted memories.

## Example Usage
```
/batch-delete abc123 def456 ghi789
```
