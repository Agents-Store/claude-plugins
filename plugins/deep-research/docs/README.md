# Deep Research Plugin

Плагин для Claude Code для комплексных веб-исследований. 4 провайдера (Exa, Firecrawl, Jina, Perplexity), capability-based CONNECTORS с автоматическим FALLBACK.

## Архитектура: CONNECTORS + FALLBACK

Плагин описывает действия через `~~capability` (search, scrape, crawl) — НЕ конкретные инструменты. Каждое действие имеет цепочку провайдеров. При ошибке — автоматически следующий.

| Capability | Описание | Fallback chain |
|-----------|----------|----------------|
| `~~search` | Поиск в интернете | Exa → Perplexity → Jina → Firecrawl |
| `~~scrape` | Прочитать страницу | Jina → Firecrawl |
| `~~batch_search` | Параллельный поиск | Jina parallel → multiple Exa |
| `~~batch_scrape` | Прочитать несколько страниц | Jina parallel → multiple Firecrawl |
| `~~crawl` | Краулинг сайта | Firecrawl crawl → map + batch_scrape |
| `~~extract` | Структурированные данные | Firecrawl extract → scrape + JSON |
| `~~academic_search` | Научные статьи | arXiv → SSRN → Perplexity |
| `~~code_search` | Поиск кода | Exa code → search + "github" |

См. `CONNECTORS.md` для полного маппинга.

## Провайдеры

| Провайдер | Специализация |
|-----------|---------------|
| **Exa** | Семантический поиск, код |
| **Firecrawl** | Скрапинг, краулинг, JSON extraction, браузер |
| **Jina** | Параллельный поиск, чтение URL, arXiv, PDF, дедупликация |
| **Perplexity** | AI-ответы с цитатами (Sonar Pro) |

## Установка

1. Скопируйте папку `deep-research` в директорию плагинов Claude Code
2. MCP-сервер настроен в `.mcp.json`
3. Перезапустите Claude Code

## Быстрый старт

```
/research AI code assistants market 2026
/search best RAG frameworks comparison
/compare Notion vs Linear vs Asana
/read-url https://example.com/article
/crawl-site https://docs.example.com
/summarize transformer architecture
```

## 6 типов исследований

| Тип | Описание | Шаблон отчёта |
|-----|----------|--------------|
| Competitive Analysis | Конкуренты, продукты, цены | Comparison Table |
| Market Research | Рынок, тренды, прогнозы | Deep Research Report |
| Technical Audit | Архитектуры, стеки, best practices | Deep Research Report |
| Person/Company Lookup | Информация из открытых источников | Executive Summary |
| Topic Deep Dive | Глубокое изучение темы | Deep Research Report |
| News & Trends | Актуальные новости | Executive Summary |

## Команды

| Команда | Описание |
|---------|----------|
| `/research <тема>` | Полное исследование по 7-шаговому алгоритму |
| `/search <запрос>` | Быстрый поиск с автоматическим fallback |
| `/read-url <url>` | Прочитать и извлечь контент со страницы |
| `/crawl-site <url>` | Краулинг сайта целиком |
| `/compare <A> vs <B>` | Сравнительный анализ |
| `/summarize <тема>` | Суммаризация темы или URL |

## Скиллы

| Скилл | Назначение |
|-------|-----------|
| `deep-research` | Главный 7-шаговый алгоритм |
| `search-strategies` | Выбор инструментов и fallback-цепочки |
| `content-extraction` | Чтение URL, скрапинг, краулинг, PDF |
| `report-generation` | 3 шаблона отчётов |
| `examples` | Примеры и справочники |

## Шаблоны отчётов

1. **Executive Summary** — Key Findings, Overview, Recommendations, Sources, Methodology
2. **Deep Research Report** — полный отчёт с Background, Findings, Analysis, Data, Quotes, Gaps
3. **Comparison Table** — таблица сравнения с Verdict и детальным анализом

Каждый отчёт содержит секцию **Methodology** с информацией о провайдерах, количестве запросов и источников.
