# Deep Research Plugin

Плагин для Claude Code для проведения комплексных веб-исследований с использованием 38 инструментов от 4 провайдеров через единый MCP endpoint.

## Провайдеры

| Провайдер | Инструменты | Специализация |
|-----------|------------|---------------|
| **Firecrawl** | 12 | Скрапинг, краулинг, структурированное извлечение, браузерные сессии |
| **Jina** | 21 | Параллельный поиск, чтение URL, arxiv, PDF, дедупликация |
| **Exa** | 2 | Семантический поиск, поиск кода |
| **Perplexity** | 1 | AI-ответы с цитатами (Sonar Pro) |

## Установка

1. Скопируйте папку `deep-research` в директорию плагинов Claude Code:
   ```bash
   cp -r plugins/deep-research ~/.claude/plugins/deep-research
   ```

2. MCP-сервер настроен в `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "deep-research": {
         "type": "http",
         "url": "https://mcp.mcpware.net/mcp/YOUR-ENDPOINT-ID"
       }
     }
   }
   ```

3. Перезапустите Claude Code для подключения MCP-сервера.

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
| `deep-research` | Главный 7-шаговый алгоритм исследования |
| `search-strategies` | Выбор инструментов поиска и fallback-цепочки |
| `content-extraction` | Чтение URL, скрапинг, краулинг, PDF |
| `report-generation` | 3 шаблона отчётов |
| `examples` | Примеры и справочники |

## Fallback Logic

При ошибке primary инструмента — автоматическое переключение на следующий:

```
Поиск:     web_search_exa → search (Perplexity) → search_web (Jina)
Чтение:    read_url (Jina) → firecrawl_scrape → parallel_read_url
Краулинг:  firecrawl_crawl → firecrawl_map
Код:       get_code_context_exa → search_web → firecrawl_search
Академия:  search_arxiv → parallel_search_arxiv → search (Perplexity)
```

## Шаблоны отчётов

1. **Executive Summary** — Key Findings, Overview, Recommendations, Sources, Methodology
2. **Deep Research Report** — полный отчёт с Background, Findings, Analysis, Data, Quotes, Gaps
3. **Comparison Table** — таблица сравнения с Verdict и детальным анализом

Каждый отчёт содержит секцию **Methodology** с информацией об использованных инструментах, количестве запросов и источников.
