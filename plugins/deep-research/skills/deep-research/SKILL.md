---
name: deep-research
description: Main research automation skill. 7-step algorithm for comprehensive research with 6 research types, query planning, parallel search, extraction, synthesis, and structured reporting. Use when conducting any multi-step research task.
---

# Deep Research

Основной алгоритм проведения комплексных исследований. 7 шагов, 6 типов исследований, 38 инструментов.

## 6 Research Types

| Тип | Сигналы-триггеры | Фокус | Шаблон отчёта |
|-----|-----------------|-------|--------------|
| **Competitive Analysis** | «конкуренты», «vs», «сравни», «альтернативы to» | Сайты, продукты, цены, позиционирование | Comparison Table |
| **Market Research** | «рынок», «market», «тренды», «TAM», «прогноз» | Размер, рост, сегменты, игроки | Deep Research Report |
| **Technical Audit** | «архитектура», «стек», «как работает», «best practices» | Технологии, производительность, паттерны | Deep Research Report |
| **Person/Company Lookup** | имя, компания, «кто такой», «о компании» | Биография, история, ключевые факты | Executive Summary |
| **Topic Deep Dive** | «объясни», «deep dive», «подробно», «comprehensive» | Все углы, история, текущее состояние | Deep Research Report |
| **News & Trends** | «новости», «latest», «свежие», год/дата | События, развитие, таймлайн | Executive Summary |

## 7-Step Algorithm

### Step 1: CLASSIFY

Определи тип исследования по сигналам в запросе пользователя.

```
Input: user query
Logic: match keywords to research type (see table above)
Output: research_type + depth_level
If ambiguous: ask user to clarify
```

**Depth levels:**

| Level | Queries | Pages | Описание |
|-------|---------|-------|----------|
| quick | 2-3 | 3 | Быстрый обзор |
| standard | 4-5 | 5 | Стандартное исследование |
| deep | 6-7 | 8-10 | Глубокий анализ |

### Step 2: PLAN

Сформировать 3-7 поисковых запросов с разных углов.

```
1. expand_query(topic) → related terms
2. Generate queries covering different angles:
   - Direct: "{topic} overview"
   - Comparison: "{topic} vs alternatives"
   - Expert: "{topic} expert analysis review"
   - Data: "{topic} statistics data 2026"
   - Trends: "{topic} trends forecast"
```

**Query patterns по типу:**

| Тип | Query patterns |
|-----|---------------|
| Competitive Analysis | "{product} pricing", "{product} vs {competitor}", "{product} reviews", "{product} features comparison" |
| Market Research | "{industry} market size", "{industry} trends 2026", "{industry} key players", "{industry} growth forecast" |
| Technical Audit | "{technology} architecture", "{technology} best practices", "{technology} performance benchmarks", "{technology} documentation" |
| Person/Company Lookup | "{name} background", "{company} about", "{company} funding revenue", "{name} interview" |
| Topic Deep Dive | "{topic} explained", "{topic} history evolution", "{topic} current state", "{topic} future predictions" |
| News & Trends | "{topic} latest news", "{topic} recent developments", "{topic} 2026 updates" |

### Step 3: SEARCH

Параллельный поиск через оптимальные инструменты.

```
1. parallel_search_web(queries) — batch search через Jina
   OR if parallel unavailable:
   web_search_exa(query) для каждого запроса

2. Для научных тем:
   search_arxiv(query) — добавить академические результаты

3. Для фактов:
   search(query) — Perplexity для AI-синтезированных ответов

4. Apply fallback chains if any tool fails
   (see search-strategies skill)
```

**Tool selection по типу:**

| Тип | Primary search | Additional |
|-----|---------------|-----------|
| Competitive Analysis | `web_search_exa` | `firecrawl_extract` для pricing |
| Market Research | `search` (Perplexity) | `web_search_exa` для детальных данных |
| Technical Audit | `get_code_context_exa` | `search_web` для docs |
| Person/Company Lookup | `web_search_exa` | `search` для фактов |
| Topic Deep Dive | `parallel_search_web` | `search_arxiv` для papers |
| News & Trends | `search` (Perplexity) | `web_search_exa` с date filter |

### Step 4: READ

Прочитать top-5 страниц из результатов поиска.

```
1. Collect all URLs from search results
2. sort_by_relevance(query, urls) → rank by relevance
3. Select top-5 (or top-N based on depth)
4. parallel_read_url(top_urls) → get content
   Fallback: read_url per URL → firecrawl_scrape

Priority:
- Official sites > reputable sources > blogs
- Recent > older (check with guess_datetime_url)
- Primary sources > secondary
```

### Step 5: EXTRACT

Извлечь ключевые данные из прочитанного контента.

```
From each page extract:
- Key facts and claims
- Numbers, metrics, data points
- Direct quotes (with attribution)
- Dates and timeline events

Tools:
- classify_text(text, labels) → categorize content
- firecrawl_extract(urls, schema) → structured data
- For PDFs: extract_pdf(url) → full text
```

### Step 6: SYNTHESIZE

Объединить данные, дедупликация, cross-check.

```
1. deduplicate_strings(facts) → remove redundant info
2. Cross-check: compare facts from different sources
   - Same fact from 3+ sources → High confidence
   - Same fact from 2 sources → Medium confidence
   - Single source only → Low confidence (flag it)
3. Identify contradictions → note in Gaps section
4. Identify information gaps → note what was NOT found
```

### Step 7: REPORT

Сформировать структурированный отчёт.

```
1. Select template based on research_type
   (see report-generation skill for full templates)

2. Fill in all sections:
   - Key Findings with inline citations
   - Data tables with sources
   - Quotes with attribution
   - Gaps & Limitations

3. ALWAYS include Methodology:
   - Research type
   - Tools used (providers)
   - Search queries (full list)
   - Pages analyzed (count)
   - Date of research
   - Limitations

4. Output the report in markdown
```

## Complete Workflow Example

**Query:** "Compare Notion vs Linear vs Asana for project management"

```
Step 1: CLASSIFY → Competitive Analysis, standard depth

Step 2: PLAN →
  - "Notion project management features pricing"
  - "Linear project management features pricing"
  - "Asana project management features pricing"
  - "Notion vs Linear vs Asana comparison"
  - "best project management tool 2026 review"

Step 3: SEARCH →
  parallel_search_web(["Notion features pricing", "Linear features pricing", "Asana features pricing"])
  web_search_exa("Notion vs Linear vs Asana comparison 2026")
  search("best project management tool comparison 2026")

Step 4: READ →
  sort_by_relevance("project management comparison", all_urls)
  parallel_read_url(top_5_urls)

Step 5: EXTRACT →
  firecrawl_extract(pricing_urls, pricing_schema)
  Extract features, pricing, ratings from content

Step 6: SYNTHESIZE →
  deduplicate_strings(all_facts)
  Cross-check pricing across sources
  Identify feature gaps

Step 7: REPORT →
  Use Comparison Table template
  Fill feature comparison table
  Add detailed analysis per product
  Include verdict and methodology
```

## Quality Checklist

Before delivering any report, verify:

- [ ] Research type correctly classified
- [ ] Minimum 3 search queries from different angles
- [ ] At least 3-5 pages read and analyzed
- [ ] Every fact has a URL source
- [ ] Data cross-checked across sources
- [ ] Confidence levels assigned (High/Medium/Low)
- [ ] Gaps and limitations documented
- [ ] Methodology section complete
- [ ] Date of research included
- [ ] Report uses correct template for research type
