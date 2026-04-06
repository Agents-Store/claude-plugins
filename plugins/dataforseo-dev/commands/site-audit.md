---
description: Run an on-page SEO audit for a URL using DataForSEO
argument-hint: <url>
allowed-tools: [Read, Bash, Skill]
---

# Site Audit

Run a comprehensive on-page SEO audit using DataForSEO MCP tools.

## Instructions

1. Load the site-audit skill: invoke `/dataforseo-dev:site-audit` mentally (use its workflow patterns)
2. Run these tools in sequence on the provided URL:
   - `mcp__dataforseo__on_page_lighthouse` with `full_data: true` — get Lighthouse scores
   - `mcp__dataforseo__on_page_instant_pages` — get page-level SEO data
   - `mcp__dataforseo__on_page_content_parsing` — get structured content
3. If the user provided a domain (not a page URL), also run:
   - `mcp__dataforseo__domain_analytics_technologies_domain_technologies` — detect tech stack
4. Present results as a structured audit report:
   - **Performance Score**: Lighthouse performance (0-100)
   - **SEO Score**: Lighthouse SEO (0-100)
   - **Accessibility Score**: Lighthouse accessibility (0-100)
   - **Tech Stack**: Detected technologies
   - **Issues Found**: List of specific problems with severity
   - **Recommendations**: Prioritized fixes

## Default Parameters

- enable_javascript: true
- full_data: true (for Lighthouse)
