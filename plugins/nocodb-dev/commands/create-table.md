---
description: Create a new NocoDB table with optional initial fields
argument-hint: [base-name-or-id] [table-title]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB Table

Create a new table in a NocoDB base. Prompt for any missing details (base, title, initial fields).

## Steps

1. Resolve the base ID from the user's input. The MCP server is pinned to one base — `mcp__plugin_nocodb-dev_nocodb__getBaseInfo` shows it. For another base, list workspaces and bases with `GET ${NOCODB_URL}/api/v3/meta/workspaces` and `…/workspaces/{workspaceId}/bases`, or prompt.
2. Confirm the table title isn't already in use:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTablesList
   ```
3. Ask the user for any initial fields they want included, or proceed with just a title and let them add fields later.
4. Create the table with the gathered payload (see the **table-management** skill for the payload shape and **field-management** for per-type field options). On Cloud / licensed: `listTools category: "tables"`, then `callTool name: "createTable"` with `arguments: { title, description?, fields? }`. On Community Edition (or as a fallback):
   ```bash
   curl -sS -X POST \
     -H "xc-token: ${NOCODB_TOKEN}" -H "Content-Type: application/json" \
     -d '<JSON>' \
     "${NOCODB_URL}/api/v3/meta/bases/<baseId>/tables"
   ```
5. Verify with `mcp__plugin_nocodb-dev_nocodb__getTableSchema` and report the new `tableId`.

## Reference

Invoke the relevant skills:

- `Skill nocodb-dev:table-management` — workflow and payload shape
- `Skill nocodb-dev:field-management` — for any initial fields
- `Skill nocodb-dev:mcp-patterns` — MCP-first contract and REST fallback

## Confirmation

Before running the create, print the planned payload and ask the user to confirm.
