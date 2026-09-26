# Learnings

## 2026-09-26 — plugin: Plugin superseded by n8n-dev and n8n-provision

**Problem:** Two newer plugins cover this one's surface: n8n-dev (workflow building, expressions, Code node, validation, against both current n8n MCP servers) and n8n-provision (template discovery and batch import). Keeping all three listed leaves users to guess which one to install.
**Fix:** Marked DEPRECATED in `plugin.json` and `marketplace.json`, pointing at n8n-dev and n8n-provision. Nothing removed.
**Root cause:** First-generation plugin (2026-03-12), written before the dev/provision split.
**Severity:** Minor
