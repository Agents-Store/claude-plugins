---
description: Crawl a website
allowed-tools: ["mcp__firecrawl__crawl_site", "mcp__firecrawl__get_crawl_status"]
argument-hint: <url> [--max-pages <n>] [--include <pattern>]
---

# Crawl Site

Start crawling a website and monitor progress.

## Arguments
Format: `<url> [--max-pages <n>] [--include <pattern>]`
- url: Starting URL to crawl (required)
- --max-pages: Maximum pages to crawl, default 50 (optional)
- --include: URL pattern to include, e.g. "/blog/*" (optional)

Parse from "$ARGUMENTS".

## Process

1. **Start crawl:**
   ```
   crawl_site({
     url: <url>,
     max_pages: <max or 50>,
     include_patterns: [<pattern>]
   })
   ```

2. **Monitor progress:**
   ```
   get_crawl_status(crawl_id)
   ```
   Report pages crawled, status, and when complete.

3. **Display results summary:**
   Show total pages crawled, URLs found, and content summary.

## Example Usage
```
/crawl-site "https://example.com"
/crawl-site "https://example.com" --max-pages 100 --include "/docs/*"
```
