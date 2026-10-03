---
description: Run keyword research for a topic or domain using DataForSEO
argument-hint: <keyword or domain>
allowed-tools: [Read, Bash, Skill, mcp__plugin_dataforseo-dev_dataforseo__api_request, mcp__plugin_dataforseo-dev_dataforseo__docs_search]
---

# Keyword Research

Run a keyword research workflow with DataForSEO. Every data call is a paid `api_request`; read the docs first and get a budget before the first one.

## Instructions

1. Load the keyword-research skill: invoke `/dataforseo-dev:keyword-research` mentally (use its workflow patterns)
2. Determine if the user provided a **keyword/topic** or a **domain**:
   - **Keyword/topic**: topic-based workflow (keyword_ideas, then keyword_overview, then search_intent)
   - **Domain**: competitor-based workflow (keywords_for_site, then ranked_keywords, then keyword_overview)
3. Plan before spending: call `docs_search` for each path in the chosen workflow, list the `api_request` calls with their `limit`, and ask the user to approve a budget (see the cost-awareness skill). No `api_request` before that answer.
4. Execute the workflow from the keyword-research skill:
   - `api_request` POST `/v3/dataforseo_labs/google/keyword_ideas/live` (topic) or `/v3/dataforseo_labs/google/keywords_for_site/live` (domain)
   - `api_request` POST `/v3/dataforseo_labs/google/keyword_overview/live` for volume, CPC and difficulty
   - `api_request` POST `/v3/dataforseo_labs/google/search_intent/live` to classify intent
5. Present results as a prioritized keyword table with columns: Keyword, Volume, Difficulty, CPC, Intent
6. Group results by search intent (informational, commercial, transactional, navigational)
7. Highlight quick wins (difficulty < 30, volume > 100)

## Default Parameters

- location_code: 2840 (United States; ask the user if different)
- language_code: "en" (ask the user if different)
- limit: 50 for initial discovery, then filter
