---
description: Compare a domain against its competitors using DataForSEO
argument-hint: <domain>
allowed-tools: [Read, Bash, Skill]
---

# Competitor Analysis

Run a comprehensive competitive analysis using DataForSEO MCP tools.

## Instructions

1. Load the competitor-analysis skill: invoke `/dataforseo-dev:competitor-analysis` mentally (use its workflow patterns)
2. Execute this workflow for the provided domain:
   - `mcp__dataforseo__dataforseo_labs_google_competitors_domain` with `exclude_top_domains: true` — discover competitors
   - `mcp__dataforseo__dataforseo_labs_google_domain_rank_overview` — get metrics for the target and top 3 competitors
   - `mcp__dataforseo__dataforseo_labs_google_domain_intersection` — find keyword gaps between target and top competitor
   - `mcp__dataforseo__backlinks_bulk_ranks` — compare backlink authority
3. Present results as a competitive landscape report:
   - **Domain Metrics Comparison**: Table comparing organic keywords, traffic, rank
   - **Top Competitors**: Ranked by relevance
   - **Keyword Gap Opportunities**: Keywords competitors rank for that the target doesn't
   - **Backlink Authority Gap**: Rank comparison
   - **Recommendations**: Quick win keywords to target, backlink strategies

## Default Parameters

- location_name: "United States" (ask user if different)
- language_code: "en" (ask user if different)
- exclude_top_domains: true
- limit: 20 for competitors, 50 for keyword gaps
