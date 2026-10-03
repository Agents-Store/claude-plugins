# LEARNINGS.md

Accumulated fixes and discoveries for the `nocodb-dev` plugin. Append entries chronologically (newest first). Format:

```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

## 2026-10 — nc CLI never existed; NOCODB_TOKEN; v3 payload keys; schema tools exist on Cloud/licensed

**Problem:** Five separate defects, all present in 1.1.0:
1. Every recipe called a CLI named `nc` (196 occurrences in 21 files). NocoDB has no such binary — on Linux/macOS `nc` is netcat, so the old recipes either hung or made netcat connect to a "host" named after the subcommand. The official CLI is `scripts/nocodb.sh` in the `nocodb/agent-skills` skill (renamed from `nc` on 2026-08-07 for exactly this reason), and it has no hook commands, no per-type view-create commands, no view-column or view-share commands.
2. The REST token variable was the old API-token name; the official script (and the root `.env.example`) use `NOCODB_TOKEN`.
3. Payloads were written in v2 style (`colOptions`, `linked_table_id`, `fk_*_column_id`, `calendar_range`, `subheading`, …) although the plugin's own bundled spec is v3: type-specific settings live in `options`, and several keys were renamed. Sorts used `order` instead of `direction`; filter groups used `logical_op` instead of `group_operator`.
4. Docs claimed the MCP server offers nothing for schema writes (tables, fields, views, hooks). Since NocoDB 2026.09.0 the server has them on Cloud and licensed self-hosted (199 tools in 2026.09.1) — they are just not in the tool list: `listTools(category)` reveals them, `callTool(name, arguments)` runs them. Community Edition still has record tools only.
5. The bundled OpenAPI specs were from 2026-05-07 and lacked the Docs API, `POST`/`DELETE …/fields/{fieldId}/options`, the Environments API and the gantt / timeline / list view types.

**Fix:** Rewrote every recipe as `curl` on Meta API v3 (a `nocodb_api` wrapper where a walkthrough repeats calls) with the matching MCP `callTool` form on Cloud/licensed; `cli-reference` now maps official `nocodb.sh` commands to REST calls and does not vendor the script (install with `npx skills add nocodb/agent-skills`). `NOCODB_TOKEN` everywhere, with one legacy-alias note in `setup`. Payloads rewritten to the v3 keys below. `mcp-patterns` carries the contract: Community = record tools only → REST; Cloud/licensed = MCP-first through `listTools` → `callTool`, REST as fallback. Both specs re-cut from NocoDB's current `swagger-v3.json` (meta + docs: 49 paths / 100 operations; data: 7 paths / 12 operations). New content: nine view types and `lock_type`, 35 field types, the select-options endpoints, Docs API, `getBaseSchema`, trash / audit tools, MCP workflow authoring. While rewriting, three more payload bugs against the bundled spec were fixed: hook notifications (messaging `type` is `Slack`/`Discord`/`Telegram`/`Whatsapp`/`Twilio` with only `payload.body`; Script payload key is `scriptId`; Email has no `cc`), dashboard widgets (`type` is `chart`/`metric`/`text`/`iframe`, `table_id` and `position` are top-level, charts select `options.chart_type`), and view `row_coloring` (`mode`, not `type`). The example scenario that showed a hook with `event: "after"` / a string `operation` was brought in line with the 2026-05-07 HookV3 correction below.

**Old key → v3 key** (everything type-specific moves inside `options`; only `title`, `type`, `description`, `default_value`, `unique` stay at the top level):

| Old | v3 |
|-----|----|
| `colOptions.options[]` (select) | `options.choices[{title, color?}]`; add/remove later via `…/fields/{fieldId}/options` |
| `linked_table_id` | `options.related_table_id` |
| `type_of_relation` | `options.relation_type` (`bt`, `hm`, `mm`, `oo`, `om`, `mo`) |
| classic link `parentId` / `childId` | gone — `related_table_id` + `relation_type` |
| Lookup `fk_relation_column_id` | `options.related_field_id` |
| Lookup `fk_lookup_column_id` | `options.related_table_lookup_field_id` |
| Rollup `fk_relation_column_id` / `fk_rollup_column_id` | `options.related_field_id` / `options.related_table_rollup_field_id` (`rollup_function` stays, inside `options`) |
| Rollup `countEmpty` / `countNotEmpty` | not in v3 — use `count`, `countDistinct`, `sumDistinct`, `avgDistinct` |
| `currency_code`, `date_format`, `time_format`, `precision`, `max`, `icon`, `color` (flat) | the same names inside `options` (Rating `max` → `options.max_value`; Duration `duration` → `options.duration_format`) |
| Barcode / QrCode `fk_column_id` | `options.barcode_value_field_id` (+ `barcode_format`) / `options.qrcode_value_field_id` |
| Button `action: {type: "url", url}` | `options: {type: "url", formula, label}` (also `webhook`, `script`, `ai`, `formula`) |
| `cdf` (default) | top-level `default_value` |
| Kanban `fk_grp_col_id` | `options.stack_by: {field_id, stack_order?}` |
| Gallery / Kanban `fk_cover_image_col_id` | `options.cover_field_id` |
| Calendar `calendar_range[{fk_from_column_id, fk_to_column_id}]` | `options.date_ranges[{start_date_field_id, end_date_field_id?}]` |
| Map `fk_geo_data_col_id` | `options.geo_data_field_id` |
| Form `subheading` / `success_msg` | `options.form_description` (+ `form_title`) / `options.thank_you_message` |
| Form `redirect_after_secs` / `show_blank_form` / `submit_another_btn` / `email` | `options.form_redirect_after_secs` / `reset_form_after_submit` / `show_submit_another_button` / `send_response_email_to` |
| Filter `fk_column_id` / `comparison_op` | `field_id` / `operator` |
| Filter group `logical_op` (`and`/`or`/`not`) | `group_operator` (`AND`/`OR`) |
| Sort `fk_column_id`, `order` | `field_id`, `direction` (`asc`/`desc`) |
| View-column commands | `PATCH` the view with the complete ordered `fields` list |

**Root cause:** The plugin was scaffolded from an older CLI-and-v2 mental model instead of from the bundled v3 spec and the real upstream repository, and nobody re-checked it when the upstream CLI was renamed (2026-08-07) and the MCP server grew its schema tools (2026-09). The 2026-05-07 entries below fixed paths and hook shapes but left the payload keys and the CLI name alone — and added a wrong "order" claim.
**Severity:** Critical

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

**Problem:** Filter and sort payloads documented as `{ fk_column_id, comparison_op, value }` and `{ fk_column_id, direction }` (the names used by an older generation of NocoDB tooling). Meta API v3 uses `field_id` + `operator` + `value` for filters and `field_id` + `direction` for sorts. *(Corrected 2026-10: this entry originally said sorts use `order`; the spec has always had `direction`.)*
**Fix:** Updated filter/sort recipes in `view-management/SKILL.md` and the corresponding section of `meta-api-endpoints.md`. *(The note added then — that the CLI translates between legacy names and `field_id` / `operator` / `order` — was wrong on both counts and was removed in 2026-10.)*
**Severity:** Major

## 2026-05-07 — coverage gap: Comments, Scripts, Dashboards, Widgets, Workflows, Members, Teams, Tokens

**Problem:** Initial scaffolding only covered Tables, Fields, Views, Hooks, Filters/Sorts. The actual Meta API v3 surface includes 8 additional domains (41 total paths, 84 operations): record Comments, base Scripts, Dashboards + per-dashboard Widgets, Workflows + Executions, Workspace + Base Members, Teams, and API Tokens. None of these were referenced in the plugin.
**Fix:** Added two new task-skills: `dashboards` (covers Dashboards + Widgets, all 7 ops with payload examples) and `workflows` (covers Workflows + Executions, all 5 ops with execution polling pattern). Documented Comments, Scripts, Members, Teams, Tokens as sections in `api-reference/references/meta-api-endpoints.md`. Updated `api-reference/SKILL.md` Meta API Quick Index to list every domain. Updated README.md and `schema-architect` agent skill-routing table to reference the new skills. Bumped plugin version 1.0.0 → 1.1.0 in `plugin.json` and marketplace.
**Severity:** Major
