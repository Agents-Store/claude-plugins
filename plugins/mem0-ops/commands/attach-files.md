---
description: Attach files to an existing memory
allowed-tools: ["attach_files_to_memory", "get_memory"]
argument-hint: <memory_id> --user <user_id> --files <file1,file2,...>
---

# Attach Files

Attach files to an existing memory for vector search.

## Process

1. **Verify memory exists:**
   ```
   get_memory({ memory_id: "<memory_id>" })
   ```

2. **Attach files:**
   ```
   attach_files_to_memory({
     memory_id: "<memory_id>",
     user_id: "<user_id>",
     files: [
       { "filename": "<file1>", "content": "<content>" }
     ]
   })
   ```

3. **Confirm attachment** with file count.

## Example Usage
```
/attach-files abc123 --user 456 --files design-doc.md,api-spec.yaml
```
