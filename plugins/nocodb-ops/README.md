# nocodb-ops

NocoDB operations plugin for business users. Manage records, build reports, search data, and handle imports/exports via MCP tools and CLI.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify NocoDB connection and MCP access |
| **mcp-patterns** | All 11 MCP tools with parameters and usage patterns |
| **record-management** | Create, read, update, delete records — single and bulk |
| **views-and-reports** | View types, aggregation reports, dashboards |
| **search-filter** | Complete filter syntax reference with all operators |
| **import-export** | Bulk data import/export workflows |
| **cli-reference** | Official NocoDB CLI command reference (from nocodb/agent-skills) |
| **troubleshoot** | Diagnose connection, auth, and data errors |
| **examples** | CRM and inventory scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/nocodb-ops:list-tables` | List all tables in the base |
| `/nocodb-ops:list-records` | Query records with optional filter |
| `/nocodb-ops:create-record` | Create a new record |
| `/nocodb-ops:search-records` | Search records by keyword |
| `/nocodb-ops:create-view` | Guide for creating views |
| `/nocodb-ops:build-report` | Build aggregation reports |

## Agent

**data-assistant** — Business-language NocoDB operations assistant for finding data, building reports, managing records, and importing/exporting data.

## Installation

Enable the plugin in Claude Code. Set these environment variables:

```bash
export NOCODB_URL="https://your-nocodb-instance.com/mcp/your-path-id"
export NOCODB_TOKEN="your-xc-mcp-token"
export NOCODB_VERBOSE=1  # optional — show resolved IDs
```

The `.mcp.json` uses `${NOCODB_URL}` and `${NOCODB_TOKEN}` to configure the `nocodb` HTTP MCP server with `xc-mcp-token` header authentication.

## Prerequisites

- NocoDB instance with MCP endpoint enabled
- Valid `xc-mcp-token` for authentication
- For CLI: `curl` + `jq` (Linux/macOS) or PowerShell 5.1+ (Windows)

## CLI Setup (Optional)

Install the official NocoDB CLI for additional capabilities:

```bash
npx skills add nocodb/agent-skills
```

The CLI uses the same environment variables (`NOCODB_URL`, `NOCODB_TOKEN`, `NOCODB_VERBOSE`).

## Related Plugins

- **nocodb** (dev) — Schema design, table management, column configuration for developers
- **agents-workspace** — NocoDB integrated with n8n and Trigger.dev for workspace automation
