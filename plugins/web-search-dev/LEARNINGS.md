# LEARNINGS.md — web-search-dev

Accumulated fixes and discoveries for the web-search-dev plugin.

## 2026-04-03 — .mcp.json: Corrupted npx cache breaks context7 MCP server

**Problem:** Context7 MCP server fails with `ERR_MODULE_NOT_FOUND: Cannot find module '@modelcontextprotocol/sdk/dist/esm/server/mcp.js'`. The npx cache at `~/.npm/_npx/` had `@upstash/context7-mcp@2.1.6` with `@modelcontextprotocol/sdk@1.27.0`, but the SDK's ESM dist only contained `.d.ts` type files — no `.js` runtime files.
**Fix:** Cleared the corrupted npx cache directory (`rm -rf ~/.npm/_npx/eea2bd7412d4593b`). Fresh `npx -y @upstash/context7-mcp` installs v1.0.21 with compatible `@modelcontextprotocol/sdk ^1.17.5` and works correctly.
**Root cause:** The npx cache had a stale/corrupted installation where `@upstash/context7-mcp@2.1.6` brought in `zod@^4.3.4` which is incompatible with `@modelcontextprotocol/sdk@1.27.0` (expects zod v3). This caused a partial/broken installation where JS runtime files were missing from the MCP SDK. The `-y` flag doesn't force re-download if npx finds an existing cache entry.
**Severity:** Critical

## 2026-04-03 — .mcp.json: Fix context7 API key passing for v2.x

**Problem:** Context7 MCP server fails to start. The `CONTEXT7_API_KEY` was set as a process env var, but @upstash/context7-mcp v2.x does not read API keys from environment variables in stdio mode.
**Fix:** Pass the API key as a CLI argument `--api-key ${CONTEXT7_API_KEY}` in the `args` array instead of using `env`.
**Root cause:** @upstash/context7-mcp v2.0+ changed its API key mechanism — stdio mode requires `--api-key` CLI arg, not env vars. The env var approach only works as an HTTP header for the remote transport mode.
**Severity:** Critical

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

## 2026-04-03 — .mcp.json: Fix exa, jina, context7 MCP server connections

**Problem:** Three MCP servers failing to connect: exa (used `mcp-remote` proxy unnecessarily), jina (`mcp-remote` sends wrong Accept headers causing HTTP 406), context7 (`CONTEXT7_API_KEY` as env var doesn't work for stdio/npx mode).
**Fix:** Exa: switched from `mcp-remote` to official `exa-mcp-server` npm package with `EXA_API_KEY` env var. Jina: switched from `mcp-remote` to native `type: http` transport with `url: https://mcp.jina.ai/v1` and `Authorization` header. Context7: removed non-functional `CONTEXT7_API_KEY` env var (API key is optional for free tier).
**Root cause:** `mcp-remote` was used as a stdio-to-HTTP proxy for exa and jina, but both servers now support native HTTP transport or have official npm packages. The proxy introduced incompatibilities (missing Accept headers for jina, unnecessary layer for exa). Context7's npm package doesn't read API keys from env vars in stdio mode.
**Severity:** Critical

## 2026-03-29 — multiple skills: remove deep-research plugin cross-references

**Problem:** Agent, README, and setup skill referenced the `deep-research` plugin, suggesting web-search-dev "complements" it. This made the plugin appear dependent on another plugin rather than standalone.
**Fix:** Removed all cross-references to deep-research plugin from agent system prompt, README, and setup skill. Kept Perplexity API `"deep-research"` preset references (those are legitimate API values, not plugin references).
**Root cause:** During initial creation, the plugin was designed with explicit differentiation from deep-research. The references were meant to help users choose between plugins, but they incorrectly positioned web-search-dev as subordinate.
**Severity:** Minor
