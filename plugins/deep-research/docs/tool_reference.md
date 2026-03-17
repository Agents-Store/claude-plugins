# Tool Reference — Deep Research Plugin

Справочник всех 38 инструментов, организованных по провайдерам. Названия указаны без MCP-префиксов.

---

## Firecrawl (12 инструментов)

### firecrawl_scrape
Скрапинг одной страницы с поддержкой JS-рендеринга.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL страницы |
| formats | string[] | Нет | Форматы: markdown, html, json, screenshot, links, summary |
| onlyMainContent | boolean | Нет | Только основной контент (без навигации) |
| waitFor | number | Нет | Ожидание JS-рендеринга (мс) |
| jsonOptions | object | Нет | Схема для JSON-извлечения |
| actions | array | Нет | Действия перед скрапингом (click, scroll, wait) |

```
firecrawl_scrape({ url: "https://example.com", formats: ["markdown"], onlyMainContent: true })
```

### firecrawl_search
Поиск по вебу с извлечением контента из результатов.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |
| limit | number | Нет | Макс. результатов (по умолчанию 5) |
| lang | string | Нет | Язык (en, ru, de...) |
| country | string | Нет | Страна (us, uk, de...) |
| tbs | string | Нет | Фильтр времени: qdr:h, qdr:d, qdr:w, qdr:m, qdr:y |
| scrapeOptions | object | Нет | Опции скрапинга результатов |

```
firecrawl_search({ query: "AI trends 2026", limit: 5, lang: "en" })
```

### firecrawl_crawl
Краулинг сайта целиком.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | Стартовый URL |
| limit | number | Нет | Макс. страниц |
| maxDiscoveryDepth | number | Нет | Глубина обхода |
| includePaths | string[] | Нет | Паттерны включения |
| excludePaths | string[] | Нет | Паттерны исключения |

```
firecrawl_crawl({ url: "https://docs.example.com", limit: 20, maxDiscoveryDepth: 3 })
```

### firecrawl_check_crawl_status
Проверка статуса краулинга.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| id | string | Да | ID задачи краулинга |

```
firecrawl_check_crawl_status({ id: "crawl-job-id" })
```

### firecrawl_map
Получение карты сайта (все URL).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL сайта |
| search | string | Нет | Поиск конкретных страниц |
| limit | number | Нет | Макс. URL |

```
firecrawl_map({ url: "https://docs.example.com", search: "API reference" })
```

### firecrawl_extract
Извлечение структурированных данных с URL по JSON-схеме.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| urls | string[] | Да | Список URL |
| prompt | string | Да | Что извлекать |
| schema | object | Нет | JSON Schema для результата |
| enableWebSearch | boolean | Нет | Дополнить веб-поиском |

```
firecrawl_extract({ urls: ["https://example.com/pricing"], prompt: "Extract pricing plans", schema: {...} })
```

### firecrawl_agent
Автономный исследовательский агент.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| prompt | string | Да | Задача исследования (макс 10000 символов) |
| urls | string[] | Нет | Стартовые URL |
| schema | object | Нет | JSON Schema для структурированного вывода |

```
firecrawl_agent({ prompt: "Compare top 5 CRM pricing plans", urls: ["https://hubspot.com/pricing"] })
```

### firecrawl_agent_status
Проверка результатов агента.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| id | string | Да | ID агента |

### firecrawl_browser_create
Создание браузерной сессии для JS-тяжёлых страниц.

### firecrawl_browser_execute
Выполнение действий в браузерной сессии.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| session_id | string | Да | ID сессии |
| actions | array | Да | Действия (click, type, scroll, screenshot) |

### firecrawl_browser_delete
Удаление браузерной сессии.

### firecrawl_browser_list
Список активных браузерных сессий.

---

## Jina (21 инструмент)

### read_url
Чтение URL и конвертация в markdown. Primary инструмент для чтения страниц.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL страницы |

```
read_url({ url: "https://example.com/article" })
```

### parallel_read_url
Параллельное чтение нескольких URL одновременно. Возвращает markdown-контент для каждого URL. Идеален для batch-чтения top-5 результатов поиска.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| urls | string[] | Да | Список URL для параллельного чтения |

```
parallel_read_url({ urls: ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"] })
→ Returns: markdown content for each URL simultaneously
```

Best practice: используй после `sort_by_relevance` для чтения top-N наиболее релевантных страниц.

### search_web
Поиск по вебу через Jina.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |

```
search_web({ query: "best practices microservices architecture" })
```

### parallel_search_web
Параллельный поиск по нескольким запросам одновременно.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| queries | string[] | Да | Список запросов (3-5 рекомендовано) |

```
parallel_search_web({ queries: ["RAG frameworks comparison", "vector database benchmarks", "embedding models 2026"] })
```

### search_arxiv
Поиск научных статей на arXiv.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |

```
search_arxiv({ query: "retrieval augmented generation" })
```

### parallel_search_arxiv
Параллельный поиск на arXiv по нескольким запросам.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| queries | string[] | Да | Список запросов |

### search_ssrn
Поиск на SSRN (социальные науки, экономика).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |

### parallel_search_ssrn
Параллельный поиск на SSRN по нескольким запросам одновременно. Аналог parallel_search_arxiv для социальных наук и экономики.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| searches | array | Да | Массив объектов поиска (max 5), каждый с полем query |
| timeout | number | Нет | Таймаут в мс (по умолчанию 30000) |

```
parallel_search_ssrn({ searches: [{ query: "fintech regulation impact" }, { query: "digital banking adoption" }] })
→ Returns: papers from SSRN for each query simultaneously
```

### search_images
Поиск изображений по запросу. Полезен для нахождения диаграмм, архитектурных схем, инфографики.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос для поиска изображений |

```
search_images({ query: "microservices architecture diagram" })
→ Returns: image URLs with descriptions
```

### search_bibtex
Поиск библиографических записей.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |

### search_jina_blog
Поиск по блогу и новостям Jina AI. Полезен для нахождения документации, туториалов и анонсов продуктов Jina.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string/string[] | Да | Поисковый запрос (строка или массив для параллельного поиска) |
| num | number | Нет | Макс. результатов (1-100, по умолчанию 30) |
| tbs | string | Нет | Фильтр времени: qdr:h, qdr:d, qdr:w, qdr:m, qdr:y |

```
search_jina_blog({ query: "embeddings reranker", num: 10 })
→ Returns: Jina blog posts about embeddings and reranker
```

### expand_query
Расширение запроса — генерация связанных поисковых терминов.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Исходный запрос |

```
expand_query({ query: "AI code assistant" })
```

### classify_text
Классификация текста по категориям.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| text | string | Да | Текст для классификации |
| labels | string[] | Да | Возможные категории |

```
classify_text({ text: "...", labels: ["technology", "business", "science"] })
```

### sort_by_relevance
Сортировка текстов по релевантности к запросу.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Запрос |
| documents | string[] | Да | Список текстов |

```
sort_by_relevance({ query: "machine learning", documents: ["text1", "text2", "text3"] })
```

### deduplicate_strings
Дедупликация текстовых строк.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| strings | string[] | Да | Список строк |

```
deduplicate_strings({ strings: ["fact A", "fact A rephrased", "fact B"] })
```

### deduplicate_images
Дедупликация изображений по визуальному сходству с использованием Jina CLIP v2. Выбирает наиболее разнообразное подмножество из набора похожих изображений.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| images | string[] | Да | Массив URL изображений или base64-строк |
| k | number | Нет | Количество уникальных изображений для возврата (auto если не указано) |

```
deduplicate_images({ images: ["https://img1.png", "https://img2.png", "https://img3.png"], k: 2 })
→ Returns: top-k most visually diverse images
```

### extract_pdf
Извлечение текста из PDF.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL PDF-файла |

```
extract_pdf({ url: "https://arxiv.org/pdf/2301.00001" })
```

### capture_screenshot_url
Скриншот веб-страницы.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL страницы |

### guess_datetime_url
Определение даты публикации страницы.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| url | string | Да | URL страницы |

```
guess_datetime_url({ url: "https://example.com/blog/post" })
```

### primer
Получение сводки/описания Jina API.

### show_api_key
Показ текущего API-ключа Jina.

---

## Exa (2 инструмента)

### web_search_exa
Семантический поиск по вебу. Лучший для поиска по смыслу, а не по ключевым словам.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос |
| num_results | number | Нет | Количество результатов |
| type | string | Нет | Тип: auto, keyword, neural |
| category | string | Нет | Категория: company, research_paper, news, tweet |
| start_published_date | string | Нет | Дата начала (ISO) |
| end_published_date | string | Нет | Дата конца (ISO) |

```
web_search_exa({ query: "best alternatives to Notion for team collaboration", num_results: 10, type: "auto" })
```

### get_code_context_exa
Поиск кода и технического контекста.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Поисковый запрос по коду |

```
get_code_context_exa({ query: "React server components implementation pattern" })
```

---

## Perplexity (1 инструмент)

### search
AI-поиск через Perplexity Sonar Pro. Возвращает синтезированный ответ с цитатами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| query | string | Да | Вопрос или поисковый запрос |

```
search({ query: "What is the current market size for AI code assistants in 2026?" })
```

Особенности:
- Возвращает готовый AI-ответ, а не список ссылок
- Включает цитаты с URL-источниками
- Лучший для фактических вопросов и быстрых ответов
- Использует модель Sonar Pro
