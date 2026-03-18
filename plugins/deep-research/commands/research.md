---
description: Conduct comprehensive deep research on a topic using 7-step algorithm
argument-hint: <topic> [--type <competitive|market|technical|person|topic|news>] [--depth <quick|standard|deep>]
---

# Deep Research

Execute the full 7-step research algorithm from the `deep-research` skill. See CONNECTORS.md for provider mapping and fallback chains.

## Steps

1. **CLASSIFY** — determine research type from topic (or use --type flag)
2. **PLAN** — expand query, generate 3-7 search queries from different angles
3. **SEARCH** — ~~batch_search / ~~search with fallback
4. **READ** — ~~batch_scrape / ~~scrape top-5 pages with fallback
5. **EXTRACT** — key facts, data, quotes with source URLs
6. **SYNTHESIZE** — deduplicate, cross-check, assess confidence
7. **REPORT** — structured report using appropriate template + Methodology

For full algorithm details, query patterns per type, and quality checklist — see the `deep-research` skill.

## Example Usage
```
/research AI code assistants market 2026
/research Notion vs Linear vs Asana --type competitive
/research RAG pipeline architecture --type technical --depth deep
/research latest AI regulation news --type news
```
