# Learnings

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
