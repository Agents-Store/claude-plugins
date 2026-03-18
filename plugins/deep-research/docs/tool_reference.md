# Tool Reference — Deep Research Plugin

Справочник всех 36 инструментов, организованных по capabilities. Для fallback-цепочек см. CONNECTORS.md.

---

## ~~search — Web Search

| Tool | Provider | Best for |
|------|----------|----------|
| `web_search_exa` | Exa | Semantic search by meaning, category filters |
| `search` | Perplexity | AI-synthesized answers with citations |
| `search_web` | Jina | General web search, supports query arrays |
| `firecrawl_search` | Firecrawl | Search + optional content scraping |

### web_search_exa
```
web_search_exa({ query: "...", numResults: 10, type: "auto", category: "company" })
```
Params: `query` (required), `numResults`, `type` (auto/fast), `category` (company/research paper/people), `livecrawl`, `contextMaxCharacters`

### search (Perplexity)
```
search({ query: "What is the market size for AI code assistants?" })
```
Params: `query` (required). Returns AI answer with citations.

### search_web (Jina)
```
search_web({ query: "...", num: 30, tbs: "qdr:m" })
```
Params: `query` (string or array), `num`, `gl`, `hl`, `location`, `tbs`

### firecrawl_search
```
firecrawl_search({ query: "...", limit: 5, lang: "en", country: "us" })
```
Params: `query` (required), `limit`, `lang`, `country`, `tbs`, `scrapeOptions`

---

## ~~scrape — Read/Scrape Single Page

| Tool | Provider | Best for |
|------|----------|----------|
| `read_url` | Jina | Fast, clean markdown output |
| `firecrawl_scrape` | Firecrawl | JS rendering, JSON extraction, screenshots |

### read_url (Jina)
```
read_url({ url: "https://example.com/article" })
```
Params: `url` (string or array), `withAllImages`, `withAllLinks`

### firecrawl_scrape
```
firecrawl_scrape({ url: "...", formats: ["markdown"], onlyMainContent: true, waitFor: 5000 })
```
Params: `url` (required), `formats`, `onlyMainContent`, `waitFor`, `jsonOptions`, `actions`, `proxy`

---

## ~~batch_search — Parallel Search

| Tool | Provider | Best for |
|------|----------|----------|
| `parallel_search_web` | Jina | 3-5 queries simultaneously |

### parallel_search_web
```
parallel_search_web({ searches: [{ query: "..." }, { query: "..." }], timeout: 30000 })
```
Params: `searches` (array of {query, num, tbs, gl, hl}, max 5), `timeout`

---

## ~~batch_scrape — Read Multiple Pages

| Tool | Provider | Best for |
|------|----------|----------|
| `parallel_read_url` | Jina | Batch reading 3-5 URLs simultaneously |

### parallel_read_url
```
parallel_read_url({ urls: [{ url: "..." }, { url: "..." }], timeout: 30000 })
```
Params: `urls` (array of {url, withAllImages, withAllLinks}, max 5), `timeout`

---

## ~~crawl — Crawl Entire Website

| Tool | Provider | Best for |
|------|----------|----------|
| `firecrawl_crawl` | Firecrawl | Full site crawl with depth control |
| `firecrawl_check_crawl_status` | Firecrawl | Poll crawl job status |
| `firecrawl_map` | Firecrawl | Get site URL map (lighter than crawl) |

### firecrawl_crawl
```
firecrawl_crawl({ url: "...", limit: 20, maxDiscoveryDepth: 3 })
```
Params: `url` (required), `limit`, `maxDiscoveryDepth`, `includePaths`, `excludePaths`

### firecrawl_check_crawl_status
```
firecrawl_check_crawl_status({ id: "crawl-job-id" })
```

### firecrawl_map
```
firecrawl_map({ url: "...", search: "API reference", limit: 100 })
```

---

## ~~extract — Structured Data Extraction

| Tool | Provider | Best for |
|------|----------|----------|
| `firecrawl_extract` | Firecrawl | LLM extraction with JSON schema |

### firecrawl_extract
```
firecrawl_extract({ urls: ["..."], prompt: "Extract pricing plans", schema: {...} })
```
Params: `urls` (required), `prompt`, `schema`, `enableWebSearch`

---

## ~~academic_search — Scientific Papers

| Tool | Provider | Best for |
|------|----------|----------|
| `search_arxiv` | Jina | arXiv preprints (CS, physics, math) |
| `parallel_search_arxiv` | Jina | Batch arXiv search |
| `search_ssrn` | Jina | Social sciences, economics, law |
| `parallel_search_ssrn` | Jina | Batch SSRN search |

### search_arxiv / search_ssrn
```
search_arxiv({ query: "...", num: 30 })
search_ssrn({ query: "...", num: 30 })
```
Params: `query` (string or array), `num`, `tbs`

### parallel_search_arxiv / parallel_search_ssrn
```
parallel_search_arxiv({ searches: [{ query: "..." }], timeout: 30000 })
parallel_search_ssrn({ searches: [{ query: "..." }], timeout: 30000 })
```

---

## ~~code_search — Code and Technical Docs

| Tool | Provider | Best for |
|------|----------|----------|
| `get_code_context_exa` | Exa | Code examples, GitHub, Stack Overflow, docs |

### get_code_context_exa
```
get_code_context_exa({ query: "React server components pattern", tokensNum: 5000 })
```
Params: `query` (required), `tokensNum` (1000-50000)

---

## Utility Tools (unique, no fallback)

### Text Processing (Jina)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `expand_query` | Generate related search terms | `query` |
| `classify_text` | Categorize text by labels | `texts`, `labels` |
| `sort_by_relevance` | Rank docs by relevance | `query`, `documents`, `top_n` |
| `deduplicate_strings` | Remove similar text | `strings`, `k` |
| `deduplicate_images` | Remove similar images | `images`, `k` |

### Document & Media (Jina)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `extract_pdf` | Extract figures/tables from PDF | `id` or `url`, `type` |
| `capture_screenshot_url` | Screenshot a page | `url`, `return_url` |
| `guess_datetime_url` | Detect publication date | `url` |
| `search_images` | Search images | `query`, `return_url` |
| `search_bibtex` | Search BibTeX citations | `query`, `num`, `author`, `year` |
| `search_jina_blog` | Search Jina blog | `query`, `num` |

### Autonomous Agent (Firecrawl)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `firecrawl_agent` | Autonomous research agent | `prompt`, `urls`, `schema` |
| `firecrawl_agent_status` | Check agent job | `id` |

### Browser Automation (Firecrawl)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `firecrawl_browser_create` | Create browser session | `ttl`, `profile` |
| `firecrawl_browser_execute` | Execute actions | `sessionId`, `code`, `language` |
| `firecrawl_browser_delete` | Delete session | `sessionId` |
| `firecrawl_browser_list` | List sessions | `status` |

### System (Jina)

| Tool | Purpose |
|------|---------|
| `primer` | Session context info |
| `show_api_key` | Show API key (debug) |
