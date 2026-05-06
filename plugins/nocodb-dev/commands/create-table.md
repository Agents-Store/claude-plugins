---
description: Create a new NocoDB table with optional initial fields
argument-hint: [base-name-or-id] [table-title]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB Table

Create a new table in a NocoDB base. Prompt for any missing details (base, title, initial fields).

## Steps

1. Resolve the base ID from the user's input. If the base name was passed, run `nc base:list` to find the matching ID. Otherwise prompt.
2. Confirm the table title isn't already in use:
   ```
   mcp__nocodb__getTablesList
   ```
3. Ask the user for any initial fields they want included, or proceed with just a title and let them add fields later.
4. Run `nc table:create <baseId> '<JSON>'` with the gathered payload — see the **table-management** skill for the payload shape and **field-management** skill for per-type field options.
5. Verify with `mcp__nocodb__getTableSchema` and report the new `tableId`.

## Reference

Invoke the relevant skills:

- `Skill nocodb-dev:table-management` — workflow and payload shape
- `Skill nocodb-dev:field-management` — for any initial fields
- `Skill nocodb-dev:cli-reference` — exact `nc` syntax

## Confirmation

Before running the create, print the planned payload and ask the user to confirm.
