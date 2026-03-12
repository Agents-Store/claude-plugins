---
description: Search the web
allowed-tools: ["mcp__firecrawl__search"]
argument-hint: <query> [--limit <n>]
---

# Search

Search the web and get results with page content.

## Arguments
Format: `<query> [--limit <n>]`
- query: Search query (required)
- --limit: Max results, default 5 (optional)

Parse from "$ARGUMENTS".

## Process

1. **Search:**
   ```
   search({
     query: <query>,
     limit: <limit or 5>,
     lang: <language if specified>,
     country: <country if specified>
   })
   ```

2. **Display results:**
   Show title, URL, and content snippet for each result in a formatted table.

3. **Suggest follow-ups:**
   - Scrape specific results for full content
   - Extract structured data from results
   - Narrow search with filters

## Advanced Options
- `--lang <code>` — filter by language (e.g., "en", "de", "ru")
- `--country <code>` — filter by country (e.g., "us", "uk", "de")

## Example Usage
```
/search "best practices for API design"
/search "n8n workflow examples" --limit 10
/search "machine learning frameworks 2024" --lang en --country us
```
