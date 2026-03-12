---
description: Map a site's URL structure
allowed-tools: ["mcp__firecrawl__map_site"]
argument-hint: <url>
---

# Map Site

Discover all URLs on a website.

## Arguments
Format: `<url>`
- url: Site URL to map (required)

Parse from "$ARGUMENTS".

## Process

1. **Map the site:**
   ```
   map_site({ url: <url> })
   ```

2. **Present results:**
   - Total URL count
   - URL tree organized by path segments
   - Key sections identified (blog, docs, pricing, etc.)
   - Suggest include/exclude patterns for focused crawling

3. **Suggest next steps:**
   - Use `/crawl-site` with include patterns for specific sections
   - Use `/batch-scrape` for a curated list of important URLs

## Example Usage
```
/map-site "https://example.com"
/map-site "https://docs.stripe.com"
```
