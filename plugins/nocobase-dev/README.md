# nocobase-dev

NocoBase V2 development plugin for the Agents Store. Full customization + data management reference covering the official `nc-mcp` MCP server (~146 tools), the `nocobase-ctl` CLI, and the HTTP API.

## What This Plugin Covers

- **MCP tool catalog** -- `nc-mcp` tools organized by domain (flow-surfaces, collections, resources, workflows, RBAC, data sources, etc.)
- **Collections & Fields** -- Create, modify, and manage data collections and their fields across MCP/CLI/HTTP
- **Data Modeling** -- Schema design playbook: collection types, field types, relations, model archetypes, verification
- **Record Operations** -- CRUD, aggregation (`resource_query`), filtering, pagination, associations, import/export
- **Workflow Automation** -- Workflows, nodes (28 types), triggers (7 types), executions, jobs, approval inbox
- **UI Composition via Flow Surfaces** -- Blueprints, blocks, tabs, popups, record actions, linkage rules, value rules, templates
- **Flow Models (v2 block engine)** -- Low-level flow model CRUD, flowSql with Liquid templates, variables
- **UI Schemas (legacy v1)** -- Maintenance-only reference for v1 pages
- **Routes & Menus** -- Desktop/mobile route structure, tabs, role-based access
- **Data Sources** -- External database connections, multi-DB scoping
- **Data Visualization** -- Charts plugin + MCP-native aggregation
- **Authentication & ACL Governance** -- Users, roles, authenticators, RBAC scopes, API keys, SSO, risk-gated ACL changes
- **Localization** -- Multi-language support
- **Plugin Development** -- Scaffolding, server/client-v2 APIs, lifecycle hooks, migrations, custom actions, i18n
- **Publish Management** -- Cross-environment publishing (risk-gated, opt-in)
- **System Administration** -- Settings, storage, plugins, app lifecycle, background jobs

## MCP Support

This plugin is a **pure technology plugin** — it contains knowledge, not infrastructure. The `nc-mcp` server is detected opportunistically; when connected, skills document MCP-first tool calls, with `nocobase-ctl` CLI and HTTP curl as explicit fallbacks.

**Transport fallback chain used throughout the skills:**
1. **MCP** — `*` tools (native NocoBase MCP, ~146 tools)
2. **`nocobase-ctl` CLI** — upstream CLI wrapper around the MCP tools
3. **HTTP curl** — raw REST API at `${NOCOBASE_URL}/api/{resource}:{action}`

To load MCP tool schemas in a fresh session, bulk-load them once:

```
ToolSearch(query: "nc-mcp", max_results: 30)
```

Full catalog grouped by domain lives in `skills/mcp-patterns/references/nc-mcp-tool-map.md`.

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify NocoBase connectivity across MCP/CLI/HTTP |
| `mcp-patterns` | MCP transport conventions, tool catalog, declarative-apply family, fallback chain |
| `api-patterns` | HTTP URL pattern, MCP⇄HTTP mapping, filter operators, pagination, utils (formulajs, mathjs, filter, UID) |
| `api-reference` | Complete HTTP endpoint reference + pointer to MCP tool catalog |
| `data-modeling` | Schema design: collection types, field types, relations, model archetypes, verification |
| `collections-and-fields` | Operational CRUD on collections/fields across MCP/CLI/HTTP |
| `record-operations` | Data CRUD + aggregation via `resource_*` + `db_views_*` |
| `workflow-automation` | Workflows, nodes (28 types), triggers (7 types), executions, jobs, approval inbox |
| `ui-builder-index` | Router: ux-constructor vs flow-models vs ui-schemas |
| `ux-constructor` | Modern page v2 — `flow_surfaces_*` blueprints, blocks, reactions, templates, patterns |
| `flow-models` | Low-level v2 block engine (flowModels, flowSql, variables) |
| `ui-schemas` | Legacy v1 UI schema maintenance |
| `routes-and-menus` | Desktop/mobile routes, menus, tabs, role-based access |
| `data-sources` | External DB connections, multi-DB scoping |
| `data-visualization` | Charts + MCP-native aggregation |
| `auth-and-users` | Auth, users, roles, ACL governance (full RBAC surface, 23 MCP tools) |
| `localization` | Multi-language support |
| `plugin-development` | Plugin scaffold, server/client-v2 playbook, pm CLI |
| `publish-manage` | Cross-env publishing (risk-gated, `disable-model-invocation: true`) |
| `system-admin` | System settings, storage, plugins, app lifecycle, jobs |
| `troubleshoot` | Transport-aware error diagnosis, MCP error modes, fallback-chain debugging |
| `examples` | End-to-end scenario walkthroughs (CRM, workflows, project management, i18n, MCP page authoring, MCP workflow build) |

## Agent

- **nocobase-developer** -- NocoBase specialist with MCP-first + CLI + HTTP fallback, collection/workflow/UI/ACL/publishing coverage, and upstream hard rules preserved (never use `this.app.use()`, client-v2 only, etc.)

## Prerequisites

- A running NocoBase V2 instance
- EITHER an API key with appropriate permissions (for HTTP) OR the `nc-mcp` MCP server connected (for MCP) OR `nocobase-ctl` installed (for CLI)

## Configuration

When enabling this plugin, you'll be prompted for:
- **nocobase_url** -- Your NocoBase instance URL (e.g., `https://your-nocobase.com`)
- **nocobase_api_key** -- Your NocoBase API key

These values are used in HTTP curl examples throughout the skills as `${NOCOBASE_URL}` and `${NOCOBASE_API_KEY}`. MCP connections are handled by the MCP host (no credentials needed in-skill); CLI uses `~/.nocobase-ctl/config.json`.

## Environment Variables

For your project code, set these environment variables:
- `NOCOBASE_URL` -- NocoBase instance URL
- `NOCOBASE_API_KEY` -- NocoBase API authentication key

## Changelog

### 1.5.0 — 2026-04-20 — MCP coverage + upstream skill content

- Added `mcp-patterns` skill documenting ~146 `nc-mcp` tools across 20 groups
- Added `data-modeling` skill with upstream design playbook (collection types, relations, model packs, decision matrix, verification)
- Added `ui-builder-index` router skill
- Added `publish-manage` skill for risk-gated cross-env publishing (disable-model-invocation)
- Extended all 18 existing skills with MCP → CLI → HTTP fallback chain
- Merged upstream nocobase-skills content (github.com/nocobase/skills) for data-modeling, acl-manage, workflow-manage, plugin-development, plugin-manage, env-bootstrap, ui-builder, utils
- Split `ux-constructor/SKILL.md` — verified classic algorithm moved to `references/verified-classic-algorithm.md` to keep SKILL.md under 900 LOC
- Added MCP-first scenarios to `examples`: page authoring via `flow_surfaces_apply_blueprint`, workflow build via `workflows_*`
- Updated `nocobase-developer` agent with MCP tools, MCP→CLI→HTTP fallback rule, and upstream hard rules

### 1.4.0 — 2026-04-13 — enrichment from nocobase ops plugin

Plugin-development skill, enriched collections-and-fields/workflow-automation, evals for 7 skills.

### 1.0.0 — initial release
