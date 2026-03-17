# Scenario: Person/Company Lookup

**Query:** "Кто такой Anthropic — история, продукты, команда"
**Type:** Person/Company Lookup
**Depth:** standard
**Template:** Executive Summary

## Step-by-Step Execution

### Step 1: CLASSIFY
```
Signals: "кто такой", company name → Person/Company Lookup
Depth: standard
```

### Step 2: PLAN
```
Queries:
1. "Anthropic company overview history"
2. "Anthropic founders team leadership"
3. "Anthropic products Claude AI models"
4. "Anthropic funding valuation investors"
5. "Anthropic AI safety research mission"
```

### Step 3: SEARCH
```
web_search_exa({
  query: "Anthropic company overview products team",
  num_results: 10,
  type: "auto",
  category: "company"
})

search({ query: "Anthropic company history funding products team 2026" })
→ Perplexity AI answer with key facts

search_web({ query: "Anthropic AI safety research Claude models" })
```

### Step 4: READ
```
parallel_read_url({
  urls: [
    "https://anthropic.com/company",
    "https://anthropic.com/research",
    top_crunchbase_url,
    top_news_article_url,
    top_interview_url
  ]
})
```

### Step 5: EXTRACT
```
Key data points:
- Founded: date, location
- Founders: names, backgrounds
- Mission: AI safety focus
- Products: Claude models, API
- Funding: rounds, amounts, investors
- Team size
- Key milestones
```

### Step 6: SYNTHESIZE
```
Cross-check funding data across Crunchbase and news
Verify team info across multiple sources
Timeline of key events
```

### Step 7: REPORT
Output: Executive Summary with:
- Key Findings (5 bullet points)
- Overview (founding, mission, growth)
- Key Data Points table (funding, team, products)
- Timeline of milestones
- Sources (5+ URLs)
- Methodology

### Expected Tools Used
`web_search_exa`, `search`, `search_web`, `parallel_read_url`
