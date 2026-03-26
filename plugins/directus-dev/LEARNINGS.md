# Learnings

## 2026-03-26 — plugin-wide: Remove hardcoded MCP server name prefix

**Problem:** Plugin shipped with `.mcp.json`, `mcpServers` in plugin.json, `tools: mcp__directus__*` in agents, and `allowed-tools: ["mcp__directus__*"]` in all 10 commands. This hardcodes the MCP server name to `directus`, breaking when users register it as `directus-1`, `cms`, `content_hub`, or any other name. Also violates Technology plugin rules — Level 1 plugins must not bundle MCP connections.
**Fix:** Deleted `.mcp.json`, removed `mcpServers` from plugin.json, removed `tools:` from both agents (inherit all session tools), removed `allowed-tools` from all 10 commands. Added MCP discovery instructions to assistant agent body. Updated README to explain project-scope MCP setup.
**Root cause:** Initial plugin generation treated directus-dev as a Process/Stack plugin rather than a Technology plugin. Technology plugins are knowledge-only — MCP connections belong in Stack plugins or the project's local config.
**Severity:** Critical
