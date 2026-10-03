# Learnings

## 2026-10-03 — flow-automation: sending item keys to a worker, write-back loops, signing (1.4.0)

**Problem:** A stack plugin carried the Flow settings for "item changed, hand it to a worker" in prose that was wrong in four places: it told readers to set the secret under "Settings → Environment Variables" (Directus has no such page; Flows read only `FLOWS_ENV_ALLOW_LIST`), to compute an HMAC of the body in a Run Script operation (the script runs in an isolated V8 context with no `crypto`, no Node modules and no network), to guard against loops with an expression (`{{ $trigger.payload.body }} != null AND ...`; the condition operation takes filter rules), and to rely on Directus retrying a failed webhook (the `request` operation makes one call).
**Fix:** New `references/send-items-to-a-worker.md`, linked from "Calling an External App": the request body with `event`, `collection` and `keys` (`$trigger.keys` is always an array and is rendered with `JSON.stringify` inside a string), ids instead of the item, the write-back loop guard as a `condition` with filter rules plus an idempotent receiver, and the signing options. One eval (id 30).
**Root cause:** The text had been written from memory of the Directus UI and never checked against the code. Checked now against the code Directus 12.4.1 ships (`@directus/api` 39.2.1 pulls `@directus/utils` 13.5.5): `renderMustache`, `validatePayload` with `requireAll` (what the `condition` operation calls) and the `exec` and `request` operations, and run with `applyOptionsData` and `validatePayload`: the keys render as `["a1","b2"]`; a payload with the source field passes the condition and the worker's write-back fails it; a missing `$env` value renders as `undefined`. The flow was not run end to end on a live instance.
**Severity:** Major

## 2026-10-03 — sdk-patterns, docker-local-dev, flow-automation, troubleshoot, api-reference: server-side use in Next.js and review items (1.3.0)

**Problem:** The stack plugin for Directus + Next.js carried SDK, Docker and Flow content that belongs here, and its code had errors (see its LEARNINGS). Here: `sdk-patterns/SKILL.md` was 526 lines; `docker-local-dev` published the Directus port on every interface, used `start_interval` without naming the Compose and Engine versions that support it, and the `.env` snippet wrote `${LOCAL_DIRECTUS_PORT}` where a `.env` file does not expand variables; the Access Control Model table did not name the system collections; the troubleshooting advice for `403` on `/assets/{id}` offered `?access_token=` in the URL, which leaks the token whenever the URL reaches a browser (`next/image` copies it into the HTML).
**Fix:** `sdk-patterns` gained `references/ssr-client.md` (server-only client, fetch options through `onRequest` and `withOptions` because `rest({ cache })` does not exist, typed commands for `directus_*` collections, `withToken`, the login and refresh contract: `expires` in milliseconds, single-use refresh tokens, CORS) and `references/content-queries.md` (relations as nested `fields` objects, many-to-many through the junction, `readSingleton`, typed `QueryFilter`, decimals arrive as strings). The content-versions and policies sections moved out of `SKILL.md` into `references/` (SKILL.md 526 to 470 lines). `docker-local-dev`: port bound to `127.0.0.1`, Compose 2.20.2 / Engine 25 stated, literal `DIRECTUS_URL=http://localhost:8055`, `CONTENT_SECURITY_POLICY_DIRECTIVES__FRAME_SRC` for Live Preview. `flow-automation` gained `references/notify-external-app.md` (event flow, `request` operation, the secret in a header read from `$env`, `FLOWS_ENV_ALLOW_LIST`). `api-reference` names `directus_policies`, `directus_permissions`, `directus_roles`, `directus_access`. `troubleshoot` and the Docker troubleshooting row now say: Public read on `directus_files` (unrestricted on the Core tier, which makes every file readable and listable) or a server route; never a token in a URL. Verified on a throwaway Directus 12.4.1: the Compose file starts healthy with the loopback port, a folder-restricted permission answers `403 RESOURCE_RESTRICTED` without a license while an unrestricted one is accepted, the refresh token is single use, `$env` in a flow is `undefined` without the allow-list, and the SDK calls behave as documented.
**Root cause:** The SDK and Docker knowledge was spread across a stack plugin instead of living with its tool; the asset advice predates the knowledge that `next/image` exposes the source URL.
**Severity:** Major

**Update 2026-10-03 (review):** The `RESOURCE_RESTRICTED` statement in `troubleshoot` is labelled as observed on Directus 12.4.1; the login and refresh contract in `references/ssr-client.md` is unchanged.

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
