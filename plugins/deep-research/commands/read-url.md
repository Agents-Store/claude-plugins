---
description: Read and extract content from a URL with fallback
allowed-tools: ["read_url", "firecrawl_scrape", "parallel_read_url", "extract_pdf", "guess_datetime_url", "capture_screenshot_url"]
argument-hint: <url> [--format <markdown|json|screenshot>]
---

# Read URL

Read and extract content from a web page or PDF.

## Process

1. **Detect content type** from URL:
   - `.pdf` → use `extract_pdf`
   - Regular URL → use `read_url` with fallback

2. **Read content** with fallback:
   ```
   read_url({ url: "$ARGUMENTS" })
   → If error: firecrawl_scrape({ url: "$ARGUMENTS", formats: ["markdown"], onlyMainContent: true })
   → If error: parallel_read_url({ urls: ["$ARGUMENTS"] })
   ```

3. **Optional extras:**
   - `--format screenshot` → `capture_screenshot_url({ url: "$ARGUMENTS" })`
   - `--format json` → `firecrawl_scrape({ url: "$ARGUMENTS", formats: ["json"] })`
   - Check publish date: `guess_datetime_url({ url: "$ARGUMENTS" })`

4. **Display** extracted content with source URL and date.

## Example Usage
```
/read-url https://example.com/article
/read-url https://arxiv.org/pdf/2301.00001
/read-url https://spa-app.com/page --format screenshot
```
