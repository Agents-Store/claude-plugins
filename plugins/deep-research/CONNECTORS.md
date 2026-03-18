# Connectors

## How tool references work

Plugin files use `~~capability` as a placeholder for whatever tool handles that action. For example, `~~search` means "use any available web search tool" — the agent tries providers in fallback order until one succeeds.

Plugins are **tool-agnostic** — they describe workflows in terms of actions (`~~search`, `~~scrape`, `~~crawl`) rather than specific tool names. The `.mcp.json` pre-configures MCP servers, but any server providing these capabilities works.

## FALLBACK Rule

Every action goes through ALL available providers for that category, one by one:
1. Try provider 1 — if it works, use the result
2. If error, empty result, rate limit, or timeout — try provider 2
3. If error — try provider 3
4. Continue until one succeeds or all are exhausted
5. Only report "not found" when ALL providers failed

**Error from a provider = skip it, try the next one. Never stop at first failure.**

## Connectors for this plugin

| Category | Placeholder | Included servers | Other options |
|----------|-------------|-----------------|---------------|
| Web search | `~~search` | Exa, Perplexity, Jina, Firecrawl | Tavily, Brave Search, SerpAPI |
| Scrape / read page | `~~scrape` | Jina, Firecrawl | Browserbase, Apify |
| Parallel search | `~~batch_search` | Jina, Exa, Perplexity | — |
| Parallel scrape | `~~batch_scrape` | Jina, Firecrawl | — |
| Crawl site | `~~crawl` | Firecrawl | — |
| Structured extraction | `~~extract` | Firecrawl | — |
| Academic papers | `~~academic_search` | Jina (arXiv, SSRN), Perplexity | Semantic Scholar |
| Code search | `~~code_search` | Exa | — |

## General workflow

```
Step 1: SEARCH — find pages on the internet
  → Use ~~search on every available provider, one by one
  → First success = take the URLs
  → Provider error = skip, next provider

Step 2: SCRAPE — read the found pages
  → Use ~~scrape on every available provider, one by one
  → First success = take the content
  → Provider error = skip, next provider
```

This same pattern applies to every capability: crawl, extract, academic_search, code_search.

## Utility tools (unique per provider, no fallback needed)

| Category | Placeholder | Included servers |
|----------|-------------|-----------------|
| Query expansion | `expand_query` | Jina |
| Text classification | `classify_text` | Jina |
| Relevance ranking | `sort_by_relevance` | Jina |
| Deduplication (text) | `deduplicate_strings` | Jina |
| Deduplication (images) | `deduplicate_images` | Jina |
| PDF extraction | `extract_pdf` | Jina |
| Screenshots | `capture_screenshot_url` | Jina |
| Page date detection | `guess_datetime_url` | Jina |
| Image search | `search_images` | Jina |
| BibTeX citations | `search_bibtex` | Jina |
| Autonomous agent | `firecrawl_agent` | Firecrawl |
| Browser automation | `firecrawl_browser_*` | Firecrawl |

## Available MCP servers

| Server | Included in `.mcp.json` | Provides |
|--------|------------------------|----------|
| Exa | Yes | search, code_search |
| Perplexity | Yes | search (AI answers with citations) |
| Jina | Yes | search, scrape, batch_search, batch_scrape, academic_search, utilities |
| Firecrawl | Yes | search, scrape, crawl, extract, browser automation |
