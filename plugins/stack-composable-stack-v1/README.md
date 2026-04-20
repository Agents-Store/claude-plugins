# stack-composable-stack-v1

Composable Stack v1 dev plugin for Agents Store. Integrates PostgreSQL (direct MCP + PostgREST API), NocoDB, n8n, Trigger.dev, and NocoBase via MCP for building data-driven applications with low-code interfaces.

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

## MCP Servers

| Server | Transport | Service |
|--------|-----------|---------|
| `trigger-dev` | stdio | Trigger.dev task management |
| `n8n-mcp-external` | stdio | n8n workflow CRUD and node search |
| `n8n-native-mcp` | HTTP | n8n native MCP operations |
| `nocodb` | HTTP | NocoDB table and record operations |
| `postgresql-mcp` | HTTP | PostgreSQL direct SQL and admin tools (27 tools) |
| `nocobase-dev` | HTTP | NocoBase dev-instance `nc-mcp` (~146 tools: collections, fields, resources, workflows, flow-surfaces, RBAC) — targets `${NOCOBASE_DEV_URL}/api/mcp` |

## Skills

| Skill | Description |
|-------|-------------|
| `postgresql-api` | PostgreSQL MCP tools and PostgREST API usage |
| `init-project` | Set up environment, verify MCP connections |
| `nocodb-to-n8n` | NocoDB → n8n integration patterns |
| `nocodb-to-trigger` | NocoDB → Trigger.dev integration patterns |
| `nocobase-to-n8n` | NocoBase → n8n integration patterns |
| `background-job` | Background task patterns with Trigger.dev and n8n |
| `full-feature` | End-to-end feature recipe across all layers |

## Agent

- **stack-orchestrator** — Cross-layer coordinator for multi-service features

## Prerequisites

### Technology Plugins (install these first)

- `trigger-dev` — Trigger.dev development knowledge
- `n8n-dev` — n8n workflow development knowledge
- `nocodb-ops` — NocoDB data operations
- `nocobase-dev` — NocoBase development knowledge
- `postgresql-external-dev` — PostgreSQL schema design
- `n8n-provision` — n8n workflow provisioning

### Environment Variables

All managed via Infisical. Run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull secrets.

See `templates/.env.example` for the full list of required variables. Notable additions:

- `NOCOBASE_URL` / `NOCOBASE_API_KEY` — production NocoBase (live data)
- `NOCOBASE_DEV_URL` / `NOCOBASE_DEV_API_KEY` — dev-sandbox NocoBase for building and testing tables, UX elements, menus, pages, and workflows; also the auth pair behind the `nocobase-dev` MCP server and usable for API calls from dev/test apps

## Installation

Add to your `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "stack-composable-stack-v1@agents-store-claude-plugins-private": true
  }
}
```

Then run `/install-plugins` to install.
