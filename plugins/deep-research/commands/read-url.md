---
description: Read and extract content from a URL with fallback
argument-hint: <url> [--format <markdown|json|screenshot>]
---

# Read URL

Read and extract content from a web page or PDF. See CONNECTORS.md for provider mapping.

## Process

1. **Detect content type** from URL:
   - `.pdf` → use PDF extraction
   - Regular URL → use ~~scrape with fallback

2. **Read content** with fallback (~~scrape):
   ```
   Try each provider: Jina → Firecrawl
   On error → next provider automatically
   ```

3. **Optional extras:**
   - `--format screenshot` → capture page screenshot
   - `--format json` → structured JSON extraction
   - Check publish date → detect page date

4. **Display** extracted content with source URL and date.

## Example Usage
```
/read-url https://example.com/article
/read-url https://arxiv.org/pdf/2301.00001
/read-url https://spa-app.com/page --format screenshot
```
