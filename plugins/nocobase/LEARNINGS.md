# Learnings

## 2026-09-26 — plugin: Plugin superseded by nocobase-dev

**Problem:** nocobase-dev 2.0.0 bundles the official nocobase/skills library (auto-synced) and works through the `nb` CLI and REST API. This plugin's six hand-written skills cover a subset of that. Its one remaining unique part is the MCP server in `.mcp.json`.
**Fix:** Marked DEPRECATED in `plugin.json` and `marketplace.json`, pointing at nocobase-dev. Version parity restored at the same time (`plugin.json` said 1.1.0, the marketplace 1.0.0; both are now 1.2.0). Nothing removed.
**Root cause:** First-generation plugin (2026-03-12); the version drift came from a `plugin.json` bump that never reached the marketplace entry.
**Severity:** Minor
