# nocodb-dev

NocoDB schema development plugin for Claude Code. Create and edit tables, fields (35 types), views (9 types), relations, formulas, lookups, rollups, and webhooks — through the NocoDB MCP server (discovery on every edition, schema writes on Cloud / licensed self-hosted) and `curl` on the Meta API v3.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify NocoDB connection across the MCP and REST surfaces and detect the edition |
| **mcp-patterns** | The MCP contract — listed read/record tools, schema tools behind `listTools(category)` → `callTool`, Community vs Cloud/licensed |
| **api-reference** | NocoDB REST API guide. Bundled Data API + Meta API v3 OpenAPI specs, full Meta API endpoint reference, full field-type catalog |
| **cli-reference** | `curl` recipes by resource, mapped to the commands of the official `nocodb.sh` script |
| **table-management** | Create, update, rename, duplicate, and delete tables |
| **field-management** | All 35 field types with `options` payloads — text, numeric, date, select, link, lookup, rollup, formula, button, etc. |
| **view-management** | Create and configure Grid, Form, Gallery, Kanban, Calendar, Map, Gantt, Timeline, and List views |
| **webhooks** | HookV3 lifecycle — triggers, notifications (URL, Email, Slack/Discord/Telegram/Whatsapp/Twilio, Script) |
| **dashboards** | Create dashboards and widgets — metric, bar/line/pie/donut/scatter chart, text, iframe |
| **workflows** | List, execute, and inspect NocoDB Workflows + executions; author drafts over MCP on Cloud/licensed |
| **troubleshoot** | Diagnose schema-side errors: read-only fields, type changes, relation cycles, formula syntax |
| **examples** | CRM and e-commerce schema build-out walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/nocodb-dev:create-table` | Create a new table with initial fields |
| `/nocodb-dev:create-field` | Add a field of any of the 35 supported types |
| `/nocodb-dev:list-fields` | List all fields on a table |
| `/nocodb-dev:create-view` | Create a Grid / Kanban / Gallery / Form / Calendar / Map / Gantt / Timeline / List view |
| `/nocodb-dev:add-relation` | Add a `LinkToAnotherRecord` field plus optional `Lookup` |
| `/nocodb-dev:add-webhook` | Configure a HookV3 webhook |

## Agent

**schema-architect** — Designs and applies schema changes. Discovers via MCP, plans the change, applies it through the MCP schema tools (Cloud / licensed) or REST, and verifies.

## Installation

Enable the plugin in Claude Code. Set these environment variables:

```bash
# MCP — used by .mcp.json
export NOCODB_MCP_URL="https://your-nocodb-instance.com/mcp"        # Community Edition: .../mcp/<your-endpoint-id>
export NOCODB_MCP_TOKEN="your-mcp-token"

# REST — schema writes on Community Edition, and the fallback everywhere else
export NOCODB_URL="https://your-nocodb-instance.com"
export NOCODB_TOKEN="your-api-token"
```

`.mcp.json` uses `${NOCODB_MCP_URL}` and `${NOCODB_MCP_TOKEN}` to configure the `nocodb` HTTP MCP server with `xc-mcp-token` header authentication (still accepted; NocoDB's newer primary header is `x-api-key`). On Cloud you can also connect over OAuth at `https://app.nocodb.com/mcp` without a token. `NOCODB_URL` and `NOCODB_TOKEN` are used by direct REST (`curl`) calls — the MCP token is separate.

The REST token variable is `NOCODB_TOKEN` (the same name the official `nocodb.sh` reads); the former variable name and its alias handling are covered in the **setup** skill.

## Prerequisites

- A NocoDB instance with MCP enabled
- An MCP token — Cloud / licensed: Account Settings → **MCP** tab → New connection; Community Edition: Overview → Settings → Model Context Protocol → New MCP Endpoint
- An API token — NocoDB → Team & Settings → API Tokens
- For the `curl` recipes: `curl` + `jq`

## MCP Contract: Community vs Cloud / Licensed

| Edition | MCP server | Schema writes |
|---------|-----------|---------------|
| **Community Edition** | Record tools and read tools only (`getTablesList`, `getTableSchema`, `queryRecords`, `createRecords`, …) | REST (`curl` on Meta API v3) |
| **Cloud / licensed self-hosted** | The same listed tools, plus schema, view, hook, workflow, dashboard, script, permission and docs **write** tools that stay out of the tool list | **MCP first**: `listTools(category)` → `callTool(name, arguments)`; REST is the fallback |

On Cloud / licensed, call `listTools` with a category (`tables`, `fields`, `views`, `filters`, `sorts`, `hooks`, `workflows`, … — 32 in all), read the argument schemas it returns, and invoke the tool with `callTool`. `getBaseSchema` returns every table with its fields and views in one call. Check `listTools category: "tables"` once per session: if it names `createTable`, use MCP-first; otherwise use REST. The **mcp-patterns** skill has the details.

## Command Line

NocoDB has no standalone `nc` binary — `nc` is the netcat utility. The official command-line tool is the Bash script `nocodb.sh`, published as an agent skill: install it with `npx skills add nocodb/agent-skills`; the path to `nocodb.sh` is in that skill's README. It reads `NOCODB_TOKEN`, `NOCODB_URL` and `NOCODB_VERBOSE`. This plugin does not bundle the script — every recipe is plain `curl` on the Meta API v3, with the matching script command noted in the **cli-reference** skill.

## Related Plugins

- **nocodb-ops** — Record management, views, reports, filtering, and import/export for business users
- **nocobase-dev** — Adjacent low-code platform for full-stack app development
