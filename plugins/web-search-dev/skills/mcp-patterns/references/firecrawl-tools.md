# Firecrawl MCP Tools (12 tools)

## Scraping

### firecrawl_scrape
Scrape a single URL and extract content in multiple formats.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | URL to scrape |
| `formats` | string[] | No | Output formats: `markdown`, `html`, `rawHtml`, `screenshot`, `links`, `json`, `changeTracking` |
| `onlyMainContent` | boolean | No | Extract only main content (default: true) |
| `waitFor` | integer | No | Wait for JS rendering (ms) |
| `includeTags` | string[] | No | Only include these HTML tags |
| `excludeTags` | string[] | No | Exclude these HTML tags |
| `jsonOptions` | object | No | Schema for structured JSON extraction |
| `actions` | array | No | Page interactions: click, type, scroll, wait, screenshot |

```
Tool: firecrawl_scrape
Input: {
  "url": "https://example.com/page",
  "formats": ["markdown", "links"],
  "onlyMainContent": true
}
```

### firecrawl_search
Search the web and optionally scrape results.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `limit` | integer | No | Max results (default: 5) |
| `lang` | string | No | Language code |
| `country` | string | No | Country code |
| `scrapeOptions` | object | No | Options for scraping each result |
| `tbs` | string | No | Time filter |
| `location` | string | No | Geographic location |

```
Tool: firecrawl_search
Input: {
  "query": "Next.js server components tutorial",
  "limit": 10
}
```

## Crawling

### firecrawl_crawl
Start an async crawl of an entire website.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Starting URL |
| `limit` | integer | No | Max pages to crawl |
| `maxDepth` | integer | No | Max crawl depth |
| `includePaths` | string[] | No | Only crawl matching paths |
| `excludePaths` | string[] | No | Skip matching paths |
| `allowSubdomains` | boolean | No | Include subdomains |
| `scrapeOptions` | object | No | Options for each scraped page |

Returns a `jobId` — check status with `firecrawl_check_crawl_status`.

```
Tool: firecrawl_crawl
Input: {
  "url": "https://docs.example.com",
  "limit": 50,
  "maxDepth": 3,
  "includePaths": ["/docs/*"]
}
```

### firecrawl_check_crawl_status
Poll a crawl job for results.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Crawl job ID from firecrawl_crawl |

### firecrawl_map
Discover all URLs on a website (fast, no content extraction).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Website URL |
| `limit` | integer | No | Max URLs to return |
| `includeSubdomains` | boolean | No | Include subdomains |
| `search` | string | No | Filter URLs by keyword |

```
Tool: firecrawl_map
Input: { "url": "https://example.com", "limit": 100 }
```

## Extraction

### firecrawl_extract
Extract structured data from web pages using LLM.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | string[] | Yes | URLs to extract from |
| `prompt` | string | No | Natural language extraction instructions |
| `schema` | object | No | JSON schema for output structure |
| `enableWebSearch` | boolean | No | Allow web search to find additional data |

```
Tool: firecrawl_extract
Input: {
  "urls": ["https://example.com/pricing"],
  "prompt": "Extract all pricing plans with name, price, and features",
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
}
```

## Agent

### firecrawl_agent
Start an autonomous web research agent.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Research task description |
| `urls` | string[] | No | Starting URLs |
| `model` | string | No | `spark-1-mini` (default) or `spark-1-pro` |
| `maxCredits` | integer | No | Credit limit for the task |
| `schema` | object | No | JSON schema for structured output |

Returns a `jobId` — check with `firecrawl_agent_status`.

### firecrawl_agent_status
Check agent job status and retrieve results.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Agent job ID |

## Browser Sessions

### firecrawl_browser_create
Create a persistent browser session via CDP.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ttl` | integer | No | Session TTL in seconds |

Returns `sessionId` and `wsUrl` for the browser session.

### firecrawl_browser_execute
Execute code in a browser session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sessionId` | string | Yes | Browser session ID |
| `code` | string | Yes | Code to execute (Python Playwright, JS, or bash) |

### firecrawl_browser_list
List all active browser sessions.

### firecrawl_browser_delete
Destroy a browser session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sessionId` | string | Yes | Session to delete |
