---
description: List all fields on a NocoDB table with their types
argument-hint: [table-name-or-id]
allowed-tools: [Read, Bash, Skill]
---

# List Fields

Print every field on a table — title, type, options summary.

## Steps

1. Resolve the target table ID — `mcp__plugin_nocodb-dev_nocodb__getTablesList` if a name was passed.
2. Run:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <tableId>
   ```
3. Format the response as a table:

| Title | Type | Options |
|-------|------|---------|
| ... | ... | ... |

   For SingleSelect / MultiSelect, show the choice titles.
   For Lookup / Rollup, show the related field (`options.related_field_id` and the looked-up / rolled-up field).
   For Formula, show the expression.
4. Also list views (name + type) at the bottom.

## Alternative — raw JSON

```bash
curl -sS -H "xc-token: ${NOCODB_TOKEN}" \
  "${NOCODB_URL}/api/v3/meta/bases/${BASE_ID}/tables/<tableId>" | jq '.fields'
```

Returns raw JSON — useful when the user wants field IDs for scripting. `mcp__plugin_nocodb-dev_nocodb__listFields` returns the same list over MCP.

## Reference

- `Skill nocodb-dev:cli-reference` — `curl` recipes for fields
- `Skill nocodb-dev:mcp-patterns` — `getTableSchema`, `getBaseSchema` and `listFields`
