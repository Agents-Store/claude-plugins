# LEARNINGS.md

Accumulated fixes and discoveries for the `nocodb-dev` plugin. Append entries chronologically (newest first). Format:

```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

## 2026-05-07 — webhooks: HookV3 shape correction

**Problem:** Initial draft documented the hook payload with `event: "before"|"after"`, a single-string `operation` (with `bulkInsert`/`bulkUpdate`/`bulkDelete` variants), and a top-level `condition` filter — none of which exist in the actual NocoDB v3 API. Worked examples and troubleshooting tables propagated this wrong shape into command files (`add-webhook.md`) and the troubleshoot skill.
**Fix:** Rewrote `HookV3Create` documentation to match the spec: `event` is `record`|`manual`, `operation` is an array of `insert`/`update`/`delete`, no top-level `condition` (use `trigger_fields` for change-gating, or a Script notification for richer logic). Updated webhooks/SKILL.md, add-webhook.md command, troubleshoot table, and the api-reference Hook section. All v3 hooks are async-after-commit; there is no synchronous-blocking variant.
**Root cause:** The initial scaffolding extrapolated a hook shape from older NocoDB versions and from generic webhook conventions, instead of probing the real OpenAPI spec.
**Severity:** Critical

## 2026-05-07 — api-reference: Meta API path version & structure

**Problem:** Documented the Meta API everywhere as `/api/v2/meta/...` with per-resource paths like `/api/v2/meta/columns/{columnId}`, `/api/v2/meta/views/{viewId}`, and per-view-type endpoints like `/api/v2/meta/tables/{tableId}/grids|forms|kanbans|...`. Real NocoDB v3 Meta API uses `/api/v3/meta/bases/{baseId}/...` everywhere, with one unified `POST .../views` endpoint that uses a `type` discriminator (`grid`/`gallery`/`kanban`/`calendar`/`map`/`form`) and a single `POST .../fields` endpoint instead of per-type endpoints.
**Fix:** Rewrote `api-reference/references/meta-api-endpoints.md` from scratch using the bundled `nocodb-meta-openapi.json` (15 303 lines, 41 paths, 84 operations). Bundled the spec as `references/nocodb-meta-openapi.json` alongside the existing data-api spec. Updated every `curl` example in `table-management`, `field-management`, `view-management`, `webhooks` SKILLs and in the `add-relation`/`add-webhook` commands to use v3 paths nested under `/bases/{baseId}/`. Replaced `field-management` API path-comments. Updated `field-types.md` reference path. Updated `schema-architect` agent.
**Root cause:** The initial scaffolding inferred path structure from the official `nc` CLI commands (which mirror v2 path semantics in some cases) rather than from a real OpenAPI spec for Meta v3. The user provided only the Data API spec at scaffolding time; the Meta API spec arrived later.
**Severity:** Critical

## 2026-05-07 — view-management / api-reference: Views are one endpoint with type discriminator

**Problem:** Documented six per-type endpoints (`/grids`, `/forms`, `/galleries`, `/kanbans`, `/calendars`, `/maps`) for view creation. The real Meta API has a single `POST /api/v3/meta/bases/{baseId}/tables/{tableId}/views` endpoint with `type` as a discriminator and view-specific config inside an `options` object (per `ViewCreate` / `ViewOptions*` schemas).
**Fix:** Rewrote the "Create a View" section of `view-management/SKILL.md` to use the unified endpoint with one `curl` example per type, all targeting the same path. Documented optional create-time extras (`sorts`, `filters`, `fields`, `row_coloring`).
**Root cause:** Same as the path-version issue — extrapolated from CLI subcommand naming.
**Severity:** Major

## 2026-05-07 — view-management: Filter/Sort field names

**Problem:** Filter and sort payloads documented as `{ fk_column_id, comparison_op, value }` and `{ fk_column_id, direction }` (the names used by the older `nc filter:create` / `nc sort:create` CLI commands). Meta API v3 uses `field_id` + `operator` + `value` for filters and `field_id` + `order` for sorts.
**Fix:** Updated filter/sort recipes in `view-management/SKILL.md` and the corresponding section of `meta-api-endpoints.md`. Added a note that the CLI translates between the legacy `fk_column_id` / `comparison_op` / `direction` names and the API's `field_id` / `operator` / `order`.
**Severity:** Major

## 2026-05-07 — coverage gap: Comments, Scripts, Dashboards, Widgets, Workflows, Members, Teams, Tokens

**Problem:** Initial scaffolding only covered Tables, Fields, Views, Hooks, Filters/Sorts. The actual Meta API v3 surface includes 8 additional domains (41 total paths, 84 operations): record Comments, base Scripts, Dashboards + per-dashboard Widgets, Workflows + Executions, Workspace + Base Members, Teams, and API Tokens. None of these were referenced in the plugin.
**Fix:** Added two new task-skills: `dashboards` (covers Dashboards + Widgets, all 7 ops with payload examples) and `workflows` (covers Workflows + Executions, all 5 ops with execution polling pattern). Documented Comments, Scripts, Members, Teams, Tokens as sections in `api-reference/references/meta-api-endpoints.md`. Updated `api-reference/SKILL.md` Meta API Quick Index to list every domain. Updated README.md and `schema-architect` agent skill-routing table to reference the new skills. Bumped plugin version 1.0.0 → 1.1.0 in `plugin.json` and marketplace.
**Severity:** Major
