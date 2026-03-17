---
description: Conduct comprehensive deep research on a topic using 7-step algorithm
allowed-tools: ["web_search_exa", "search", "search_web", "parallel_search_web", "read_url", "parallel_read_url", "firecrawl_scrape", "firecrawl_extract", "search_arxiv", "get_code_context_exa", "expand_query", "sort_by_relevance", "deduplicate_strings", "classify_text", "guess_datetime_url", "extract_pdf"]
argument-hint: <topic> [--type <competitive|market|technical|person|topic|news>] [--depth <quick|standard|deep>]
---

# Deep Research

Conduct comprehensive research using the 7-step algorithm.

## Process

1. **CLASSIFY** the research type from the topic (or use --type if specified):
   - Competitive Analysis: "vs", "compare", "competitors"
   - Market Research: "market", "trends", "TAM"
   - Technical Audit: "architecture", "how works", "best practices"
   - Person/Company: names, "who is"
   - Topic Deep Dive: "explain", "deep dive"
   - News & Trends: "news", "latest", year/date

2. **PLAN** search queries:
   ```
   expand_query({ query: "$ARGUMENTS" })
   → Generate 3-7 queries from different angles
   ```

3. **SEARCH** using optimal tools with fallback:
   ```
   parallel_search_web(queries)
   web_search_exa(main_query)
   search(fact_question) [Perplexity]
   ```

4. **READ** top-5 relevant pages:
   ```
   sort_by_relevance(topic, urls)
   parallel_read_url(top_5_urls)
   ```

5. **EXTRACT** key facts, data, quotes with source URLs

6. **SYNTHESIZE** — deduplicate, cross-check, assess confidence:
   ```
   deduplicate_strings(facts)
   ```

7. **REPORT** using the appropriate template with Methodology section

## Example Usage
```
/research AI code assistants market 2026
/research Notion vs Linear vs Asana --type competitive
/research RAG pipeline architecture --type technical --depth deep
/research latest AI regulation news --type news
```
