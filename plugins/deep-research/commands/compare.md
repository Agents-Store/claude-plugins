---
description: Compare multiple products, companies, or technologies
allowed-tools: ["web_search_exa", "search", "parallel_search_web", "read_url", "parallel_read_url", "firecrawl_scrape", "firecrawl_extract", "sort_by_relevance", "deduplicate_strings"]
argument-hint: <item1> vs <item2> [vs <item3>...] [--criteria <criteria>]
---

# Compare

Comparative analysis of multiple items using the Comparison Table template.

## Process

1. **Parse items** from arguments (split by "vs"):
   ```
   Items: [item1, item2, item3...]
   ```

2. **Search for each item** + comparison articles:
   ```
   parallel_search_web([
     "{item1} features pricing review",
     "{item2} features pricing review",
     "{item1} vs {item2} comparison"
   ])

   web_search_exa({
     query: "{item1} vs {item2} vs {item3} comparison",
     num_results: 5
   })
   ```

3. **Read and extract** from pricing/feature pages:
   ```
   firecrawl_extract({
     urls: [item_pricing_urls],
     prompt: "Extract pricing plans and key features",
     schema: { plans with name, price, features }
   })

   parallel_read_url(comparison_article_urls)
   ```

4. **Synthesize** into Comparison Table:
   ```
   deduplicate_strings(all_facts)
   Build feature comparison matrix
   Analyze strengths/weaknesses per item
   ```

5. **Output** Comparison Table report with:
   - Feature comparison table
   - Detailed analysis per item
   - Verdict by use case
   - Sources + Methodology

## Example Usage
```
/compare Notion vs Linear vs Asana
/compare PostgreSQL vs MySQL vs MongoDB --criteria performance, scalability, ease of use
/compare React vs Vue vs Svelte
```
