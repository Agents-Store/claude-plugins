# Scenario: Competitive Analysis

**Query:** "Сравни Notion vs Linear vs Asana для управления проектами"
**Type:** Competitive Analysis
**Depth:** standard
**Template:** Comparison Table

## Step-by-Step Execution

### Step 1: CLASSIFY
```
Signals: "сравни", "vs" → Competitive Analysis
Depth: standard (3 products to compare)
```

### Step 2: PLAN
```
expand_query({ query: "project management tools comparison" })

Queries:
1. "Notion project management features pricing 2026"
2. "Linear project management features pricing 2026"
3. "Asana project management features pricing 2026"
4. "Notion vs Linear vs Asana comparison review"
5. "best project management tool for teams 2026"
```

### Step 3: SEARCH
```
parallel_search_web({
  queries: [
    "Notion project management pricing features",
    "Linear project management pricing features",
    "Asana project management pricing features"
  ]
})

web_search_exa({
  query: "Notion vs Linear vs Asana comparison 2026",
  num_results: 5,
  type: "auto"
})

search({ query: "best project management tool comparison 2026" })
```

### Step 4: READ
```
sort_by_relevance("project management comparison", all_urls)

parallel_read_url({
  urls: [
    "https://notion.so/pricing",
    "https://linear.app/pricing",
    "https://asana.com/pricing",
    "top_comparison_article_url",
    "top_review_url"
  ]
})
```

### Step 5: EXTRACT
```
firecrawl_extract({
  urls: ["https://notion.so/pricing", "https://linear.app/pricing", "https://asana.com/pricing"],
  prompt: "Extract plan names, monthly prices, key features, and user limits",
  schema: {
    "type": "object",
    "properties": {
      "plans": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "price_monthly": { "type": "number" },
            "features": { "type": "array", "items": { "type": "string" } },
            "user_limit": { "type": "string" }
          }
        }
      }
    }
  }
})
```

### Step 6: SYNTHESIZE
```
deduplicate_strings(all_facts)
Cross-check pricing across official sites and review articles
Note discrepancies in feature comparisons
```

### Step 7: REPORT
Output: Comparison Table template with:
- Feature comparison table (pricing, features, integrations, UX)
- Detailed analysis per product (Strengths, Weaknesses, Best for)
- Verdict by use case
- Sources (5+ URLs)
- Methodology section

### Expected Tools Used
`parallel_search_web`, `web_search_exa`, `search`, `sort_by_relevance`, `parallel_read_url`, `firecrawl_extract`, `deduplicate_strings`
