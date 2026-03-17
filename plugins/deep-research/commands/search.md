---
description: Search the web using optimal provider with automatic fallback
allowed-tools: ["web_search_exa", "search", "search_web", "parallel_search_web", "search_arxiv", "get_code_context_exa", "firecrawl_search"]
argument-hint: <query> [--provider <exa|perplexity|jina|firecrawl>] [--type <web|code|academic>]
---

# Web Search

Search the web with automatic fallback between providers.

## Process

1. **Determine search type** from query or --type flag:
   - `web` (default): general web search
   - `code`: code and technical search
   - `academic`: arxiv and papers

2. **Execute search** with fallback chain:

   **Web search:**
   ```
   web_search_exa({ query: "$ARGUMENTS" })
   → If error: search({ query: "$ARGUMENTS" })
   → If error: search_web({ query: "$ARGUMENTS" })
   ```

   **Code search:**
   ```
   get_code_context_exa({ query: "$ARGUMENTS" })
   → If error: search_web({ query: "$ARGUMENTS github code" })
   ```

   **Academic search:**
   ```
   search_arxiv({ query: "$ARGUMENTS" })
   → If error: search({ query: "$ARGUMENTS arxiv paper" })
   ```

3. **Display results** with titles, URLs, and snippets.

## Example Usage
```
/search best RAG frameworks 2026
/search React server components --type code
/search transformer attention mechanism --type academic
/search AI market trends --provider perplexity
```
