# Learnings

## 2026-09-26 — plugin: Plugin superseded by web-search-dev

**Problem:** The plugin teaches tool names (`scrape_url`, `crawl_site`, `map_site`, `extract_data`) that the official Firecrawl MCP server does not expose; its tools are `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_extract`. web-search-dev teaches the current names and Firecrawl REST API v2, plus Exa, Perplexity, Jina and Context7.
**Fix:** Marked DEPRECATED in `plugin.json` and `marketplace.json`, pointing at web-search-dev. Nothing removed.
**Root cause:** First-generation plugin (2026-03-12), not updated when Firecrawl renamed its MCP tools and moved the REST API to v2.
**Severity:** Minor
