---
description: Summarize a topic or URL content
allowed-tools: ["search", "read_url", "firecrawl_scrape", "parallel_read_url", "classify_text", "web_search_exa", "sort_by_relevance"]
argument-hint: <topic-or-url>
---

# Summarize

Quick summary of a topic or URL content.

## Process

1. **Detect input type:**
   - Starts with `http` → URL to summarize
   - Otherwise → topic to research and summarize

2. **For URL input:**
   ```
   read_url({ url: "$ARGUMENTS" })
   → If error: firecrawl_scrape({ url: "$ARGUMENTS", formats: ["markdown"] })

   classify_text({ text: content, labels: ["news", "tutorial", "research", "opinion", "documentation"] })

   Summarize: key points, main argument, data highlights
   ```

3. **For topic input:**
   ```
   search({ query: "$ARGUMENTS" })
   → Perplexity AI-summarized answer

   web_search_exa({ query: "$ARGUMENTS", num_results: 3 })
   → Top results for additional context

   read_url(top_result_url) → fuller context if needed
   ```

4. **Output** concise summary with:
   - Key points (3-5 bullets)
   - Main insights
   - Source URLs

## Example Usage
```
/summarize https://example.com/long-article
/summarize transformer architecture
/summarize latest developments in quantum computing
```
