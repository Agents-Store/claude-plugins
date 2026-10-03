# LEARNINGS.md — web-search-dev

Accumulated fixes and discoveries for the web-search-dev plugin.

## 2026-10 — Jina 21→12 tools, Perplexity messages, Firecrawl extract deprecated; media search moved to REST; image-search-dev merged here

**Problem:** (1) Jina's MCP server dropped 9 of 21 tools on 2026-09-18 (all `parallel_*` variants, `expand_query`, `classify_text`, `deduplicate_images`, `search_bibtex`, `show_api_key`); the plugin still taught them, so every such call ended in "tool not found". (2) `perplexity_ask` / `perplexity_reason` / `perplexity_research` take `messages: [{role, content}]`, not `query` — all examples failed validation. (3) `firecrawl_extract` and `firecrawl_research_search_github` return `DEPRECATED_TOOL` (extract was already deprecated in 3.23.6 although the 2026-08 refresh documented it as working); `find_tools` and `credit_usage` were undocumented; `firecrawl_crawl` was described as async although it polls to completion; `firecrawl_agent` documented a `model` parameter the MCP schema does not have; `firecrawl_interact` required `url` and `prompt` instead of one-of; `firecrawl_parse` documented `url` instead of `filePath`. (4) `resolve-library-id` requires `query` together with `libraryName` (Context7 4.x). (5) The agent had `tools: [Read, Write, Edit, Grep, Glob, Bash]`, which blocks every MCP tool for a subagent. (6) Pexels and Unsplash "MCP tools" were names from a private gateway server that no user can install; the sibling `image-search-dev` plugin documented the same names, with wrong rate limits (Unsplash production 1,000 not 5,000 req/hour; Pexels 200/hour plus 20,000/month) and "attribution not required" for Unsplash (it is required for API use; images must be hotlinked and the download event sent). (7) Exa: `agent_run` documented as a one-liner and as always opt-in; `web_search_exa` inline categories are only `company` and `people`; effort tier `max` is `ultra`; the URL-similarity endpoint is deprecated. (8) Perplexity Sonar presented as an equal path although support ended 2026-09-27; stale preset table. (9) CLI recipes with wrong flags (`map --allow-subdomains`, `interact <url> --prompt`, `monitor create <url>`); REST paths removed or moved (`/v2/browser`, `/v2/developer/search`, `/v2/research/papers/search`). (10) "Node.js 18+" while `firecrawl-mcp` needs 22+.

**Fix:** Rewrote the Firecrawl, Jina, Perplexity, Exa, Context7 references against the live tool schemas and the npm dist of firecrawl-mcp 3.27.x, exa-mcp-server 3.4.1, context7-mcp 4.1.1 and @perplexity-ai/mcp-server 1.3.0. Jina now documents exactly 12 tools with array inputs, `read_url` question mode, `return_url`, and server-side tool filtering. All `perplexity_*` examples use `messages`. Structured extraction is `firecrawl_scrape` with `formats: ["json"]` + `jsonOptions` (one URL) or `firecrawl_agent` + `firecrawl_agent_status` (unknown URLs); GitHub search is `firecrawl_developer_search`; Alexandria and `firecrawl_credit_usage` documented. Exa: `ENABLED_TOOLS` opt-in for the bundled server, `agent_run` parameters, advanced-search field names from the 3.4.1 schema. Removed the `tools:` line from the agent so it inherits the five MCP servers. Media search rewritten to public REST (`curl` with `PEXELS_API_KEY` / `UNSPLASH_ACCESS_KEY`), including the Unsplash checklist (hotlink `photo.urls.*`, `download_location`, attribution with utm parameters; no re-hosting) and Pexels `locale`; the "download and store" scenario is Pexels-only. `image-search-dev` content (Pexels `locale`, popular-video filters, collections, landing-page video recipe, attribution checklist) merged into `media-search` and `media-tools.md`; the plugin was removed from the marketplace and `renames["image-search-dev"]` points here. Removed-tool names appear only in this file; the other files describe the replacements.

**Root cause:** The 2026-08 refresh counted tools and parameters from tool names and READMEs instead of the live `tools/list` schemas, and the media tools were never verifiable because they belonged to a private server. Upstream cut Jina's surface and moved Perplexity to Agent API presets within two months of that refresh.

**Severity:** Critical

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
