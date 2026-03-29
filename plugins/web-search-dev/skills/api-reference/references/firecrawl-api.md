# Firecrawl REST API

Base URL: `https://api.firecrawl.dev`

## Scrape a Page

```bash
curl -s -X POST https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "formats": ["markdown", "links"],
    "onlyMainContent": true
  }' | jq .
```

With JS rendering wait:
```bash
curl -s -X POST https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/spa",
    "formats": ["markdown"],
    "waitFor": 3000
  }' | jq .
```

## Search the Web

```bash
curl -s -X POST https://api.firecrawl.dev/v1/search \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Next.js server components tutorial",
    "limit": 10
  }' | jq .
```

## Start a Crawl

```bash
curl -s -X POST https://api.firecrawl.dev/v1/crawl \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com",
    "limit": 50,
    "maxDepth": 3,
    "includePaths": ["/docs/*"],
    "scrapeOptions": {
      "formats": ["markdown"]
    }
  }' | jq .
```

Returns `{ "id": "crawl-job-id" }`. Check status:

```bash
curl -s https://api.firecrawl.dev/v1/crawl/${CRAWL_ID} \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" | jq .
```

## Map Site URLs

```bash
curl -s -X POST https://api.firecrawl.dev/v1/map \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "limit": 100
  }' | jq .
```

## Extract Structured Data

```bash
curl -s -X POST https://api.firecrawl.dev/v1/extract \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/pricing"],
    "prompt": "Extract pricing plans",
    "schema": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "plan": { "type": "string" },
          "price": { "type": "string" },
          "features": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }' | jq .
```

## Start Research Agent

```bash
curl -s -X POST https://api.firecrawl.dev/v1/agent \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find the top 5 headless CMS platforms and compare their pricing",
    "model": "spark-1-mini"
  }' | jq .
```

## Batch Scrape

```bash
curl -s -X POST https://api.firecrawl.dev/v1/batch/scrape \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/page1",
      "https://example.com/page2",
      "https://example.com/page3"
    ],
    "formats": ["markdown"]
  }' | jq .
```

## Error Codes

| Code | Meaning |
|------|---------|
| 401 | Missing or invalid API key |
| 402 | Payment required (insufficient credits) |
| 429 | Rate limit exceeded |
| 500 | Server error |
