# directus-dev

Directus development plugin for Claude Code. Knowledge base for working with Directus MCP tools (12 tools), REST API, and @directus/sdk. Covers collections, items, fields, relations, files, flows, operations, and schema design.

## Features

- **11 skills** covering MCP tools, item operations, schema design, field/relations, flow automation, file management, REST API, SDK patterns, local Docker Compose development, troubleshooting, and examples
- **2 agents** — general assistant and schema architect
- **10 commands** for quick operations

## Prerequisites

- Directus v11.12+ (tested up to v12.4.1) with MCP enabled (Settings > AI > Model Context Protocol)
- OAuth sign-in (recommended) or a Directus access token for a dedicated user whose policies grant only what the work needs

### Directus 12 notes

- **Licensing is enforced.** Self-hosted instances run on the Core tier. SSO, custom permission rules and custom or self-hosted LLMs need a licensed tier, and an instance that stays over its limits after the 30 day grace period loses GraphQL, WebSockets and **MCP** until the license is resolved.
- **Permissions live in policies** (since Directus 11). Roles organize users, policies hold the access flags and the permissions. The plugin teaches the policy model, not the role-permission model.
- **`/server/health` needs a token**; use `/server/ping` for liveness probes.
- A collection with status **Inactive** answers `403 COLLECTION_INACTIVE` on REST, GraphQL, WebSockets and MCP (12.4.0+). Use 12.4.1 or later: 12.4.0 breaks reading `directus_folders` as a non-admin.
- `IP_TRUST_PROXY` now defaults to `false`; set it when Directus runs behind a reverse proxy.
- The JavaScript SDK moves with Directus: `@directus/sdk` 26 targets Directus 12.4 and needs Node 22 or later.

## Installation

### As Claude Code Plugin (user scope)

```bash
claude plugin install directus-dev@agents-store
```

This plugin provides **knowledge only** — it teaches Claude how to use Directus MCP tools, API, and SDK. It does NOT connect to any Directus instance.

### Connecting to Directus (project scope)

MCP connection is configured per-project, NOT in this plugin. Set it up in your project:

```bash
# Recommended: OAuth, sign in in the browser (server needs MCP_OAUTH_ENABLED and a
# client registration method, see the mcp-tools skill)
claude mcp add --transport http directus https://your-directus-instance.com/mcp

# Fallback: static token of a dedicated user
claude mcp add --transport http directus \
  https://your-directus-instance.com/mcp \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Claude Code searches MCP tools on demand, so use the default `/mcp` URL. A client that loads every tool definition up front, or has a tool-count limit, can use registry mode, which exposes only `search`, `execute` and `schema`:

```bash
claude mcp add --transport http directus_registry \
  "https://your-directus-instance.com/mcp?tool_mode=registry"
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
| schema-design | Data modeling, creation order, system fields, content versioning, archive pattern |
| field-relations | Field types, M2O/O2M/M2M/M2A relation workflows |
| flow-automation | Flows, operations, triggers, data chains, flow folders, calling an external app (cache revalidation) |
| file-management | Files, assets, folders, imports |
| api-reference | REST API endpoints and curl examples, policies and access endpoints |
| sdk-patterns | @directus/sdk 26 composable client, login, server-side use in Next.js (fetch options, per-request tokens, relations), content versions, policies |
| docker-local-dev | Run Directus 12 locally with Docker Compose (PostgreSQL, Redis, loopback port, health checks, Live Preview) |
| troubleshoot | Common errors, diagnostics, MCP issues, Directus 12 notes |
| examples | End-to-end scenarios and tool call patterns |

## Agents

| Agent | Purpose |
|-------|---------|
| directus-assistant | Interactive assistant for all Directus operations |
| directus-schema-architect | Specialized schema design and data modeling |

## Commands

`/explore-schema`, `/list-collections`, `/list-items`, `/create-item`, `/search-items`, `/create-collection`, `/list-flows`, `/list-files`, `/snapshot-schema`, `/trigger-flow`
