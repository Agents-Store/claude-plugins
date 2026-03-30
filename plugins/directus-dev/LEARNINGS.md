# Learnings

## 2026-03-30 — troubleshoot: 403 section missing file asset authentication gotcha

**Problem:** The 403 troubleshooting section covered general permission issues but didn't mention the #1 403 gotcha: Directus file assets (`/assets/{id}`) returning 403 when accessed without authentication. Developers integrating with frontends (Next.js, React, etc.) hit this constantly.
**Fix:** Added a dedicated "403 on file assets" subsection documenting the two fix approaches (access_token in URL vs public role file read permission) and the opaque symptom when using `next/image`.
**Root cause:** Troubleshoot skill focused on API/collection permissions, overlooked file/asset access as a distinct permission category.
**Severity:** Major

## 2026-03-26 — plugin-wide: Remove hardcoded MCP server name prefix

**Problem:** Plugin shipped with `.mcp.json`, `mcpServers` in plugin.json, `tools: mcp__directus__*` in agents, and `allowed-tools: ["mcp__directus__*"]` in all 10 commands. This hardcodes the MCP server name to `directus`, breaking when users register it as `directus-1`, `cms`, `content_hub`, or any other name. Also violates Technology plugin rules — Level 1 plugins must not bundle MCP connections.
**Fix:** Deleted `.mcp.json`, removed `mcpServers` from plugin.json, removed `tools:` from both agents (inherit all session tools), removed `allowed-tools` from all 10 commands. Added MCP discovery instructions to assistant agent body. Updated README to explain project-scope MCP setup.
**Root cause:** Initial plugin generation treated directus-dev as a Process/Stack plugin rather than a Technology plugin. Technology plugins are knowledge-only — MCP connections belong in Stack plugins or the project's local config.
**Severity:** Critical

## 2026-03-30 — file-management: tags field type is string, not array

**Problem:** Skill examples showed `tags` as a JSON array (e.g., `["product", "hero"]`) in file import and update operations. The Directus MCP tool schema defines `tags` as `string | null`, causing validation errors: `Invalid input: expected string, received array`.
**Fix:** Removed array-formatted `tags` from all examples. Updated field reference table to document `tags` as `string | null` with a note about the validation constraint. Updated best practices to clarify tags should be comma-separated strings.
**Root cause:** Directus REST API accepts tags as arrays, but the MCP tool schema wraps the API with stricter typing that only accepts `string | null`. Skill was written against REST API docs, not the MCP schema.
**Severity:** Major
