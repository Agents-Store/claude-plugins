---
name: mcp-patterns
description: |
  NocoBase MCP tool transport conventions, the ~133 `*` tool catalog, the declarative-apply family, and the MCP → CLI → HTTP fallback chain. Use when:
  - "what NocoBase MCP tools are available?"
  - "how do I use nc-mcp?"
  - "which NocoBase tool should I call for..."
  - "NocoBase MCP reference"
  - "nc-mcp tool catalog"
  - "NocoBase flow_surfaces_apply"
  - "NocoBase collections_apply"
  - "fields_apply NocoBase"
  - "NocoBase declarative apply"
  - "nocobase-ctl fallback"
  - "NocoBase MCP vs CLI vs HTTP"
  - "load nc-mcp schemas"
  - "MCP tool discovery NocoBase"
---

# NocoBase MCP Patterns

The `nc-mcp` server is NocoBase's official MCP endpoint. It exposes roughly **133 tools** under the `*` prefix covering collections, records, workflows, UI composition (flow-surfaces), RBAC, data sources, and more.

This skill is the single source of truth for MCP-side conventions in `nocobase-dev`. Every other skill references this one for transport, naming, and discovery.

## Three-tier fallback chain

Every operation in this plugin is documented as:

1. **MCP first** — `*` tool call. Preferred when `nc-mcp` is connected; no URL/token plumbing needed because auth goes through the MCP transport.
2. **`nocobase-ctl` CLI second** — the upstream CLI wrapper. Preferred when MCP is unavailable but the CLI is installed on the host (e.g., on a NocoBase dev machine).
3. **HTTP curl third** — the raw REST API at `${NOCOBASE_URL}/api/{resource}:{action}` with `Authorization: Bearer ${NOCOBASE_API_KEY}`. Universal fallback, always works.

All three reach the same backend. Pick the first tier that is available.

## Loading tool schemas (do this once per session)

Tool schemas for `nc-mcp` are **deferred** — they show up as names only in the tool registry until loaded. Before invoking any tool, bulk-load schemas with one `ToolSearch` call:

```
ToolSearch(query: "nc-mcp", max_results: 30)
```

The keyword search matches the server-name substring in every tool name, so this single call returns the schemas for the whole toolkit. Do NOT load tools one at a time with `select:` — that's one round-trip per tool.

When a tool call returns `InputValidationError`, the schema wasn't loaded first. Run the `ToolSearch` above and retry.

## Tool name convention

Every `nc-mcp` tool uses the pattern:

```
{group}_{verb}[_{qualifier}]
```

Examples:
- `collections_list`
- `resource_create`
- `flow_surfaces_apply_blueprint`
- `roles_users_add`

When citing a tool in text use the full prefixed name so downstream agents can copy-paste directly. Never invent or abbreviate.

## Tool groups — quick orientation

Full catalog and per-group reference in [`references/nc-mcp-tool-map.md`](references/nc-mcp-tool-map.md).

| Group | Count | What it does |
|-------|-------|--------------|
| `auth_*` | 5 | Session lifecycle (`sign_in`, `sign_out`, `check`, `sign_up`, `change_password`) |
| `authenticators_*` | 7 | Auth-provider CRUD + type registry |
| `collections_*` + `collections_fields_*` | 16 | Schema CRUD on collections and fields |
| `collection_categories_*` | 6 | Sidebar grouping of collections |
| `fields_apply` | 1 | High-level field upsert |
| `resource_*` | 6 | Generic record CRUD across any collection — the data plane |
| `db_views_*` | 3 | Raw database view inspection and query (read-only) |
| `workflows_*` | 9 | Workflow CRUD, execute, sync, revision |
| `flow_nodes_*` | 7 | Workflow node editing |
| `executions_*` | 4 | Execution list, get, cancel, destroy |
| `jobs_*` | 3 | Background job list, get, resume |
| `user_workflow_tasks_*` | 1 | Approval inbox for current user |
| `flow_surfaces_*` | 40 | UI composition — pages, menus, tabs, popups, blocks, fields, actions, linkage/value rules, blueprints, templates |
| `desktop_routes_*` | 1 | Routing/menus for current user |
| `roles_*` | 15 | Role CRUD + scope/resource/route binding |
| `users_*` | 5 | User CRUD |
| `users_roles_*` | 3 | User↔role membership |
| `data_sources_*` | 7 | Multi-datasource CRUD |
| `available_actions_*` | 1 | ACL action registry (`view`, `create`, `update`, `destroy`, `export`, `importXlsx`) |

## The declarative-apply family

Three tools accept a full sub-tree spec and upsert it in one call. Prefer these over repeated low-level edits — they are idempotent, atomic, and match the upstream `applyBlueprint` pattern.

| Tool | Purpose |
|------|---------|
| `fields_apply` | Upsert fields inside an existing collection from a single `fields[]` array |
| `collections_apply` | Upsert a collection + all its fields in one call |
| `flow_surfaces_apply` | Replace a UI surface subtree (block, popup, page fragment) by `target.uid` |
| `flow_surfaces_apply_blueprint` | Create a full page + menu entry from a declarative blueprint |
| `flow_surfaces_apply_approval_blueprint` | Variant for approval-flow pages |

**Rule of thumb:** if you are making more than one `add_block`/`add_field`/`add_action` call on the same target, collapse them into a single `flow_surfaces_apply` with a combined `spec.subModels`. Fewer round-trips, atomic failure.

## Discovery workflow

Before operating on a live instance, introspect:

```
# What collections exist?
collections_list_meta()

# What ACL actions can I grant?
available_actions_list()

# What UI surfaces does this page expose?
flow_surfaces_catalog({ target: { uid: "<pageUid>" } })
flow_surfaces_describe_surface({ target: { uid: "<pageUid>" } })

# What reaction sources/targets are available at this node?
flow_surfaces_get_reaction_meta({ target: { uid: "<nodeUid>" } })
```

These four discovery calls replace guesswork. Always introspect before composing.

## Generic CRUD via `resource_*`

For record-level data work, the 6-tool `resource_*` family operates against **any** collection uniformly. No collection-specific tool, no schema needed per call.

| Tool | Purpose | Key params |
|------|---------|------------|
| `resource_list` | Paginated list of records | `resource`, `filter?`, `fields?`, `sort?`, `page?`, `pageSize?`, `appends?`, `dataSource?` |
| `resource_query` | Server-side aggregated query (group/measure/dim) | `resource`, `measures?`, `dimensions?`, `filter?` |
| `resource_get` | Fetch one record by primary key | `resource`, `filterByTk` |
| `resource_create` | Insert one record | `resource`, `values`, `sourceId?` |
| `resource_update` | Update by filter/pk | `resource`, `filterByTk`/`filter`, `values` |
| `resource_destroy` | Delete by filter/pk | `resource`, `filterByTk`/`filter` |

The `resource` param is the collection name (e.g. `"users"`, `"posts"`). The `dataSource` param scopes to a specific external DB (defaults to `main`).

## Filter syntax (shared across MCP + HTTP)

Filters use NocoBase's `$`-operator JSON. Same shape in MCP `filter` params and in HTTP `?filter=` query strings.

```json
{ "status": { "$eq": "published" } }
{ "$and": [{ "status": { "$eq": "open" } }, { "priority": { "$gte": 3 } }] }
{ "$or": [{ "assignee": { "$eq": null } }, { "assignee.role": { "$eq": "lead" } }] }
```

Common operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$notIn`, `$empty`, `$notEmpty`, `$includes`, `$dateOn`, `$dateBefore`, `$dateAfter`, `$startsWith`, `$endsWith`. Full list in `api-patterns/references/filter-operators.md`.

Association fields use dot notation: `{ "author.role": { "$eq": "admin" } }`.

## Fallback: CLI equivalents

The upstream `nocobase-ctl` CLI wraps the same MCP tools. Every MCP call has a CLI counterpart:

| MCP tool | CLI equivalent |
|----------|----------------|
| `collections_list` | `nocobase-ctl data-modeling collections list` |
| `collections_apply` | `nocobase-ctl data-modeling collections apply --body @spec.json` |
| `fields_apply` | `nocobase-ctl data-modeling fields apply --body @fields.json` |
| `resource_list` | `nocobase-ctl resource list --resource <name> --filter '<json>' -j` |
| `flow_surfaces_apply_blueprint` | `nocobase-ctl flow-surfaces apply-blueprint --body @page.json` |
| `flow_surfaces_get_reaction_meta` | `nocobase-ctl flow-surfaces get-reaction-meta --target-uid <uid>` |
| `workflows_execute` | `nocobase-ctl workflows execute --filter-by-tk <id> --body @ctx.json` |

Two-transport rule: the CLI passes the business object as raw JSON; MCP wraps the same object under a `requestBody` key in some surfaces. Check the schema for the exact param name — most tools take `requestBody`, a few take flat fields.

## Fallback: HTTP equivalents

Every MCP tool maps to an HTTP endpoint at `/api/{resource}:{action}`. Mapping is mechanical:

| MCP tool | HTTP equivalent |
|----------|-----------------|
| `collections_list` | `GET  /api/collections:list` |
| `collections_create` | `POST /api/collections:create` |
| `resource_list` with `resource:"posts"` | `GET  /api/posts:list` |
| `resource_create` with `resource:"posts"` | `POST /api/posts:create` |
| `workflows_execute` with `filterByTk:42` | `POST /api/workflows:execute?filterByTk=42` |
| `roles_users_add` | `POST /api/roles/{name}/users:add` |

For HTTP examples with headers and filter encoding, see `api-patterns`.

## Auth

MCP auth is handled by the MCP transport — no `Authorization` header needed in the tool call itself. The MCP host (claude.ai, IDE, or local stdio wrapper) negotiates auth once and reuses it.

HTTP auth uses `Authorization: Bearer ${NOCOBASE_API_KEY}` on every request. `X-Role: <roleName>` to impersonate a role. `X-Authenticator: <name>` to pick a specific authenticator when signing in.

CLI auth reads the active env from `~/.nocobase-ctl/config.json` (or the `NOCOBASE_CTL_ENV` env var).

## Practical rules

1. **Introspect before composing.** Always call `collections_list_meta`, `flow_surfaces_catalog`, or `available_actions_list` before writing mutating calls — field names and UIDs change.
2. **Prefer apply-family for bulk work.** One `collections_apply` or `flow_surfaces_apply_blueprint` beats a dozen granular calls.
3. **Never wrap the whole call in `try/catch` and ignore.** MCP surfaces NocoBase validation errors via the response body — parse them, show them to the user.
4. **Use `dataSource` for multi-DB.** Default is `main`. Pass `dataSource: "<key>"` on `resource_*` and `collections_*` to target an external DB.
5. **UID lifecycle.** After `flow_surfaces_apply_blueprint` or `_create_page`, normalize returned IDs: `navigation.group.routeId` and `desktopRoute.id` are navigation locators only — use `pageSchemaUid` for page-level `get`, and live `uid` values from `get`/`describe_surface` for lower-level calls.
6. **Fallback deliberately, not reactively.** If MCP returns an error, read it first. Most errors are permission or filter problems, not transport problems — don't silently retry with curl.

## See also

- `api-patterns` — HTTP Resource:Action URL pattern, query params, filter operators
- `api-reference` — full catalog of HTTP endpoints; MCP tool catalog lives in `references/nc-mcp-tool-map.md` (this skill)
- `ux-constructor` — flow-surfaces blueprint playbook (the big UI composition surface)
- `data-modeling` — schema design decisions before touching `collections_apply`
- `troubleshoot` — MCP error modes and fallback-chain debugging
