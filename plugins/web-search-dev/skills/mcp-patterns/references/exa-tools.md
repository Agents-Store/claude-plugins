# Exa MCP Tools (2 default + 2 optional)

Exa excels at **semantic search** — finding pages by meaning, not just keywords. Best for documentation discovery and category-specific searches. The default MCP server exposes `web_search_exa` and `web_fetch_exa`; advanced search and the Exa Agent must be enabled explicitly (see below).

## web_search_exa
General web search with semantic understanding.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `numResults` | integer | No | Results to return (1-100, default: 10) |
| `type` | string | No | `auto`, `fast`, `instant`, `deep-lite`, `deep`, `deep-reasoning` |
| `category` | string | No | `company`, `people`, `research paper`, `news`, `personal site`, `financial report` |
| `includeDomains` | string[] | No | Only search these domains |
| `excludeDomains` | string[] | No | Exclude these domains |
| `startPublishedDate` | string | No | ISO 8601 start date filter |
| `endPublishedDate` | string | No | ISO 8601 end date filter |
| `includeText` | string[] | No | Must contain this text |
| `excludeText` | string[] | No | Must not contain this text |

```
Tool: web_search_exa
Input: {
  "query": "React server components best practices 2025",
  "numResults": 10,
  "type": "auto"
}
```

**Category filtering example** (company lookup):
```
Tool: web_search_exa
Input: {
  "query": "Vercel",
  "category": "company",
  "numResults": 5
}
```

**Domain-scoped search:**
```
Tool: web_search_exa
Input: {
  "query": "authentication middleware",
  "includeDomains": ["github.com", "stackoverflow.com"],
  "numResults": 15
}
```

**Important:** `category: "company"` and `category: "people"` disable date, text, and excludeDomains filters — using them together causes a 400 error.

## web_fetch_exa
Read one or more URLs as clean markdown. Replaces the old `crawling_exa` tool.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | URL(s) to read |
| `maxCharacters` | integer | No | Max characters to return |

```
Tool: web_fetch_exa
Input: {
  "url": "https://nextjs.org/docs/app/building-your-application/data-fetching",
  "maxCharacters": 50000
}
```

**Code/dev search:** the old `get_code_context_exa` tool no longer exists. Use `firecrawl_developer_search` (Firecrawl MCP) or `web_search_exa` with `includeDomains: ["github.com"]`. Exa's code vertical is available via the REST API only.

## Optional Tools (via remote MCP)

`web_search_advanced_exa` and the new `agent_run` (multi-step Exa Agent) are not served by default. Enable them via the remote MCP URL with a `tools` query parameter and `x-api-key` header:

```
https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa,agent_run
```

### web_search_advanced_exa
Advanced search with full filter control.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `numResults` | integer | No | Results count |
| `type` | string | No | Search type |
| `contents` | object | No | Content extraction options |
| `contents.text` | object | No | `{ maxCharacters, includeHtmlTags }` |
| `contents.highlights` | object | No | `{ maxCharacters, query }` |
| `contents.summary` | object | No | `{ query }` |

This tool combines search + content extraction in one call — useful when you need both results and page content.

### agent_run
Run a multi-step Exa Agent research task (backed by the Agent API `POST /agent/runs`).

## Pricing

See https://exa.ai/pricing for current pricing. MCP has a free tier with rate limits — add your API key for higher limits.
