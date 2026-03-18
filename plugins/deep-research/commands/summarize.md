---
description: Summarize a topic or URL content
argument-hint: <topic-or-url>
---

# Summarize

Quick summary of a topic or URL content. See CONNECTORS.md for provider mapping.

## Process

1. **Detect input type:**
   - Starts with `http` → URL to summarize
   - Otherwise → topic to research and summarize

2. **For URL input:**
   ```
   ~~scrape(url) → get content
   Classify content type (news, tutorial, research, etc.)
   Summarize: key points, main argument, data highlights
   ```

3. **For topic input:**
   ```
   ~~search(topic) → AI-summarized answer + top results
   ~~scrape(top_result_url) → fuller context if needed
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
