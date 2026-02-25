---
description: Search Trigger.dev documentation
allowed-tools: mcp__trigger_dev__tds-search_docs
argument-hint: <search-query>
---

# Search Docs

Search the Trigger.dev documentation for guides, API references, and examples.

## Arguments
- search-query: What to search for

## Process

1. **Search documentation:**
   ```
   tds-search_docs(query="$ARGUMENTS")
   ```

2. **Display results:**
   - Show relevant documentation excerpts
   - Include titles and links to full pages
   - Highlight key code examples

## Example Usage
```
/search-docs how to set up scheduled tasks
/search-docs build extensions prisma
/search-docs wait for token human in the loop
/search-docs realtime API react hooks
/search-docs queue concurrency limit
/search-docs retry configuration
```

## Notes
- No authentication required for docs search
- Returns contextual content with direct links
- Useful for learning about features before implementing
