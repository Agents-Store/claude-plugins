# LEARNINGS.md — web-search-dev

Accumulated fixes and discoveries for the web-search-dev plugin.

## [2026-08-09] — fact-check: corrections from adversarial doc verification

**Problem:** Six claims refuted against live sources: (1) Firecrawl MCP tool count stated as 28 — the firecrawl-mcp@3.23.6 dist and the live hosted server both register exactly 27 tools; (2) `web_search_exa` documented with `type`/`category`/`includeDomains`/`excludeDomains`/date/`includeText`/`excludeText` parameters — its strict schema accepts only `query` and `numResults`, filters exist solely on the opt-in `web_search_advanced_exa` (type enum `auto`/`fast`/`instant`, academic category is `publication` not `research paper`, `includeText`/`excludeText` on neither tool); (3) `web_fetch_exa` documented with a required `url` string — the actual required parameter is `urls` (string[]) plus optional `maxCharacters` (default 3000/page); (4) Perplexity Gateway endpoint given as `/gateway/chat/completions` — the documented path is `POST https://api.perplexity.ai/router/v1/chat/completions`; (5) a Jina `X-Num` header documented for search result count — no such header exists, result count is the `num` field of the s.jina.ai request; (6) `pip install jina-grep` presented as working — the package is not published on PyPI as of 2026-08-09.

**Fix:** Changed 28→27 in firecrawl-tools.md, mcp-patterns/SKILL.md (×2), README.md, and amended the v1.1.0 LEARNINGS entry. Rewrote the exa-tools.md `web_search_exa` table to `query`+`numResults` only with inline `category:<type>` query syntax, moved all filters to the `web_search_advanced_exa` section with corrected enums, and switched the domain-scoped examples/fallbacks to `web_search_advanced_exa` across mcp-patterns, doc-search, media-search, troubleshoot, and the doc-search-workflow scenario; converted the content-pipeline scenario's `category` param to inline query syntax. Renamed `web_fetch_exa`'s parameter to `urls` (array) with `maxCharacters` default noted. Corrected the Gateway path in perplexity-api.md and api-reference/SKILL.md. Removed the `X-Num` header row and switched the s.jina.ai curl example to a `num` query parameter. Added a caveat to cli-recipes Local Mode that `jina-grep` is not installable from PyPI (upstream jina-cli docs reference it; see github.com/jina-ai/jina-grep-cli).

**Root cause:** The v1.1.0 refresh mixed REST-API capabilities into MCP tool tables (Exa filters/types exist only in the REST API and the advanced tool), miscounted the Firecrawl tool list under its own header, carried a Gateway path from a pre-release docs draft, inferred an `X-Num` header by analogy with other Jina X-* headers, and faithfully mirrored an upstream jina-cli instruction whose package was never published to PyPI.

**Severity:** Major

## [2026-08-09] — doc-alignment: Firecrawl v1→v2 migration, MCP tool renames, Perplexity preset renames

**Feature:** Aligned all skills with current official docs (v1.1.0). Firecrawl: REST endpoints moved to `/v2/` (26 stale `/v1/` references), `maxDepth`→`maxDiscoveryDepth`, `sitemap` enum, `prompt`-based crawl config, `maxAge` 2-day cache default, object-style formats; MCP `firecrawl_browser_*` replaced by `firecrawl_interact`/`firecrawl_interact_stop`, and ~16 new tools documented (parse, developer_search, monitors ×8, research ×5, feedback ×2 — 27 tools total; the entry originally said 28, corrected 2026-08-09 after recounting the firecrawl-mcp dist). SDK v4: `Firecrawl` class, `scrape()`/`crawl()`/`map()`/`batchScrape()` kwargs style. CLI: `view-config`, `interact`, `monitor`, `developer` commands. Exa: `crawling_exa`→`web_fetch_exa`, `get_code_context_exa` removed (routed to `firecrawl_developer_search`), `deep-lite` search type, `/answer`, `/contents` (URL-based), Agent API `/agent/runs`, docs moved to exa.ai/docs. Context7: tool names fixed from typo'd `contex7-*` gateway prefixes to bare `resolve-library-id`/`query-docs` (6 files), API key marked optional-with-benefits, remote MCP + `npx ctx7 setup` documented. Perplexity: Agent API presets renamed (`fast-search`→`fast`, `pro-search`→`low`, `deep-research`→`medium`, plus new `high`/`xhigh`/`wide-research`), Search API path is `/search` (no `/v1`), SDK namespaces fixed to `client.responses`/`client.chat.completions`/`client.search`, MCP tool backings updated, Gateway API added. Jina: 21 MCP tools (added `show_api_key`), reranker v3.5, reader/search rate limits split. Unsplash production tier corrected to 1,000 req/hr.

**Implementation:** Updated mcp-patterns (SKILL + all 6 service references), api-reference (SKILL + firecrawl/exa/perplexity/jina references), sdk-patterns, cli-recipes, web-scraping, doc-search, setup, examples (+ doc-search-workflow scenario), troubleshoot, agent, README. Version bumped 1.0.7 → 1.1.0. `.mcp.json` untouched — all five server entries verified working as-is.

**Rationale:** The live MCP servers and current API docs no longer match what the plugin taught: removed tools (`firecrawl_browser_*`, `crawling_exa`, `get_code_context_exa`), wrong tool names (`contex7-*` prefix from a private gateway users don't have), renamed presets, and a deprecated API generation would produce failing calls and non-compiling SDK code.

**Severity:** Critical

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
