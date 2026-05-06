# nocodb-dev

NocoDB schema development plugin for Claude Code. Create and edit tables, fields (30+ types), views, relations, formulas, lookups, rollups, and webhooks via MCP discovery, the REST API, and the official `nc` CLI.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify NocoDB connection across MCP and CLI/API surfaces |
| **mcp-patterns** | Discovery-only MCP tools — `getTablesList`, `getTableSchema`, `getBaseInfo` |
| **api-reference** | NocoDB REST API guide. Bundled Data API + Meta API v3 OpenAPI specs, full Meta API endpoint reference, full field-type catalog |
| **cli-reference** | Official `nc` CLI reference focused on schema commands |
| **table-management** | Create, update, rename, duplicate, and delete tables |
| **field-management** | All 30 field types with config payloads — text, numeric, date, select, link, lookup, rollup, formula, button, etc. |
| **view-management** | Create and configure Grid, Kanban, Gallery, Form, Calendar, and Map views |
| **webhooks** | HookV3 lifecycle — triggers, notifications (URL, Email, Messaging, Script) |
| **dashboards** | Create dashboards and widgets — metric, bar/line/pie/donut chart, text, iframe |
| **workflows** | List, execute, and inspect NocoDB Workflows + executions |
| **troubleshoot** | Diagnose schema-side errors: read-only fields, type changes, relation cycles, formula syntax |
| **examples** | CRM and e-commerce schema build-out walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/nocodb-dev:create-table` | Create a new table with initial fields |
| `/nocodb-dev:create-field` | Add a field of any of the 30 supported types |
| `/nocodb-dev:list-fields` | List all fields on a table |
| `/nocodb-dev:create-view` | Create a Grid / Kanban / Gallery / Form / Calendar / Map view |
| `/nocodb-dev:add-relation` | Add a `LinkToAnotherRecord` field plus optional `Lookup` |
| `/nocodb-dev:add-webhook` | Configure a HookV3 webhook |

## Agent

**schema-architect** — Designs and applies schema changes. Discovers via MCP, plans the change, executes via API or CLI, and verifies.

## Installation

Enable the plugin in Claude Code. Set these environment variables:

```bash
# MCP — used by .mcp.json (read-only schema discovery)
export NOCODB_MCP_URL="https://your-nocodb-instance.com/mcp/your-path-id"
export NOCODB_MCP_TOKEN="your-xc-mcp-token"

# API / CLI — used by all schema-write operations
export NOCODB_URL="https://your-nocodb-instance.com"
export NOCODB_API_TOKEN="your-api-token"

export NOCODB_VERBOSE=1   # optional — show resolved IDs in CLI output
```

`.mcp.json` uses `${NOCODB_MCP_URL}` and `${NOCODB_MCP_TOKEN}` to configure the `nocodb` HTTP MCP server with `xc-mcp-token` header authentication. `NOCODB_URL` and `NOCODB_API_TOKEN` are used by the CLI and direct REST API calls — and **all schema-modification work uses these**, not the MCP token.

## Prerequisites

- NocoDB instance with MCP endpoint enabled (for discovery)
- Valid `xc-mcp-token` (NocoDB → Integrations → MCP)
- Valid API token (NocoDB → Account Settings → API Tokens)
- For CLI: `curl` + `jq` (Linux/macOS) or PowerShell 5.1+ (Windows)

## Why MCP Cannot Modify Schema

The shared NocoDB MCP server only exposes record/data tools (`createRecords`, `queryRecords`, `aggregate`, etc.) and read-only meta tools (`getTablesList`, `getTableSchema`, `getBaseInfo`). There are **no MCP tools for `createTable`, `createField`, `createView`, or any other schema CRUD**. Schema changes must go through the **REST API** or the **`nc` CLI**. This plugin uses the MCP only to discover state before and verify state after a schema change.

## CLI Setup (Required for Schema Work)

Install the official NocoDB CLI:

```bash
npx skills add nocodb/agent-skills
```

The CLI uses `NOCODB_URL` and `NOCODB_API_TOKEN` (plus optional `NOCODB_VERBOSE`).

## Related Plugins

- **nocodb-ops** — Record management, views, reports, filtering, and import/export for business users
- **nocobase-2-dev** — Adjacent low-code platform for full-stack app development
