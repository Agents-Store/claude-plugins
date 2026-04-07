# stack-composable-stack-v1

Composable Stack v1 dev plugin for Agents Store. Integrates PostgreSQL, NocoDB, n8n, Trigger.dev, and NocoBase via MCP for building data-driven applications with low-code interfaces.

## Architecture

| Layer | Service | Purpose |
|-------|---------|---------|
| Data | PostgreSQL | Relational database (source of truth) |
| Data | NocoDB | Spreadsheet interface + MCP access |
| Logic | n8n | Workflow automation |
| Logic | Trigger.dev | Background tasks and AI agents |
| Interface | NocoBase | Low-code admin UI |
| Interface | NocoDB | Data views and shared forms |

## MCP Servers

| Server | Transport | Service |
|--------|-----------|---------|
| `trigger-dev` | stdio | Trigger.dev task management |
| `n8n-mcp-external` | stdio | n8n workflow CRUD and node search |
| `n8n-native-mcp` | HTTP | n8n native MCP operations |
| `nocodb` | HTTP | NocoDB table and record operations |

## Skills

| Skill | Description |
|-------|-------------|
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

See `templates/.env.example` for the full list of required variables.

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
