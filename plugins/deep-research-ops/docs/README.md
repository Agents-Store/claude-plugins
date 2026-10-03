# Deep Research Plugin

Плагин для Claude Code для комплексных веб-исследований: многошаговый workflow поверх любых search MCP-серверов. Тулы приходят из плагина `web-search-dev` (Exa, Firecrawl, Jina, Perplexity) — он указан в `dependencies` и ставится вместе с этим плагином. Capability-based CONNECTORS с автоматическим FALLBACK.

## Архитектура: CONNECTORS + FALLBACK

Плагин описывает действия через `~~capability` (search, scrape, crawl) — НЕ конкретные инструменты. Каждое действие имеет цепочку провайдеров. При ошибке — автоматически следующий.

| Capability | Описание | Fallback chain |
|-----------|----------|----------------|
| `~~search` | Поиск в интернете | `web_search_exa` → `perplexity_search` → `search_web` → `firecrawl_search` |
| `~~scrape` | Прочитать страницу (с `question` — только нужные пассажи) | `read_url` → `firecrawl_scrape` → `web_fetch_exa` |
| `~~batch_search` | Параллельный поиск (до 5 запросов) | `search_web({query: [...]})` → по одному `web_search_exa` → по одному `perplexity_search` |
| `~~batch_scrape` | Прочитать несколько страниц (до 5 URL) | `read_url({url: [...]})` → `web_fetch_exa` → по одному `firecrawl_scrape` |
| `~~crawl` | Краулинг сайта | `firecrawl_crawl` → `firecrawl_map` + `~~batch_scrape` |
| `~~extract` | Структурированные данные | `firecrawl_scrape` (`formats: ["json"]`, `jsonOptions`) → `firecrawl_agent` для неизвестных URL |
| `~~academic_search` | Научные статьи | `firecrawl_research_search_papers` → `search_arxiv` / `search_ssrn` → `perplexity_search` |
| `~~code_search` | Поиск кода | `firecrawl_developer_search` → `web_search_advanced_exa` (opt-in) → search + "github" |
| `~~deep_agent` | «Тяжёлый» уровень для depth=deep | `agent_run` (Exa) → `firecrawl_agent` → `perplexity_research` |

См. `CONNECTORS.md` для полного маппинга.

## Провайдеры

| Провайдер | Специализация |
|-----------|---------------|
| **Exa** | Семантический поиск, поиск компаний и людей, чтение страниц |
| **Firecrawl** | Скрапинг, краулинг, JSON extraction, developer search, поиск научных статей, агент, браузер (`firecrawl_interact`) |
| **Jina** | Пакетный поиск и чтение (массивы), точечное чтение (`question`), arXiv/SSRN, PDF, ранжирование, дедупликация |
| **Perplexity** | AI-ответы с цитатами (Agent API presets `fast` / `medium` / `high`) |

## Установка

1. Скопируйте папку `deep-research-ops` в директорию плагинов Claude Code
2. При установке из маркетплейса плагин `web-search-dev` подтягивается автоматически (`dependencies` в `plugin.json`; при ручном копировании папки установите его сами) — он подключает MCP-серверы Exa, Firecrawl, Jina и Perplexity. Без него плагин работает с любыми другими серверами поиска: недоступные тулы в цепочках пропускаются
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
