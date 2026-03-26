# directus-dev

Directus development plugin for Claude Code. Knowledge base for working with Directus MCP tools (12 tools), REST API, and @directus/sdk. Covers collections, items, fields, relations, files, flows, operations, and schema design.

## Features

- **10 skills** covering MCP tools, item operations, schema design, field/relations, flow automation, file management, REST API, SDK patterns, troubleshooting, and examples
- **2 agents** — general assistant and schema architect
- **10 commands** for quick operations

## Prerequisites

- Directus v11.12+ with MCP enabled (Settings > AI > Model Context Protocol)
- A Directus access token for a user with appropriate permissions

## Installation

### As Claude Code Plugin (user scope)

```bash
claude plugin install directus-dev@agents-store
```

This plugin provides **knowledge only** — it teaches Claude how to use Directus MCP tools, API, and SDK. It does NOT connect to any Directus instance.

### Connecting to Directus (project scope)

MCP connection is configured per-project, NOT in this plugin. Set it up in your project:

```bash
claude mcp add --transport http directus \
  https://your-directus-instance.com/mcp \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

For multiple instances:
```bash
claude mcp add --transport http directus_products \
  https://products.example.com/mcp \
  --header "Authorization: Bearer TOKEN_1"

claude mcp add --transport http directus_content \
  https://content.example.com/mcp \
  --header "Authorization: Bearer TOKEN_2"
```

Or in the project's `.mcp.json` (for Stack Plugins with `${VAR}`):
```json
{
  "mcpServers": {
    "directus": {
      "type": "http",
      "url": "${DIRECTUS_URL}/mcp",
      "headers": {
        "Authorization": "Bearer ${DIRECTUS_TOKEN}"
      }
    }
  }
}
```

## Skills

| Skill | Description |
|-------|-------------|
| mcp-tools | All 12 MCP tools reference — action patterns, parameters, query system |
| item-operations | Items CRUD, filtering, deep queries, aggregation, batch operations |
| schema-design | Data modeling, creation order, system fields, versioning |
| field-relations | Field types, M2O/O2M/M2M/M2A relation workflows |
| flow-automation | Flows, operations, triggers, data chains |
| file-management | Files, assets, folders, imports |
| api-reference | REST API endpoints and curl examples |
| sdk-patterns | @directus/sdk composable client patterns |
| troubleshoot | Common errors, diagnostics, MCP issues |
| examples | End-to-end scenarios and tool call patterns |

## Agents

| Agent | Purpose |
|-------|---------|
| directus-assistant | Interactive assistant for all Directus operations |
| directus-schema-architect | Specialized schema design and data modeling |

## Commands

`/explore-schema`, `/list-collections`, `/list-items`, `/create-item`, `/search-items`, `/create-collection`, `/list-flows`, `/list-files`, `/snapshot-schema`, `/trigger-flow`
