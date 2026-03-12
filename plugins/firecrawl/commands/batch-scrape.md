---
description: Batch scrape multiple URLs at once
allowed-tools: ["mcp__firecrawl__batch_scrape", "mcp__firecrawl__check_batch_status"]
argument-hint: <url1> <url2> [url3] ... [--format <markdown|html>]
---

# Batch Scrape

Scrape multiple URLs in a single request with rate limiting and progress tracking.

## Arguments
Format: `<url1> <url2> [url3] ... [--format <markdown|html>]`
- urls: One or more URLs to scrape (required, space-separated)
- --format: Output format — markdown (default) or html (optional)

Parse from "$ARGUMENTS".

## Process

1. **Start batch scrape:**
   Use `batch_scrape` with the list of URLs and format options.

2. **Monitor progress:**
   Use `check_batch_status` to poll until complete.

3. **Present results:**
   Show summary of scraped content for each URL.

## Example Usage
```
/batch-scrape https://example.com/page1 https://example.com/page2 https://example.com/page3
/batch-scrape https://docs.example.com/intro https://docs.example.com/guide --format markdown
```
