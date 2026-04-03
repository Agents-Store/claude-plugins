# LEARNINGS.md — web-search-dev

Accumulated fixes and discoveries for the web-search-dev plugin.

## 2026-04-03 — .mcp.json: Switch from user_config to standard env vars

**Problem:** `.mcp.json` used `${user_config.xxx}` variables and `plugin.json` had a `userConfig` section for API keys. This non-standard approach required plugin-specific config UI instead of using standard environment variables.
**Fix:** Replaced all `user_config` references with standard `${ENV_VAR}` syntax: `FIRECRAWL_API_TOKEN`, `EXA_API_KEY`, `JINA_API_KEY`, `PERPLEXITY_API_KEY`, `CONTEXT7_API_KEY`. Removed `userConfig` section from `plugin.json`. Added missing env vars for exa (header) and context7.
**Root cause:** Plugin was created using the `userConfig` pattern which is not the standard approach for Stack/Process plugins. Standard env var references (`${VAR}`) are simpler and consistent with other plugins.
**Severity:** Major

## 2026-03-31 — mcp-patterns, web-scraping: MCP tools must be preferred over WebFetch

**Problem:** During research/planning phases (e.g., exploring external data sources), Claude used the basic `WebFetch` tool instead of available MCP tools (Firecrawl, Exa, Jina, Perplexity). `WebFetch` is slower, produces lower-quality output, and rate-limits quickly (429 errors).
**Fix:** Added "Tool Priority" section to `mcp-patterns/SKILL.md` that explicitly states MCP tools MUST be used before `WebFetch`/`WebSearch` when available. Updated `web-scraping` skill description to trigger during research/exploration phases, not just explicit user scraping requests.
**Root cause:** Skills only triggered on explicit user scraping requests ("scrape this", "extract data"). No guidance existed for Claude's own research behavior — it defaulted to the basic built-in tools.
**Severity:** Major

## 2026-03-29 — multiple skills: remove deep-research plugin cross-references

**Problem:** Agent, README, and setup skill referenced the `deep-research` plugin, suggesting web-search-dev "complements" it. This made the plugin appear dependent on another plugin rather than standalone.
**Fix:** Removed all cross-references to deep-research plugin from agent system prompt, README, and setup skill. Kept Perplexity API `"deep-research"` preset references (those are legitimate API values, not plugin references).
**Root cause:** During initial creation, the plugin was designed with explicit differentiation from deep-research. The references were meant to help users choose between plugins, but they incorrectly positioned web-search-dev as subordinate.
**Severity:** Minor
