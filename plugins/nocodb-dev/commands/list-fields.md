---
description: List all fields on a NocoDB table with their types
argument-hint: [table-name-or-id]
allowed-tools: [Read, Bash, Skill]
---

# List Fields

Print every field on a table — title, type, options summary.

## Steps

1. Resolve the target table ID — `nc table:list <baseId>` if name was passed.
2. Run:
   ```
   mcp__nocodb__getTableSchema  tableId: <tableId>
   ```
3. Format the response as a table:

| Title | Type | Options |
|-------|------|---------|
| ... | ... | ... |

   For SingleSelect / MultiSelect, show the option titles.
   For Lookup / Rollup, show the linked column.
   For Formula, show the expression.
4. Also list views (name + type) at the bottom.

## Alternative — pure CLI

```bash
nc field:list <baseId> <tableId>
```

Returns raw JSON — useful when the user wants column IDs for scripting.

## Reference

- `Skill nocodb-dev:cli-reference` — `nc field:list` syntax
- `Skill nocodb-dev:mcp-patterns` — `getTableSchema` parameters
