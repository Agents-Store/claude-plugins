# Exa MCP Tools (4 tools)

Exa excels at **semantic search** — finding pages by meaning, not just keywords. Best for code examples, documentation, and category-specific searches.

## web_search_exa
General web search with semantic understanding.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `numResults` | integer | No | Results to return (1-100, default: 10) |
| `type` | string | No | `auto`, `fast`, `instant`, `deep`, `deep-reasoning` |
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

## get_code_context_exa
Find code examples, documentation, and programming solutions. Optimized for developer queries.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Code or programming query |
| `numResults` | integer | No | Results to return |

```
Tool: get_code_context_exa
Input: {
  "query": "TypeScript Prisma ORM pagination example",
  "numResults": 5
}
```

Best for: finding code snippets, library usage examples, API implementation patterns.

## crawling_exa
Read full page content as clean markdown from a known URL.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | URL to read |
| `maxCharacters` | integer | No | Max characters to return |

```
Tool: crawling_exa
Input: {
  "url": "https://nextjs.org/docs/app/building-your-application/data-fetching",
  "maxCharacters": 50000
}
```

## web_search_advanced_exa
Advanced search with full filter control. May need to be enabled via MCP URL parameter.

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

## Pricing Notes

| Operation | Cost |
|-----------|------|
| Search (1-10 results) | $0.007 |
| Each additional result | $0.001 |
| Deep search | $0.012 |
| Content text per page | $0.001 |
| Content summary per page | $0.001 |

MCP has a free tier with rate limits. Add your API key for higher limits.
