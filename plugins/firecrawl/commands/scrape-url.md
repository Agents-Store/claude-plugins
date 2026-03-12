---
description: Scrape a single URL
allowed-tools: ["mcp__firecrawl__scrape_url"]
argument-hint: <url> [--format <markdown|html>]
---

# Scrape URL

Scrape a single URL and return its content.

## Arguments
Format: `<url> [--format <markdown|html>]`
- url: The URL to scrape (required)
- --format: Output format — markdown (default) or html (optional)

Parse from "$ARGUMENTS".

## Process

1. **Scrape the URL:**
   ```
   scrape_url({
     url: <url>,
     formats: [<format or "markdown">]
   })
   ```

2. **Display results:**
   Show page title, content summary, and metadata.

## Example Usage
```
/scrape-url "https://example.com/blog/article"
/scrape-url "https://example.com/products/123" --format html
```
