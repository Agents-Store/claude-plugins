---
description: Search memories by semantic query
allowed-tools: ["search_memories"]
argument-hint: "<query>" [--user <user_id>] [--limit <n>]
---

# Search Memories

Find memories using semantic search.

## Process

1. **Run semantic search:**
   ```
   search_memories({
     query: "<search query>",
     user_id: "<user_id if provided>",
     top_k: <limit or 10>
   })
   ```

2. **Display results** in a table with ID, content snippet, and relevance score.

## Example Usage
```
/search-memories API authentication
/search-memories database schema --user project-alpha --limit 5
```
