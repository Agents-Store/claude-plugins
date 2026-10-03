# nocodb-ops

NocoDB operations plugin for business users. Manage records, build reports, search data, and handle imports/exports through the NocoDB MCP server -- with `curl` recipes on the v3 API for scripts.

> **Coming from the deprecated `nocodb` plugin?** Records, filters, reports and imports work here the same way over MCP. Schema and fields (tables, field types, views, hooks) are handled by **`nocodb-dev`**.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify NocoDB connection and MCP access; detect Community vs Cloud/licensed |
| **mcp-patterns** | The MCP contract, every record/read/analytics tool with parameters, 100-record batches, `sort` objects, `filter` vs `where` |
| **record-management** | Create, read, update, delete records -- single and bulk; what a delete can undo |
| **views-and-reports** | View types, aggregation reports, per-value counts, dashboards |
| **search-filter** | Complete filter syntax reference -- structured `filter`, `where`, operators, date sub-operators |
| **import-export** | Bulk data import/export workflows (batches, `importCsv`, `upsertRecords`, `exportCsv`) |
| **cli-reference** | curl recipes on the v3 API mapped to the official `nocodb.sh` script (from nocodb/agent-skills) |
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

**data-assistant** -- Business-language NocoDB operations assistant for finding data, building reports, managing records, and importing/exporting data.

## MCP Contract: Community vs Cloud / Licensed

| Edition | What the MCP server offers |
|---------|----------------------------|
| **Community Edition** | The eleven record tools only: `getBaseInfo`, `getTablesList`, `getTableSchema`, `queryRecords`, `getRecord`, `countRecords`, `aggregate`, `createRecords`, `updateRecords`, `deleteRecords`, `readAttachment` |
| **Cloud / licensed self-hosted** | Those plus many more (about 200 in 2026.09): `whoami`, `groupByRecords`, `linkRecords`, `exportCsv` are listed directly; `upsertRecords`, `updateRecordsByCondition`, `importCsv`, `exportExcel` and the trash tools are reached with `listTools(category)` then `callTool(name, arguments)` |

Limits worth knowing before you write: record-array tools take **at most 100 records per call** (a longer array is rejected outright), `queryRecords` pages default to 50 and cap at 200, `sort` is an array of `{field, direction}` objects, and date filters need a sub-operator (`exactDate`) -- ranges are two bounds, never `btw`. The **mcp-patterns** skill has the details.

## Installation

Enable the plugin in Claude Code. Set these environment variables:

```bash
# MCP -- used by .mcp.json
export NOCODB_MCP_URL="https://your-nocodb-instance.com/mcp"      # Community Edition: .../mcp/<your-endpoint-id>
export NOCODB_MCP_TOKEN="your-mcp-token"

# REST / curl recipes -- optional
export NOCODB_URL="https://your-nocodb-instance.com"
export NOCODB_TOKEN="your-api-token"

export NOCODB_VERBOSE=1  # optional -- show resolved IDs in the official nocodb.sh script
```

The `.mcp.json` uses `${NOCODB_MCP_URL}` and `${NOCODB_MCP_TOKEN}` to configure the `nocodb` HTTP MCP server with `xc-mcp-token` header authentication (still accepted; NocoDB's newer primary header is `x-api-key`). On Cloud you can also connect over OAuth at `https://app.nocodb.com/mcp` without a token. `NOCODB_URL` and `NOCODB_TOKEN` are used by direct REST (`curl`) calls and the optional official script -- the MCP token is separate. The REST token variable is `NOCODB_TOKEN`; the former variable name is covered as a legacy alias in the **setup** skill.

## Prerequisites

- A NocoDB instance with MCP enabled
- An MCP token -- Cloud / licensed: Account Settings → **MCP** tab → New connection; Community Edition: Overview → Settings → Model Context Protocol → New MCP Endpoint
- For REST recipes: an API token (NocoDB → Team & Settings → API Tokens), `curl` and `jq` (Linux/macOS) or PowerShell 5.1+ (Windows)

## curl and the Official Script (Optional)

NocoDB has **no `nc` binary** (on Linux and macOS `nc` is netcat). The **cli-reference** skill gives `curl` recipes on the v3 API. To use NocoDB's own command-line script as well:

```bash
npx skills add nocodb/agent-skills
```

The script (`nocodb.sh`) reads `NOCODB_TOKEN`, `NOCODB_URL` and `NOCODB_VERBOSE`. MCP-only variables (`NOCODB_MCP_URL`, `NOCODB_MCP_TOKEN`) are not needed for REST calls.

## Related Plugins

- **nocodb-dev** -- Schema design, table, field and view management, webhooks for developers
