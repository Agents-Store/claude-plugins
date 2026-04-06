---
description: Run keyword research for a topic or domain using DataForSEO
argument-hint: <keyword or domain>
allowed-tools: [Read, Bash, Skill]
---

# Keyword Research

Run a comprehensive keyword research workflow using DataForSEO MCP tools.

## Instructions

1. Load the keyword-research skill: invoke `/dataforseo-dev:keyword-research` mentally (use its workflow patterns)
2. Determine if the user provided a **keyword/topic** or a **domain**:
   - **Keyword/topic**: Use topic-based research workflow (keyword_ideas → keyword_overview → search_intent)
   - **Domain**: Use competitor-based research workflow (keywords_for_site → ranked_keywords → keyword_overview)
3. Execute the appropriate workflow from the keyword-research skill
4. Present results as a prioritized keyword table with columns: Keyword, Volume, Difficulty, CPC, Intent
5. Group results by search intent (informational, commercial, transactional, navigational)
6. Highlight quick wins (difficulty < 30, volume > 100)

## Default Parameters

- location_name: "United States" (ask user if different)
- language_code: "en" (ask user if different)
- limit: 50 for initial discovery, then filter
