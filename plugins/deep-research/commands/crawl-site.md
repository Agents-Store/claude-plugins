---
description: Crawl an entire website or map its structure
allowed-tools: ["firecrawl_crawl", "firecrawl_check_crawl_status", "firecrawl_map", "parallel_read_url"]
argument-hint: <url> [--depth <number>] [--limit <max-pages>] [--map-only]
---

# Crawl Site

Crawl a website to extract all pages or map its structure.

## Process

1. **If --map-only:** get site structure only:
   ```
   firecrawl_map({ url: "$ARGUMENTS" })
   → Returns list of all URLs
   ```

2. **Otherwise:** full crawl with monitoring:
   ```
   firecrawl_crawl({
     url: "$ARGUMENTS",
     limit: <--limit or 20>,
     maxDiscoveryDepth: <--depth or 3>
   }) → crawl_id

   firecrawl_check_crawl_status({ id: crawl_id })
   → Repeat until status: "completed"
   ```

3. **On timeout/error:** fallback to map + selective read:
   ```
   firecrawl_map({ url: "$ARGUMENTS" })
   → Select key pages
   parallel_read_url(key_page_urls)
   ```

4. **Display** crawl results summary with page count and key content.

## Example Usage
```
/crawl-site https://docs.example.com
/crawl-site https://docs.example.com --limit 50 --depth 4
/crawl-site https://example.com --map-only
```
