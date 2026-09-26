---
description: Compare multiple products, companies, or technologies
argument-hint: <item1> vs <item2> [vs <item3>...] [--criteria <criteria>]
---

# Compare

Comparative analysis of multiple items using the Comparison Table template. See CONNECTORS.md for provider mapping.

## Process

1. **Parse items** from arguments (split by "vs"):
   ```
   Items: [item1, item2, item3...]
   ```

2. **Search for each item** + comparison articles:
   ```
   ~~batch_search([
     "{item1} features pricing review",
     "{item2} features pricing review",
     "{item1} vs {item2} comparison"
   ])

   ~~search("{item1} vs {item2} vs {item3} comparison")
   ```

3. **Read and extract** from pricing/feature pages:
   ```
   ~~extract(
     urls: [item_pricing_urls],
     prompt: "Extract pricing plans and key features",
     schema: { plans with name, price, features }
   )

   ~~batch_scrape(comparison_article_urls)
   ```

4. **Synthesize** into Comparison Table:
   ```
   Deduplicate facts
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
