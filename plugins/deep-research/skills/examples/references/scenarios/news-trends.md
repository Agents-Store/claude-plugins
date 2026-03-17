# Scenario: News & Trends

**Query:** "Последние новости AI regulation 2026"
**Type:** News & Trends
**Depth:** standard
**Template:** Executive Summary

## Step-by-Step Execution

### Step 1: CLASSIFY
```
Signals: "последние новости", "2026" → News & Trends
Depth: standard
```

### Step 2: PLAN
```
Queries:
1. "AI regulation news 2026"
2. "EU AI Act implementation 2026"
3. "US AI regulation executive order 2026"
4. "AI safety regulation latest developments"
5. "AI governance global policy updates"
```

### Step 3: SEARCH
```
search({ query: "latest AI regulation news and developments 2026" })
→ Perplexity for most recent AI answer

web_search_exa({
  query: "AI regulation policy 2026",
  num_results: 10,
  category: "news",
  start_published_date: "2025-09-01"
})
→ Exa filtered to recent news

parallel_search_web({
  queries: [
    "EU AI Act enforcement 2026",
    "US AI regulation legislation 2026",
    "China AI regulation updates"
  ]
})
```

### Step 4: READ
```
guess_datetime_url(all_urls) → filter for most recent only

sort_by_relevance("AI regulation 2026", recent_urls)

parallel_read_url(top_5_recent_urls)
```

### Step 5: EXTRACT
```
From each source:
- Regulation name/type
- Country/region
- Status (proposed, enacted, enforced)
- Key provisions
- Dates and deadlines
- Impact on industry
```

### Step 6: SYNTHESIZE
```
deduplicate_strings(news_items)
Build timeline of events
Group by region (EU, US, China, others)
Identify trends and patterns
```

### Step 7: REPORT
Output: Executive Summary with:
- Key Findings (top 5 developments)
- Overview (global AI regulation landscape)
- Key Data Points (table by region)
- Timeline of recent events
- Recommendations (what to watch)
- Sources (5+ recent URLs)
- Methodology

### Expected Tools Used
`search`, `web_search_exa` (with date filter), `parallel_search_web`, `guess_datetime_url`, `sort_by_relevance`, `parallel_read_url`, `deduplicate_strings`
