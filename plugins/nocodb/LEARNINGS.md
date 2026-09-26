# Learnings

## 2026-09-26 — plugin: Plugin superseded by nocodb-dev and nocodb-ops

**Problem:** The plugin teaches snake_case MCP tools (`list_records`, `create_table`, `search_records`, …) that the current NocoDB MCP server does not expose; its tools are camelCase (`queryRecords`, `getTablesList`, `createRecords`). nocodb-dev and nocodb-ops already cover the same surface with the current names.
**Fix:** Marked DEPRECATED in `plugin.json` and `marketplace.json`, pointing at nocodb-dev and nocodb-ops. Nothing removed; installed copies keep working as before.
**Root cause:** First-generation plugin (2026-03-12), written before the dev/ops split and not updated when the server's tool names changed.
**Severity:** Minor
