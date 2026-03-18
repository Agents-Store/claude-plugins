---
description: Search the web using optimal provider with automatic fallback
argument-hint: <query> [--type <web|code|academic>]
---

# Web Search

Search the web with automatic fallback between providers. See CONNECTORS.md for provider mapping.

## Process

1. **Determine search type** from query or --type flag:
   - `web` (default): general web search
   - `code`: code and technical search
   - `academic`: arxiv and papers

2. **Execute search** with fallback chain:

   **Web search (~~search):**
   ```
   Try each provider: Exa → Perplexity → Jina → Firecrawl
   On error → next provider automatically
   ```

   **Code search (~~code_search):**
   ```
   Try: Exa code → ~~search + "github code"
   ```

   **Academic search (~~academic_search):**
   ```
   Try: Jina arXiv → Jina SSRN → Perplexity + "paper"
   ```

3. **Display results** with titles, URLs, and snippets.

## Example Usage
```
/search best RAG frameworks 2026
/search React server components --type code
/search transformer attention mechanism --type academic
```
