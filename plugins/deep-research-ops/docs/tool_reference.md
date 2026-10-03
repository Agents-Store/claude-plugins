# Tool Reference — Deep Research Plugin

Справочник инструментов, организованных по capabilities. Плагин сам тулов не владеет — они приходят из серверов плагина `web-search-dev` (Exa, Firecrawl, Jina, Perplexity), поэтому полный список тулов и параметров смотрите там: skill `mcp-patterns`, `references/*-tools.md`. Здесь — только то, что нужно research-workflow. Для fallback-цепочек см. CONNECTORS.md.

Имена ниже — голые. При установке через `web-search-dev` они регистрируются как `mcp__plugin_web-search-dev_<server>__<tool>`, где `<server>` — `jina`, `exa`, `firecrawl` или `perplexity`.

---

## ~~search — Web Search

| Tool | Provider | Best for |
|------|----------|----------|
| `web_search_exa` | Exa | Semantic search by meaning |
| `perplexity_search` | Perplexity | Ranked results with dates, recency and domain filters |
| `search_web` | Jina | General web search, supports query arrays |
| `firecrawl_search` | Firecrawl | Search + optional content scraping |

### web_search_exa
```
web_search_exa({ query: "blog post comparing RAG frameworks", numResults: 10 })
```
Params: `query` (required), `numResults`. Схема строгая — других параметров нет. Категория задаётся внутри строки запроса: `category:company ...` или `category:people ...`. Фильтры по доменам и датам — только в opt-in `web_search_advanced_exa`.

### perplexity_search
```
perplexity_search({ query: "AI code assistant market size", max_results: 10, search_recency_filter: "month" })
```
Params: `query` (required), `max_results` (1-20), `max_tokens_per_page`, `country`, `search_recency_filter` (`hour`/`day`/`week`/`month`/`year`), `search_domain_filter` (префикс `-` исключает домен), `search_type` (`web`/`fast`). Возвращает ранжированные результаты без AI-синтеза.

### Perplexity AI answers — `~~answer`
Для ответа с цитатами вместо списка ссылок (`perplexity_search` выше возвращает только ссылки):

| Tool | Agent API preset | Use for |
|------|------------------|---------|
| `perplexity_ask` | `fast` | Quick facts with numbered citations |
| `perplexity_reason` | `medium` | Comparisons, step-by-step analysis |
| `perplexity_research` | `high` | Deep multi-source research (slow, expensive) |

```
perplexity_ask({ messages: [{ role: "user", content: "What is the market size for AI code assistants?" }] })
```
Params: `messages` — массив `{role, content}` (**не** `query`). У `ask` и `reason` ещё `search_recency_filter`, `search_domain_filter`, `search_context_size` (`low`/`medium`/`high`); у `research` только `messages`.

### search_web (Jina)
```
search_web({ query: "...", num: 10, tbs: "qdr:m" })
```
Params: `query` (string или массив до 5), `num` (1-100, default 30), `gl`, `hl`, `location`, `tbs`

### firecrawl_search
```
firecrawl_search({ query: "...", limit: 5, sources: ["web"] })
```
Params: `query` (required), `limit`, `sources` (`web`/`news`/`images`/`alexandria`), `categories` (`research`/`pdf`/`developer`), `includeDomains`/`excludeDomains`, `tbs`, `location`, `scrapeOptions`. Параметров `lang` и `country` нет.

---

## ~~scrape — Read/Scrape Single Page

| Tool | Provider | Best for |
|------|----------|----------|
| `read_url` | Jina | Fast, clean markdown; PDFs; targeted passages via `question` |
| `firecrawl_scrape` | Firecrawl | JS rendering, JSON extraction, screenshots, `query` format |
| `web_fetch_exa` | Exa | Last-resort page read |

### read_url (Jina)
```
read_url({ url: "https://example.com/article" })
```
Params: `url` (string или массив до 5), `question`, `topk` (1-50, default 1), `chunk_size` (слов, default 100), `ocr`, `page`, `withAllImages`, `withAllLinks`

**Дешёвый режим** — только пассажи, отвечающие на вопрос, вместо всей страницы:
```
read_url({ url: ["https://example.com/a", "https://example.com/b"], question: "What does it cost?", topk: 3 })
```

### firecrawl_scrape
```
firecrawl_scrape({ url: "...", formats: ["markdown"], onlyMainContent: true, waitFor: 5000 })
```
Params: `url` (required), `formats` (только строки: `markdown`, `html`, `rawHtml`, `screenshot`, `links`, `summary`, `json`, `query`, ...), `jsonOptions`, `queryOptions`, `onlyMainContent`, `waitFor`, `actions`, `proxy`, `parsers`, `maxAge`

Точечный вопрос к странице:
```
firecrawl_scrape({ url: "...", formats: ["query"], queryOptions: { prompt: "What is the rate limit?", mode: "directQuote" } })
```

### web_fetch_exa
```
web_fetch_exa({ urls: ["https://example.com/article"], maxCharacters: 20000 })
```
Params: `urls` (required), `maxCharacters` (default 3000 — страница режется до 3000 символов, если не передать)

---

## ~~batch_search — Parallel Search

| Tool | Provider | Best for |
|------|----------|----------|
| `search_web` | Jina | До 5 запросов одним вызовом |

```
search_web({ query: ["RAG frameworks comparison", "vector database benchmarks", "embedding models"], num: 10 })
```
Массив в `query` выполняется параллельно за один вызов. Если Jina недоступен — по одному вызову `web_search_exa`, затем `perplexity_search` на каждый запрос.

---

## ~~batch_scrape — Read Multiple Pages

| Tool | Provider | Best for |
|------|----------|----------|
| `read_url` | Jina | До 5 URL одним вызовом |
| `web_fetch_exa` | Exa | Несколько URL одним вызовом (`urls`); по умолчанию режет страницу до 3000 символов — передавайте `maxCharacters: 20000` |

```
read_url({ url: ["https://example.com/1", "https://example.com/2"], question: "...", topk: 3 })
```
Если оба недоступны — по одному вызову `firecrawl_scrape` на URL. `question` понимает только `read_url`; фолбэки возвращают страницы целиком (или `firecrawl_scrape` с `formats: ["query"]` на каждый URL).

---

## ~~crawl — Crawl Entire Website

| Tool | Provider | Best for |
|------|----------|----------|
| `firecrawl_crawl` | Firecrawl | Full site crawl with depth control; ждёт завершения и возвращает данные |
| `firecrawl_check_crawl_status` | Firecrawl | Подхватить crawl, запущенный ранее или оборванный |
| `firecrawl_map` | Firecrawl | Get site URL map (lighter than crawl) |

### firecrawl_crawl
```
firecrawl_crawl({ url: "...", limit: 20, maxDiscoveryDepth: 3, includePaths: ["/docs/*"] })
```
Params: `url` (required), `limit`, `maxDiscoveryDepth`, `includePaths`, `excludePaths`, `scrapeOptions`

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
| `firecrawl_scrape` (`formats: ["json"]`) | Firecrawl | LLM extraction with JSON schema, one URL per call |
| `firecrawl_agent` + `firecrawl_agent_status` | Firecrawl | Unknown URLs, data spread across several sites |

Отдельного extract-тула больше нет: структурированные данные берутся через `firecrawl_scrape` с `formats: ["json"]`.

### firecrawl_scrape with JSON
```
firecrawl_scrape({
  url: "https://example.com/pricing",
  formats: ["json"],
  jsonOptions: { prompt: "Extract pricing plans", schema: { type: "object", properties: { plans: { type: "array", items: { type: "object" } } } } }
})
```
Один вызов — один URL; для нескольких URL повторите вызов.

### firecrawl_agent
```
firecrawl_agent({ prompt: "Find the top 5 headless CMS with starting price", schema: {...}, effort: "medium", maxCredits: 500 })
```
Params: `prompt` (required), `urls`, `schema`, `effort` (`low`/`medium`/`high`), `maxCredits`, `threadId`. Возвращает id задачи — читайте `firecrawl_agent_status({ id })` каждые 15-30 секунд до `completed` или `failed` (обычно 1-3 минуты).

---

## ~~academic_search — Scientific Papers

| Tool | Provider | Best for |
|------|----------|----------|
| `firecrawl_research_search_papers` | Firecrawl | PubMed, bioRxiv, medRxiv, arXiv — метаданные и аннотации |
| `firecrawl_research_read_paper` | Firecrawl | Пассажи полного текста одной статьи под вопрос |
| `firecrawl_research_related_papers` | Firecrawl | Граф цитирований: похожие, цитирующие, цитируемые |
| `firecrawl_research_inspect_paper` | Firecrawl | Канонические метаданные одной статьи |
| `search_arxiv` | Jina | arXiv preprints (CS, physics, math) |
| `search_ssrn` | Jina | Social sciences, economics, law |

### Paper research (search_papers, read_paper, related_papers)
```
firecrawl_research_search_papers({ query: "retrieval augmented generation evaluation", k: 20, from: "2025-01-01" })
firecrawl_research_read_paper({ paperId: "arxiv:1706.03762", question: "What is the attention mechanism?", k: 4 })
firecrawl_research_related_papers({ seed_ids: ["arxiv:1706.03762"], intent: "follow-up work on efficiency", mode: "citers" })
```
Params: `search_papers` — `query`, `k`, `authors`, `categories`, `from`, `to`; `read_paper` — `paperId`, `question`, `k`; `related_papers` — `seed_ids` (1-10), `intent`, `mode` (`similar`/`citers`/`references`), `k`, `rerank`. `paperId` — `arxiv:…`, `doi:…`, `pmid:…`, `pmcid:…`.

### search_arxiv / search_ssrn
```
search_arxiv({ query: ["...", "..."], num: 20 })
search_ssrn({ query: "...", num: 20 })
```
Params: `query` (string или массив до 5), `num`, `tbs`

---

## ~~code_search — Code and Technical Docs

| Tool | Provider | Best for |
|------|----------|----------|
| `firecrawl_developer_search` | Firecrawl | Репозитории, GitHub issues, merged PR, README, документация |
| `web_search_advanced_exa` | Exa (opt-in) | Поиск с `includeDomains: ["github.com", "stackoverflow.com"]` |

Отдельного code-search тула у Exa нет.

### firecrawl_developer_search
```
firecrawl_developer_search({ query: "React server components hydration mismatch", k: 10 })
```
Params: `query` (required), `k` (1-100, default 10), `skills` (`"only"` — искать только по agent-skill файлам)

### web_search_advanced_exa
```
web_search_advanced_exa({ query: "authentication middleware", includeDomains: ["github.com"], numResults: 15 })
```
Включается через `ENABLED_TOOLS` на локальном сервере или параметр `tools` на hosted-сервере — см. `web-search-dev`. Если не включён — следующий шаг цепочки.

---

## ~~deep_agent — Heavy Tier for depth=deep

| Tool | Provider | Notes |
|------|----------|-------|
| `agent_run` | Exa | Нужен API key или OAuth; на локальном сервере opt-in. `query` или `runId` (продолжить), `outputSchema`, `effort` |
| `firecrawl_agent` + `firecrawl_agent_status` | Firecrawl | См. выше; ограничивайте `maxCredits` |
| `perplexity_research` | Perplexity | Только `messages`; медленный, самый дорогой тул Perplexity |

Тяжёлые вызовы идут минутами и тратят кредиты: только для depth `deep`, как дополнительный проход, и результат сверяется со страницами, прочитанными обычной цепочкой.

---

## Utility Tools (unique, no fallback)

### Text Processing (Jina)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `sort_by_relevance` | Rank docs by relevance | `query`, `documents`, `top_n` |
| `deduplicate_strings` | Remove near-duplicate text | `strings`, `k` |

Расширение запросов и классификация текста — шаги самой модели, отдельных тулов нет.

### Document & Media (Jina)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `extract_pdf` | Extract figures/tables/equations from PDF as images | `id` or `url`, `type` |
| `capture_screenshot_url` | Screenshot a page | `url`, `return_url: true` |
| `guess_datetime_url` | Detect publication date | `url` |
| `search_images` | Search images | `query`, `return_url: true` |
| `search_jina_blog` | Search Jina blog | `query`, `num` |

### Browser Automation (Firecrawl)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `firecrawl_interact` | Drive a live browser session | `url` или `scrapeId`; `prompt` или `code` |
| `firecrawl_interact_stop` | Close the session | `scrapeId` |

Действует на реальном сайте: отправка форм имеет побочные эффекты. Сессию всегда закрывайте.

### System (Jina)

| Tool | Purpose |
|------|---------|
| `primer` | Current time and user location |
