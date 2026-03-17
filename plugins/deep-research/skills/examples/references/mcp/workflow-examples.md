# Workflow Examples

5 многошаговых воркфлоу для типичных исследовательских задач.

---

## 1. Quick Web Search with Fallback

Быстрый поиск с автоматическим переключением при ошибке.

```
Step 1: web_search_exa({ query: "best RAG frameworks 2026", num_results: 5 })
        → If success: results with URLs
        → If error/empty: go to Step 2

Step 2: search({ query: "best RAG frameworks 2026" })
        → If success: Perplexity AI answer with citations
        → If error: go to Step 3

Step 3: search_web({ query: "best RAG frameworks 2026" })
        → Jina fallback results

Step 4: read_url(best_result_url)
        → Get full content from top result
```

---

## 2. Parallel Research Batch

Массовый параллельный поиск для глубокого исследования.

```
Step 1: expand_query({ query: "AI code assistant market" })
        → Related terms: "copilot", "code completion", "AI IDE", "developer tools"

Step 2: parallel_search_web({
          queries: [
            "AI code assistant market size 2026",
            "copilot vs cursor vs cody comparison",
            "AI developer tools funding investment",
            "code completion tools benchmark"
          ]
        })
        → Batch results from all queries

Step 3: sort_by_relevance({
          query: "AI code assistant market",
          documents: [all_result_urls]
        })
        → Ranked by relevance

Step 4: parallel_read_url({
          urls: [top_5_ranked_urls]
        })
        → Content from best sources

Step 5: deduplicate_strings({
          strings: [extracted_facts]
        })
        → Clean, unique facts for report
```

---

## 3. Site Analysis

Анализ целого сайта — документация, структура, контент.

```
Step 1: firecrawl_map({
          url: "https://docs.example.com",
          search: "API reference"
        })
        → List of all relevant URLs

Step 2: Select key URLs from map results (docs, API, guides)

Step 3: parallel_read_url({
          urls: [key_page_urls]
        })
        → Content from important pages

Step 4: firecrawl_crawl({
          url: "https://docs.example.com/api",
          limit: 15,
          maxDiscoveryDepth: 2
        })
        → crawl_id

Step 5: firecrawl_check_crawl_status({ id: crawl_id })
        → Repeat until "completed"

Step 6: Synthesize map + read + crawl results into report
```

---

## 4. Academic Research

Поиск и анализ научных статей.

```
Step 1: search_arxiv({ query: "retrieval augmented generation evaluation" })
        → List of papers with abstracts

Step 2: parallel_search_arxiv({
          queries: [
            "RAG evaluation metrics",
            "retrieval augmented generation benchmarks"
          ]
        })
        → Additional papers

Step 3: Select top papers by relevance

Step 4: extract_pdf({ url: "https://arxiv.org/pdf/PAPER_ID" })
        → Full text of key papers

Step 5: parallel_read_url({
          urls: [paper_landing_pages]
        })
        → Abstracts and metadata

Step 6: search({ query: "RAG evaluation current state of the art 2026" })
        → Perplexity summary for context

Step 7: Synthesize into Deep Research Report with:
        - Key findings from papers
        - Methodology comparison
        - BibTeX citations
```

---

## 5. Code Investigation

Исследование кода, технических реализаций и паттернов.

```
Step 1: get_code_context_exa({
          query: "React server components streaming SSR implementation"
        })
        → Code examples and technical context

Step 2: search_web({ query: "React server components best practices 2026" })
        → Blog posts and tutorials

Step 3: read_url({ url: "https://react.dev/reference/rsc/server-components" })
        → Official documentation
        → If error: firecrawl_scrape(url, formats: ["markdown"])

Step 4: firecrawl_map({
          url: "https://react.dev/reference",
          search: "server components"
        })
        → Find all related doc pages

Step 5: parallel_read_url({
          urls: [related_doc_pages]
        })
        → Full documentation content

Step 6: Synthesize into Technical Audit Report with:
        - Architecture overview
        - Implementation patterns
        - Code examples
        - Best practices
        - Common pitfalls
```
