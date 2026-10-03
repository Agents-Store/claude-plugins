# stack-composable-stack-v1

Composable Stack v1 architecture plugin for Agents Store. It describes how PostgreSQL (direct MCP + PostgREST API), NocoDB, n8n, Trigger.dev and NocoBase fit together for data-driven applications with low-code interfaces — which layer does what, how data and events flow between the services, and how to bring a project up. It names its parts in `dependencies`; what one tool does and how to drive it is taught by that tool's own plugin.

## Architecture

| Layer | Service | Purpose |
|-------|---------|---------|
| Data | PostgreSQL | Relational database (source of truth) |
| Data | NocoDB | Spreadsheet interface + MCP access |
| Data | PostgreSQL MCP | Direct SQL access and database administration |
| Data | PostgREST API | REST API over PostgreSQL schema |
| Logic | n8n | Workflow automation |
| Logic | Trigger.dev | Background tasks and AI agents |
| Interface | NocoBase (prod) | Low-code admin UI — live data |
| Interface | NocoBase (dev) | Sandbox for building/testing tables, UX, menus, pages, workflows, and dev/test apps (API + MCP) |
| Interface | NocoDB | Data views and shared forms |

## Dependencies

Declared in `plugin.json` and installed together with the stack. They hold the tool-level knowledge:

| Plugin | Teaches |
|--------|---------|
| `postgresql-external-dev` | Schema design for NocoDB/NocoBase, the PostgreSQL MCP tools (`postgres-mcp-tools`), PostgREST (`postgrest-api`) |
| `nocodb-ops` | NocoDB MCP tools, filters, webhooks (`webhooks`) |
| `n8n-dev` | n8n workflows, n8n MCP (external and native), workflow sketches (`examples`) |
| `trigger-dev` | Trigger.dev tasks, CLI, MCP, record-driven task patterns (`task-development`) |
| `nocobase-dev` | NocoBase `nb` CLI, REST API (`api-reference`), workflows |

`n8n-provision` (provisioning an n8n instance) is not a dependency; install it separately if you need it.

## MCP Servers

This plugin's `.mcp.json` wires the stack's services in one place. Tools are named `mcp__plugin_stack-composable-stack-v1_<server>__<tool>`.

| Server | Transport | Service |
|--------|-----------|---------|
| `trigger-dev` | stdio | Trigger.dev task management |
| `n8n-mcp-external` | stdio | n8n workflow CRUD and node search |
| `n8n-native-mcp` | HTTP | n8n native MCP operations |
| `nocodb` | HTTP | NocoDB table and record operations |
| `postgresql-mcp` | HTTP | PostgreSQL direct SQL and admin tools |
| `nocobase-dev` | HTTP | NocoBase dev-instance MCP — targets `${NOCOBASE_DEV_URL}/api/mcp` |

Tool counts are not listed here because they drift between releases; ask the server.

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Set up environment, verify MCP connections |
| `data-access-selection` | Choose between NocoDB MCP, PostgreSQL MCP and PostgREST |
| `nocodb-to-n8n` | NocoDB → n8n integration patterns |
| `nocodb-to-trigger` | NocoDB → Trigger.dev integration patterns |
| `nocobase-to-n8n` | NocoBase → n8n integration patterns |
| `background-job` | Choose between Trigger.dev and n8n for background work; job status contract |
| `full-feature` | End-to-end feature recipe across all layers |

## Agent

- **stack-orchestrator** — Cross-layer coordinator for multi-service features

## Environment Variables

All managed via Infisical. Run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull secrets.

See `templates/.env.example` for the full list of required variables. Notable additions:

- `NOCOBASE_URL` / `NOCOBASE_API_KEY` — production NocoBase (live data)
- `NOCOBASE_DEV_URL` / `NOCOBASE_DEV_API_KEY` — dev-sandbox NocoBase for building and testing tables, UX elements, menus, pages, and workflows; also the auth pair behind the `nocobase-dev` MCP server and usable for API calls from dev/test apps

## Installation

Add to your `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "stack-composable-stack-v1@agents-store-claude-plugins": true
  }
}
```

Then run `/install-plugins` to install. The five technology plugins above come with it.
