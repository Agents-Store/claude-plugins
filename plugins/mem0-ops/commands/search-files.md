---
description: Search attached files via vector search
allowed-tools: ["get_memory_files"]
argument-hint: "<query>" --user <user_id> [--file <filename>] [--limit <n>]
---

# Search Files

Search through attached files using vector search.

## Process

1. **Run file search:**
   ```
   get_memory_files({
     user_id: <user_id>,
     search_query: "<query>",
     file_name: "<filename if provided>",
     limit: <limit or 5>
   })
   ```

2. **Display matching results** with file names and relevant content snippets.

## Example Usage
```
/search-files "authentication flow" --user 123
/search-files "database schema" --user 123 --file architecture.pdf --limit 10
```
