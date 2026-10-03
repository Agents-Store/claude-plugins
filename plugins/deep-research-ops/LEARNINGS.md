# Learnings

## 2026-10-03 — plugin: fallback chains and tool reference moved to the live tools; web-search-dev declared as a dependency

**Problem:** After the 3.0.0 split the plugin ran on the servers of `web-search-dev`, but its chains and `docs/tool_reference.md` still named tools that no longer exist: Jina `parallel_search_web` / `parallel_read_url` / `parallel_search_arxiv` / `parallel_search_ssrn`, `expand_query`, `classify_text`, `deduplicate_images`, `search_bibtex`, `show_api_key`; Firecrawl `firecrawl_extract` and `firecrawl_browser_*`; Exa `get_code_context_exa`. A chain whose first step is a missing tool wastes a call, and the "Jina parallel -> multiple Exa" fallbacks never reached a working tool for `~~batch_search` and `~~batch_scrape`. The reference also used the wrong Perplexity tool name (`search`), documented `web_search_exa` with parameters its strict schema rejects, gave `firecrawl_search` a `lang` / `country` the schema does not have, presented Perplexity as "Sonar Pro", and counted tools ("36", "38") the plugin no longer owns. The `~~code_search` capability pointed at an Exa tool that is REST-only. The plugin used `web-search-dev` without declaring it.

**Fix:** `~~batch_search` is `search_web` with a query array (<=5), `~~batch_scrape` is `read_url` with a URL array (<=5), with `web_fetch_exa` and per-item calls behind them. `~~extract` is `firecrawl_scrape` with `formats: ["json"]` + `jsonOptions` (one URL per call), `firecrawl_agent` + `firecrawl_agent_status` for unknown URLs, then a model step over `~~scrape`. `~~code_search` is `firecrawl_developer_search`, then `web_search_advanced_exa` (opt-in). `~~academic_search` starts at `firecrawl_research_search_papers` (+ `read_paper`, `related_papers`), then `search_arxiv` / `search_ssrn`. New `~~deep_agent` for depth `deep` (`agent_run`, `firecrawl_agent`, `perplexity_research`). READ uses `read_url` with `question` / `topk` so only the relevant passages enter the context. Query planning and classification are model steps; text dedup is `deduplicate_strings`. Browser sessions are `firecrawl_interact` / `firecrawl_interact_stop`. Perplexity tools are `perplexity_search` (`query`, links only) and `perplexity_ask` / `reason` / `research` (`messages`) on the Agent API presets; a new `~~answer` capability (`perplexity_ask` -> `perplexity_reason` -> search results plus a model-written cited answer) carries the cited-answer role that `~~search` no longer implies. `web_fetch_exa` is called with `maxCharacters: 20000` (default 3000 per page), and the batch-scrape fallbacks are documented as ignoring `question`. Removed every tool count. `plugin.json` declares `"dependencies": ["web-search-dev"]` and the description says so. Removed-tool names appear only in this file; every tool the plugin still names was checked against the `web-search-dev` tool lists and the live MCP tool schemas. Version 3.0.0 -> 3.1.0 in `plugin.json` and `marketplace.json`.

**Root cause:** The chains were written for the bundled server of 2.x and copied unchanged through the 3.0.0 split; nothing compared them with the tool lists of the plugin that now provides the tools. Upstream cut Jina's surface (2026-09-18), deprecated Firecrawl's extract and browser tools, and moved Perplexity to Agent API presets within weeks.

**Severity:** Major

## 2026-09-30 — plugin: bundled mcpware MCP server removed

**Problem:** The only bundled MCP server, `deep-research`, pointed at a per-tenant gateway endpoint (`MCPWARE_MCP_URL`). Without that value the server failed on every session start, and the gateway dependency was dropped from the catalogue.
**Fix:** Deleted `.mcp.json` and the `mcpServers` field. The skills were already tool-agnostic (CONNECTORS pattern), so research runs on whatever search servers are installed — `web-search-dev` bundles all four providers. Major version bump: installed copies lose the `deep-research` server.
**Root cause:** A gateway tenant endpoint was the default wiring of a public plugin whose skills never needed it.
**Severity:** Major

## 2026-09-26 — plugin: renamed from `deep-research` to `deep-research-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `deep-research-ops` — research runs and reports for the person asking — no API or SDK teaching, so ops rather than dev. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `deep-research` at `deep-research-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `deep-research:` to `deep-research-ops:`. The MCP server keeps its name `deep-research`, and so does the `deep-research` skill — only the plugin was renamed.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
