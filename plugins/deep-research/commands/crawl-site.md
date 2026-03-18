---
description: Crawl an entire website or map its structure
argument-hint: <url> [--depth <number>] [--limit <max-pages>] [--map-only]
---

# Crawl Site

Crawl a website to extract all pages or map its structure. See CONNECTORS.md for provider mapping.

## Process

1. **If --map-only:** get site structure only:
   ```
   ~~crawl(url, map_only: true)
   → Returns list of all URLs
   ```

2. **Otherwise:** full crawl with monitoring (~~crawl):
   ```
   ~~crawl(url, limit: <--limit or 20>, depth: <--depth or 3>)
   → Poll status until completed
   ```

3. **On timeout/error:** fallback to map + selective read:
   ```
   ~~crawl(url, map_only: true) → get URLs
   ~~batch_scrape(key_page_urls) → read selected pages
   ```

4. **Display** crawl results summary with page count and key content.

## Example Usage
```
/crawl-site https://docs.example.com
/crawl-site https://docs.example.com --limit 50 --depth 4
/crawl-site https://example.com --map-only
```
