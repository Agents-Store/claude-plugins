# Learnings

## 2026-09-26 — plugin: renamed from `teleshop` to `teleshop-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `teleshop-ops` — catalogue, orders and customers for store operators. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `teleshop` at `teleshop-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `teleshop:` to `teleshop-ops:`. The MCP server keeps its name `teleshop`.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
