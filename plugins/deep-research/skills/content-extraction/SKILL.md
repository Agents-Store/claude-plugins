---
name: content-extraction
description: Content reading and extraction guidelines — reading URLs, scraping pages, crawling sites, extracting PDFs, and taking screenshots. Use when reading web content, extracting structured data from pages, or processing documents.
---

# Content Extraction

Чтение и извлечение контента из веб-страниц, PDF и целых сайтов.

## Available Tools

| Tool | Provider | Purpose | Key Params |
|------|----------|---------|------------|
| `read_url` | Jina | Чтение URL → markdown | url |
| `parallel_read_url` | Jina | Чтение нескольких URL | urls[] |
| `firecrawl_scrape` | Firecrawl | Скрапинг с JS-поддержкой | url, formats, waitFor |
| `firecrawl_crawl` | Firecrawl | Краулинг сайта | url, limit, maxDiscoveryDepth |
| `firecrawl_check_crawl_status` | Firecrawl | Статус краулинга | id |
| `firecrawl_map` | Firecrawl | Карта сайта (все URL) | url, search |
| `firecrawl_extract` | Firecrawl | Структурированные данные | urls, prompt, schema |
| `firecrawl_agent` | Firecrawl | Автономный исследователь | prompt, urls |
| `firecrawl_agent_status` | Firecrawl | Статус агента | id |
| `firecrawl_browser_create` | Firecrawl | Создать браузерную сессию | — |
| `firecrawl_browser_execute` | Firecrawl | Действия в браузере | session_id, actions |
| `firecrawl_browser_delete` | Firecrawl | Удалить сессию | session_id |
| `firecrawl_browser_list` | Firecrawl | Список сессий | — |
| `extract_pdf` | Jina | Извлечь текст из PDF | url |
| `capture_screenshot_url` | Jina | Скриншот страницы | url |
| `guess_datetime_url` | Jina | Определить дату публикации | url |

## Reading a Single URL

### Primary: Jina read_url
```
read_url({ url: "https://example.com/article" })
→ Возвращает чистый markdown контент
```

### Fallback 1: Firecrawl scrape
```
firecrawl_scrape({
  url: "https://example.com/article",
  formats: ["markdown"],
  onlyMainContent: true
})
→ Лучше справляется с JS-рендерингом
```

### Fallback 2: Jina parallel (single URL)
```
parallel_read_url({ urls: ["https://example.com/article"] })
→ Альтернативный endpoint Jina
```

### Для JS-heavy страниц
```
firecrawl_scrape({
  url: "https://spa-app.com/page",
  formats: ["markdown"],
  waitFor: 5000
})
→ Ждёт 5 секунд для JS-рендеринга
```

## Reading Multiple URLs

### Batch чтение (3+ URL)
```
parallel_read_url({
  urls: [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
  ]
})
→ Все страницы параллельно
```

### Workflow: поиск → ранжирование → чтение
```
1. search_web(query) → список URL
2. sort_by_relevance(query, urls) → top-5
3. parallel_read_url(top_5_urls) → контент
```

## Crawling a Site

### Полный краулинг
```
1. firecrawl_crawl({
     url: "https://docs.example.com",
     limit: 20,
     maxDiscoveryDepth: 3
   }) → crawl_id

2. firecrawl_check_crawl_status({ id: crawl_id })
   → Повторять до status: "completed"

3. Обработать результаты
```

### Fallback: карта сайта
```
firecrawl_map({
  url: "https://docs.example.com",
  search: "API reference"
})
→ Список URL без контента (быстрее)
→ Затем parallel_read_url для нужных страниц
```

### Краулинг с фильтрацией
```
firecrawl_crawl({
  url: "https://example.com",
  limit: 50,
  includePaths: ["/blog/*", "/docs/*"],
  excludePaths: ["/admin/*", "/login/*"]
})
```

## Structured Data Extraction

### Извлечение по JSON-схеме
```
firecrawl_extract({
  urls: ["https://example.com/pricing"],
  prompt: "Extract all pricing plans",
  schema: {
    "type": "object",
    "properties": {
      "plans": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "price": { "type": "number" },
            "features": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    }
  }
})
```

### Извлечение из нескольких URL
```
firecrawl_extract({
  urls: [
    "https://competitor1.com/pricing",
    "https://competitor2.com/pricing"
  ],
  prompt: "Extract pricing plan name and monthly price"
})
```

### Скрапинг с JSON-форматом
```
firecrawl_scrape({
  url: "https://example.com/product",
  formats: ["json"],
  jsonOptions: {
    prompt: "Extract product details",
    schema: {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "price": { "type": "number" },
        "rating": { "type": "number" }
      }
    }
  }
})
```

## Browser Sessions

Для динамических страниц, требующих взаимодействия.

```
1. firecrawl_browser_create() → session_id

2. firecrawl_browser_execute({
     session_id: "...",
     actions: [
       { type: "click", selector: "#load-more" },
       { type: "wait", milliseconds: 2000 },
       { type: "scrape" }
     ]
   })

3. firecrawl_browser_delete({ session_id: "..." })
```

## PDF Processing

```
extract_pdf({ url: "https://arxiv.org/pdf/2301.00001" })
→ Извлекает полный текст из PDF
→ Работает с research papers, annual reports, whitepapers
```

## Autonomous Research Agent

Для сложных многошаговых исследований.

```
1. firecrawl_agent({
     prompt: "Research and compare the top 5 vector databases by performance, pricing, and features",
     urls: ["https://pinecone.io", "https://weaviate.io"]
   }) → agent_id

2. firecrawl_agent_status({ id: agent_id })
   → Повторять до status: "completed"
   → Получить структурированный результат
```

## Utility Tools

### Скриншот страницы
```
capture_screenshot_url({ url: "https://example.com" })
→ Визуальный снимок для отчёта
```

### Определение даты публикации
```
guess_datetime_url({ url: "https://blog.example.com/post" })
→ Определяет дату для фильтрации свежести контента
```

## Best Practices

1. **Всегда начинай с `read_url`** — самый быстрый и чистый вывод
2. **JS-страницы** — используй `firecrawl_scrape` с `waitFor: 5000`
3. **3+ URL** — используй `parallel_read_url` для параллельности
4. **Краулинг** — ограничивай `limit` и `maxDiscoveryDepth` для больших сайтов
5. **PDF** — `extract_pdf` для научных статей и отчётов
6. **Структурированные данные** — `firecrawl_extract` с JSON schema
7. **Проверяй дату** — `guess_datetime_url` для фильтрации устаревшего контента
8. **Browser sessions** — только для SPA и динамических страниц, всегда удаляй сессию после использования

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Empty content | JS-рендеринг не завершён | Добавить waitFor: 5000-10000 |
| Timeout | Сайт слишком большой | Уменьшить limit, использовать map вместо crawl |
| 403 Forbidden | Доступ заблокирован | Попробовать firecrawl_scrape с proxy: "stealth" |
| PDF extraction failed | Некорректный URL PDF | Проверить URL, попробовать read_url |
| Crawl stuck | Бесконечный краулинг | Установить limit и maxDiscoveryDepth |
