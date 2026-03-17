# Tool Call Patterns

Паттерны вызовов всех 38 инструментов Deep Research Plugin. Названия без MCP-префиксов.

---

## Firecrawl (12 tools)

### firecrawl_scrape
```
firecrawl_scrape({
  url: "https://example.com/page",
  formats: ["markdown"],
  onlyMainContent: true
})
```
Minimal: `firecrawl_scrape({ url: "https://example.com" })`

### firecrawl_search
```
firecrawl_search({
  query: "AI automation tools comparison",
  limit: 10,
  lang: "en",
  country: "us",
  tbs: "qdr:m"
})
```
Minimal: `firecrawl_search({ query: "AI tools" })`

### firecrawl_crawl
```
firecrawl_crawl({
  url: "https://docs.example.com",
  limit: 20,
  maxDiscoveryDepth: 3,
  includePaths: ["/docs/*"],
  excludePaths: ["/admin/*"]
})
```
Minimal: `firecrawl_crawl({ url: "https://docs.example.com", limit: 20 })`

### firecrawl_check_crawl_status
```
firecrawl_check_crawl_status({ id: "crawl-job-uuid" })
```

### firecrawl_map
```
firecrawl_map({
  url: "https://docs.example.com",
  search: "API reference",
  limit: 100
})
```
Minimal: `firecrawl_map({ url: "https://docs.example.com" })`

### firecrawl_extract
```
firecrawl_extract({
  urls: ["https://example.com/pricing"],
  prompt: "Extract all pricing plans with names, prices, and features",
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
Minimal: `firecrawl_extract({ urls: ["https://example.com"], prompt: "Extract key info" })`

### firecrawl_agent
```
firecrawl_agent({
  prompt: "Research the top 5 vector databases and compare pricing and features",
  urls: ["https://pinecone.io", "https://weaviate.io"],
  schema: { "type": "object", "properties": { "databases": { "type": "array" } } }
})
```
Minimal: `firecrawl_agent({ prompt: "Research topic" })`

### firecrawl_agent_status
```
firecrawl_agent_status({ id: "agent-uuid" })
```

### firecrawl_browser_create
```
firecrawl_browser_create()
→ Returns: { session_id: "session-uuid" }
```

### firecrawl_browser_execute
```
firecrawl_browser_execute({
  session_id: "session-uuid",
  actions: [
    { type: "click", selector: "#load-more" },
    { type: "wait", milliseconds: 2000 },
    { type: "scrape" }
  ]
})
```

### firecrawl_browser_delete
```
firecrawl_browser_delete({ session_id: "session-uuid" })
```

### firecrawl_browser_list
```
firecrawl_browser_list()
→ Returns: list of active sessions
```

---

## Jina (21 tools)

### read_url
```
read_url({ url: "https://example.com/article" })
→ Returns: markdown content
```

### parallel_read_url
```
parallel_read_url({
  urls: [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
  ]
})
→ Returns: content for all URLs
```

### search_web
```
search_web({ query: "microservices best practices 2026" })
→ Returns: search results with snippets
```

### parallel_search_web
```
parallel_search_web({
  queries: [
    "RAG frameworks comparison",
    "vector database benchmarks 2026",
    "embedding models performance"
  ]
})
→ Returns: results for all queries
```

### search_arxiv
```
search_arxiv({ query: "retrieval augmented generation transformer" })
→ Returns: arxiv papers with abstracts
```

### parallel_search_arxiv
```
parallel_search_arxiv({
  queries: ["RAG transformer", "dense passage retrieval"]
})
```

### search_ssrn
```
search_ssrn({ query: "digital transformation impact SME" })
```

### parallel_search_ssrn
```
parallel_search_ssrn({ queries: ["fintech regulation", "digital banking"] })
```

### search_images
```
search_images({ query: "system architecture diagram microservices" })
```

### search_bibtex
```
search_bibtex({ query: "attention is all you need" })
→ Returns: BibTeX citation entries
```

### search_jina_blog
```
search_jina_blog({ query: "embeddings" })
```

### expand_query
```
expand_query({ query: "AI code assistant" })
→ Returns: related queries and terms
```

### classify_text
```
classify_text({
  text: "This article discusses the latest developments in quantum computing...",
  labels: ["technology", "science", "business", "politics"]
})
→ Returns: classification with confidence
```

### sort_by_relevance
```
sort_by_relevance({
  query: "machine learning deployment",
  documents: [
    "MLOps best practices for production",
    "History of artificial intelligence",
    "Deploying ML models at scale"
  ]
})
→ Returns: sorted by relevance
```

### deduplicate_strings
```
deduplicate_strings({
  strings: [
    "GPT-4 has 1.8T parameters",
    "GPT-4 reportedly has 1.8 trillion parameters",
    "LLaMA 3 was released by Meta"
  ]
})
→ Returns: deduplicated list
```

### deduplicate_images
```
deduplicate_images({ images: ["url1", "url2", "url3"] })
```

### extract_pdf
```
extract_pdf({ url: "https://arxiv.org/pdf/2301.00001" })
→ Returns: full text from PDF
```

### capture_screenshot_url
```
capture_screenshot_url({ url: "https://example.com" })
→ Returns: screenshot image
```

### guess_datetime_url
```
guess_datetime_url({ url: "https://blog.example.com/post-title" })
→ Returns: estimated publication date
```

### primer
```
primer()
→ Returns: Jina API overview and capabilities
```

### show_api_key
```
show_api_key()
→ Returns: current Jina API key
```

---

## Exa (2 tools)

### web_search_exa
```
web_search_exa({
  query: "best alternatives to Notion for team collaboration",
  num_results: 10,
  type: "auto",
  category: "company",
  start_published_date: "2025-01-01",
  end_published_date: "2026-12-31"
})
```
Minimal: `web_search_exa({ query: "Notion alternatives" })`

### get_code_context_exa
```
get_code_context_exa({
  query: "React server components implementation pattern"
})
```

---

## Perplexity (1 tool)

### search
```
search({
  query: "What is the current market size for AI code assistants in 2026?"
})
→ Returns: AI-synthesized answer with citations
```
