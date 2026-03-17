---
name: examples
description: Tool call patterns, end-to-end research workflow examples, and scenario references for all 6 research types. Use when you need reference implementations or complete research examples.
---

# Examples & References

Паттерны вызовов инструментов, многошаговые воркфлоу и полные сценарии исследований.

## Reference Files

| File | Description |
|------|-------------|
| [tool-patterns.md](references/mcp/tool-patterns.md) | Все 38 MCP tool call паттернов с параметрами |
| [workflow-examples.md](references/mcp/workflow-examples.md) | 5 многошаговых workflow-примеров |
| [competitive-analysis.md](references/scenarios/competitive-analysis.md) | Сценарий: сравнение конкурентов |
| [market-research.md](references/scenarios/market-research.md) | Сценарий: исследование рынка |
| [technical-audit.md](references/scenarios/technical-audit.md) | Сценарий: технический аудит |
| [person-company-lookup.md](references/scenarios/person-company-lookup.md) | Сценарий: поиск информации о компании/персоне |
| [topic-deep-dive.md](references/scenarios/topic-deep-dive.md) | Сценарий: глубокое изучение темы |
| [news-trends.md](references/scenarios/news-trends.md) | Сценарий: новости и тренды |

## Quick Reference: All Tools by Provider

### Firecrawl (12)
`firecrawl_scrape`, `firecrawl_search`, `firecrawl_crawl`, `firecrawl_check_crawl_status`, `firecrawl_map`, `firecrawl_extract`, `firecrawl_agent`, `firecrawl_agent_status`, `firecrawl_browser_create`, `firecrawl_browser_execute`, `firecrawl_browser_delete`, `firecrawl_browser_list`

### Jina (21)
`read_url`, `parallel_read_url`, `search_web`, `parallel_search_web`, `search_arxiv`, `parallel_search_arxiv`, `search_ssrn`, `parallel_search_ssrn`, `search_images`, `search_bibtex`, `search_jina_blog`, `expand_query`, `classify_text`, `sort_by_relevance`, `deduplicate_strings`, `deduplicate_images`, `extract_pdf`, `capture_screenshot_url`, `guess_datetime_url`, `primer`, `show_api_key`

### Exa (2)
`web_search_exa`, `get_code_context_exa`

### Perplexity (1)
`search`

## Quick Workflow Patterns

### Quick Search with Fallback
```
1. web_search_exa(query) → results
2. If error → search(query) → Perplexity AI answer
3. If error → search_web(query) → Jina results
```

### Parallel Research Batch
```
1. expand_query(topic) → related terms
2. parallel_search_web(queries[]) → batch results
3. sort_by_relevance(topic, urls) → ranked
4. parallel_read_url(top_5) → content
5. deduplicate_strings(facts) → clean data
```

### Full 7-Step Research
```
1. CLASSIFY → research type + depth
2. PLAN → expand_query + 3-7 queries
3. SEARCH → parallel_search_web / web_search_exa
4. READ → parallel_read_url top-5
5. EXTRACT → key facts, data, quotes
6. SYNTHESIZE → deduplicate + cross-check
7. REPORT → template + methodology
```

## Conventions

- Tool names omit MCP prefixes for brevity
- Fallback chains apply automatically on errors or empty results
- All reports include Methodology section
- Every fact must have a URL source
