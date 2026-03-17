---
name: search-strategies
description: Search strategy guidelines — tool selection, fallback chains, query optimization, and parallel search orchestration. Use when choosing which search tools to use, handling tool failures, or optimizing search queries.
---

# Search Strategies

Стратегии поиска, выбор инструментов и fallback-цепочки для 4 провайдеров (Exa, Firecrawl, Jina, Perplexity).

## Available Search Tools

| Tool | Provider | Best For | Speed | Quality |
|------|----------|----------|-------|---------|
| `web_search_exa` | Exa | Семантический поиск, похожий контент | Fast | High relevance |
| `search` | Perplexity | AI-ответы с цитатами, факты | Medium | High (pre-analyzed) |
| `search_web` | Jina | Общий веб-поиск | Fast | Good |
| `parallel_search_web` | Jina | Множество запросов одновременно | Fast | Good |
| `firecrawl_search` | Firecrawl | Поиск + скрапинг контента | Medium | Good |
| `search_arxiv` | Jina | Научные статьи (arXiv) | Fast | High for papers |
| `parallel_search_arxiv` | Jina | Множество академических запросов | Fast | High |
| `search_ssrn` | Jina | Социальные науки, экономика | Fast | Niche |
| `get_code_context_exa` | Exa | Код, технический контекст | Fast | High for code |
| `search_images` | Jina | Поиск изображений | Fast | Good |
| `search_bibtex` | Jina | Библиографии, цитирования | Fast | Niche |

## Fallback Chains

### Семантический поиск
```
1. Try web_search_exa(query) — семантический, высокая релевантность
2. If error/empty → Try search(query) — Perplexity AI-ответ
3. If error/empty → Try search_web(query) — Jina общий поиск
```

### Чтение страницы (URL → текст)
```
1. Try read_url(url) — Jina, быстрый и чистый markdown
2. If error/empty → Try firecrawl_scrape(url, formats: ["markdown"]) — с JS-рендерингом
3. If error/empty → Try parallel_read_url([url]) — Jina альтернативный endpoint
```

### Краулинг сайта
```
1. Try firecrawl_crawl(url, limit: 20) — полный краулинг
2. If error/timeout → Try firecrawl_map(url) — получить карту сайта (легче)
```

### AI-ответ с цитатами
```
1. Try search(query) — Perplexity Sonar Pro, готовый ответ
2. If error → Try web_search_exa(query) + read top results — собрать вручную
```

### Поиск кода
```
1. Try get_code_context_exa(query) — специализированный поиск кода
2. If error/empty → Try search_web(query + " github code example")
3. If error/empty → Try firecrawl_search(query + " code implementation")
```

### Научные статьи
```
1. Try search_arxiv(query) — прямой поиск по arXiv
2. If error/empty → Try parallel_search_arxiv([query, related_query])
3. If error/empty → Try search(query + " research paper arxiv") — Perplexity
```

### Параллельный поиск
```
1. Try parallel_search_web(queries[]) — batch запросы через Jina
2. If error → Sequential: search_web(query) для каждого запроса отдельно
```

## When to Use Each Provider

### Exa — семантика и смысл
- Поиск по смыслу, а не ключевым словам
- Найти похожий контент (`type: "auto"`)
- Фильтрация по категории (company, research_paper, news)
- Поиск кода и технического контекста

### Perplexity — быстрые факты
- Фактические вопросы (размер рынка, даты, определения)
- Когда нужен готовый AI-ответ с цитатами
- Быстрая проверка фактов

### Jina — параллельность и объём
- Множество запросов одновременно (`parallel_search_web`)
- Чтение URL (`read_url` — primary для чтения)
- Научный поиск (arXiv, SSRN)
- Дедупликация и сортировка результатов
- Расширение запросов (`expand_query`)

### Firecrawl — скрапинг и структура
- JS-тяжёлые страницы (с `waitFor`)
- Краулинг целых сайтов
- Структурированное извлечение данных (JSON schema)
- Скриншоты и browser sessions

## Query Optimization

### Расширение запросов
```
1. expand_query(query) → получить связанные термины
2. Сформировать 3-7 запросов с разных углов:
   - Direct query: "RAG frameworks comparison"
   - Synonym: "retrieval augmented generation tools"
   - Comparison: "RAG vs fine-tuning"
   - Expert opinion: "best RAG framework expert review"
   - Data: "RAG benchmark results 2026"
```

### Domain Filtering
| Домен | Источники |
|-------|----------|
| Tech | github.com, stackoverflow.com, dev.to |
| Business | crunchbase.com, linkedin.com, bloomberg.com |
| Academic | arxiv.org, scholar.google.com |
| News | techcrunch.com, reuters.com, theverge.com |

### Date Filtering
- Актуальные темы (новости, тренды) → последние 3-6 месяцев
- Evergreen темы (концепции, архитектуры) → без ограничений
- Firecrawl: `tbs: "qdr:m"` (month), `"qdr:y"` (year)
- Exa: `start_published_date: "2025-01-01"`

## Parallel Search Strategy

### Оптимальный паттерн
```
1. expand_query(topic) → related terms
2. Сформировать 3-5 запросов с разных углов
3. parallel_search_web(queries) → batch результаты
4. sort_by_relevance(topic, results) → ранжирование
5. deduplicate_strings(results) → убрать дубли
```

### Ограничения
- Рекомендовано 3-5 запросов в одном batch
- При ошибке parallel — откат на последовательный search_web

## Error Handling

| Ошибка | Действие |
|--------|---------|
| Tool not available | Перейти к следующему в fallback-цепочке |
| Empty results | Расширить запрос, попробовать другой провайдер |
| Rate limited | Подождать, попробовать альтернативный провайдер |
| Timeout | Попробовать более лёгкую альтернативу (map вместо crawl) |
| Invalid URL | Проверить URL, попробовать firecrawl_scrape с waitFor |
| Content blocked | Использовать firecrawl_scrape с proxy: "stealth" |

## Best Practices

1. **Всегда начинай с семантического поиска** — web_search_exa для высокой релевантности
2. **Используй параллельный поиск** — parallel_search_web для скорости
3. **Дедупликация обязательна** — deduplicate_strings после параллельного поиска
4. **Расширяй запросы** — expand_query перед поиском для лучшего покрытия
5. **Fallback автоматически** — при ошибке сразу переключайся, не жди
6. **Минимум 3 запроса** — разные углы для полноты исследования
7. **Сортируй по релевантности** — sort_by_relevance перед чтением страниц
