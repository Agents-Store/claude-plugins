---
description: List all tables in the NocoDB base
allowed-tools: ["mcp__nocodb__getTablesList", "mcp__nocodb__getBaseInfo"]
argument-hint: ""
---

# List Tables

List all tables in the current NocoDB base.

## Process

1. Run `getTablesList` to fetch all accessible tables.
2. Display results in a table with ID, name, and description.
3. If no tables found, suggest checking the connection with the setup skill.
