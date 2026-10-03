---
description: Compare a domain against its competitors using DataForSEO
argument-hint: <domain>
allowed-tools: [Read, Bash, Skill, mcp__plugin_dataforseo-dev_dataforseo__api_request, mcp__plugin_dataforseo-dev_dataforseo__docs_search]
---

# Competitor Analysis

Run a competitive analysis with DataForSEO. Every data call is a paid `api_request`; read the docs first and get a budget before the first one.

## Instructions

1. Load the competitor-analysis skill: invoke `/dataforseo-dev:competitor-analysis` mentally (use its workflow patterns)
2. Plan before spending: call `docs_search` for each path below, list the calls, and ask the user to approve a budget (see the cost-awareness skill). No `api_request` before that answer.
3. Execute this workflow for the provided domain (method POST, `data` is an array with one task):
   - `/v3/dataforseo_labs/google/competitors_domain/live` with `exclude_top_domains: true`, to discover competitors
   - `/v3/dataforseo_labs/google/domain_rank_overview/live`, once for the target and once for each of the top 3 competitors
   - `/v3/dataforseo_labs/google/domain_intersection/live` with the top competitor as `target1`, the target as `target2` and `intersections: false`, to find keyword gaps
   - `/v3/backlinks/bulk_ranks/live` with all the domains in `targets`, to compare backlink authority
4. Present results as a competitive landscape report:
   - **Domain Metrics Comparison**: Table comparing organic keywords, traffic, rank
   - **Top Competitors**: Ranked by relevance
   - **Keyword Gap Opportunities**: Keywords competitors rank for that the target doesn't
   - **Backlink Authority Gap**: Rank comparison
   - **Recommendations**: Quick win keywords to target, backlink strategies

## Default Parameters

- location_code: 2840 (United States; ask the user if different)
- language_code: "en" (ask the user if different)
- exclude_top_domains: true
- limit: 20 for competitors, 50 for keyword gaps
