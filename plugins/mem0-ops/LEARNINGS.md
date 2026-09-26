# Learnings

## 2026-09-26 — plugin: renamed from `mem0` to `mem0-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `mem0-ops` — memory CRUD through the Mem0 MCP server; nothing here teaches integrating Mem0 into code. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `mem0` at `mem0-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `mem0:` to `mem0-ops:`. The MCP server keeps its name `mem0`.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
