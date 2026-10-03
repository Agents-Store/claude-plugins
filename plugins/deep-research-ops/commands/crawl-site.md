---
description: Crawl an entire website or map its structure
argument-hint: <url> [--depth <number>] [--limit <max-pages>] [--map-only]
---

# Crawl Site

Crawl a website to extract all pages or map its structure. See CONNECTORS.md for provider mapping.

## Process

1. **If --map-only:** get site structure only (Firecrawl map, no page content):
   ```
   firecrawl_map(url, limit: <--limit or 100>)
   → Returns list of all URLs
   ```

2. **Otherwise:** full crawl (~~crawl):
   ```
   ~~crawl(url, limit: <--limit or 20>, depth: <--depth or 3>)
   → Waits for the crawl to finish and returns the pages
   → Crawl cut off? pick it up by its id with the crawl-status tool
   ```

3. **On timeout/error:** fallback to map + selective read:
   ```
   firecrawl_map(url) → get URLs
   ~~batch_scrape(key_page_urls) → read selected pages (≤5 per call)
   ```

4. **Display** crawl results summary with page count and key content.

## Example Usage
```
/crawl-site https://docs.example.com
/crawl-site https://docs.example.com --limit 50 --depth 4
/crawl-site https://example.com --map-only
```
