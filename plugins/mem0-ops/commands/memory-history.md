---
description: View the change history of a memory
allowed-tools: ["get_memory_history", "get_memory"]
argument-hint: <memory_id>
---

# Memory History

View the complete change history of a memory over time.

## Process

1. **Get current state:**
   ```
   get_memory({ memory_id: "<memory_id>" })
   ```

2. **Get change history:**
   ```
   get_memory_history({ memory_id: "<memory_id>" })
   ```

3. **Display timeline** of changes with timestamps and old/new values.

## Example Usage
```
/memory-history abc123-def456
```
