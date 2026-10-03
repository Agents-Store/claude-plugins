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

## 2026-10-03 — api-reference, troubleshoot: roles and permissions taught the pre-v11 model

**Problem:** `POST /roles` examples carried the admin and app access flags, `POST /permissions` used `role`, and troubleshooting pointed at the Roles settings page. Since Directus 11 permissions belong to policies. On a live 12.4.1 instance a role payload with those flags is accepted with HTTP 200 and the flags are silently dropped, so the example looked successful and granted nothing; a permission with `role` fails with `FAILED_VALIDATION` (`policy` required).
**Fix:** Added Policies and Access sections (`/policies`, `/access`, `/permissions/me`), rewrote the role and permission examples (policy, permissions on the policy, role, access row), and moved troubleshooting to Settings → Access Policies. Verified every call against a throwaway Directus 12.4.1.
**Root cause:** Skill was written from pre-11 REST docs and never re-checked after the policies breaking change.
**Severity:** Critical

## 2026-10-03 — sdk-patterns: `login(email, password)` removed in SDK 20

**Problem:** The login example used two positional arguments. SDK 20+ takes one payload object; the old call throws (`Cannot use 'in' operator to search for 'otp'` in the password string). The default `authentication()` mode is `cookie`, which in a Node script returns no refresh token, and the refresh timer keeps one-shot scripts from exiting.
**Fix:** `login({ email, password }, options)` with `authentication('json')` for Node and `authentication('session', { credentials: 'include' })` for browsers, `stopRefreshing()` for scripts, plus content versions, policies and `schemaDiff` options for SDK 26. All snippets type-checked against `@directus/sdk` 26.0.0.
**Root cause:** SDK major versions were never tracked; the skill pinned no version.
**Severity:** Critical

## 2026-10-03 — flow-automation, troubleshoot, docker-local-dev: Directus 12 behavior changes

**Problem:** Update/Delete Items operations were documented without the 12.3.0 targeting rules (empty `key` and `query` now return `null`; a `query` without `limit` is capped at `QUERY_LIMIT_DEFAULT`, 100 by default), `/server/health` needs a token since 12.0.0, MCP registry mode and OAuth were missing, and there was no local Docker recipe. The upstream docs' compose health check (`wget` against `localhost`) reports the container unhealthy, because `wget` tries IPv6 first and Directus listens on IPv4.
**Fix:** Documented the operation targeting with `{"limit": -1}`, the Directus 12 notes (licensing, `COLLECTION_INACTIVE`, `IMPORT_MAX_FILE_SIZE`, `IP_TRUST_PROXY`), `?tool_mode=registry`, and added the `docker-local-dev` skill (127.0.0.1 health check, uid 1000 volume ownership, `LOCAL_` variable prefix so a shell-exported `DIRECTUS_*` cannot override `.env`). Verified on a throwaway 12.4.1 stack.
**Root cause:** Plugin targeted v11.12 and was not re-verified against v12 breaking changes.
**Severity:** Major
