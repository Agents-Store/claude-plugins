# Learnings

## 2026-09-26 — plugin: Plugin superseded by nocobase-dev

**Problem:** nocobase-dev 2.0.0 bundles the official nocobase/skills library (auto-synced) and works through the `nb` CLI and REST API. This plugin's six hand-written skills cover a subset of that. Its one remaining unique part is the MCP server in `.mcp.json`.
**Fix:** Marked DEPRECATED in `plugin.json` and `marketplace.json`, pointing at nocobase-dev. Version parity restored at the same time (`plugin.json` said 1.1.0, the marketplace 1.0.0; both are now 1.2.0). Nothing removed.
**Root cause:** First-generation plugin (2026-03-12); the version drift came from a `plugin.json` bump that never reached the marketplace entry.
**Severity:** Minor

## 2026-09-30 — mcp: The bundled MCP server no longer exists

**Problem:** `.mcp.json` launched `npx -y @nocobase/mcp-server`; npm now answers 404 for that package, so the server failed on every session start and no `mcp__nocobase__*` tool ever appeared. Found by the live plugin test (MCP handshake of every plugin server).
**Fix:** Removed `.mcp.json` and the `mcpServers` entry from `plugin.json`; version 1.2.1 in both manifests. The commands and agents still name `mcp__nocobase__*` tools, so they work again if the user registers a server called `nocobase` — NocoBase's built-in `/api/mcp` endpoint, as `stack-composable-stack-v1` wires it.
**Root cause:** Upstream withdrew the package; the workspace root config dropped the same server on 2026-09-29 (claude-plugins#9), the plugin kept it.
**Severity:** Minor
