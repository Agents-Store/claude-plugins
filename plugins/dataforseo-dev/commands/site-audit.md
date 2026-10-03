---
description: Run an on-page SEO audit for a URL using DataForSEO
argument-hint: <url>
allowed-tools: [Read, Bash, Skill, mcp__plugin_dataforseo-dev_dataforseo__api_request, mcp__plugin_dataforseo-dev_dataforseo__docs_search]
---

# Site Audit

Run an on-page SEO audit with DataForSEO. Every data call is a paid `api_request`; read the docs first and get a budget before the first one.

## Instructions

1. Load the site-audit skill: invoke `/dataforseo-dev:site-audit` mentally (use its workflow patterns)
2. Plan before spending: call `docs_search` for each path below, list the calls, and ask the user to approve a budget (see the cost-awareness skill). No `api_request` before that answer.
3. Run these `api_request` calls in sequence on the provided URL (method POST, `data` is an array with one task):
   - `/v3/on_page/lighthouse/live/json` with `for_mobile: true` for the Lighthouse scores
   - `/v3/on_page/instant_pages` for page-level SEO data
   - `/v3/on_page/content_parsing/live` for structured content
4. If the user provided a domain (not a page URL), also run:
   - `/v3/domain_analytics/technologies/domain_technologies/live` with `target` set to the domain, to detect the tech stack
5. Present results as a structured audit report:
   - **Performance Score**: Lighthouse performance (0-100)
   - **SEO Score**: Lighthouse SEO (0-100)
   - **Accessibility Score**: Lighthouse accessibility (0-100)
   - **Tech Stack**: Detected technologies
   - **Issues Found**: List of specific problems with severity
   - **Recommendations**: Prioritized fixes

## Default Parameters

- enable_javascript: true
- for_mobile: true (for Lighthouse)
