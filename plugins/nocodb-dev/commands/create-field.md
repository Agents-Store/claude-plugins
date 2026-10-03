---
description: Add a field of any of the 35 supported types to a NocoDB table
argument-hint: [table-name-or-id] [field-title] [field-type]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB Field

Add a field to an existing table. Choose any of the 35 supported types — see the **field-management** skill and `api-reference/references/field-types.md` for per-type payloads. Type-specific settings go inside `options`.

## Steps

1. Resolve the target table ID — `mcp__plugin_nocodb-dev_nocodb__getTablesList` if a name was passed, or prompt.
2. Snapshot existing fields:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <tableId>
   ```
3. Confirm the new field title isn't already taken.
4. Determine the field type. Common pairings:
   - "phone" → `PhoneNumber`
   - "money / price / amount" → `Currency`
   - "status / stage" → `SingleSelect` (gather choices)
   - "tags / categories (many)" → `MultiSelect` (gather choices)
   - "image / file / attachment" → `Attachment`
   - "linked record" → `LinkToAnotherRecord` (ask cardinality: bt / hm / mm / oo)
   - "computed value" → `Formula` (gather expression)
   - "auto-incrementing id" → `AutoNumber`
5. Build the payload (per `field-types.md`): `{ "title": …, "type": …, "options": { … } }`.
6. Create it. On Cloud / licensed: `listTools category: "fields"`, then `callTool name: "createField"` with `arguments: { tableId: "<tableId>", field: <payload> }`. On Community Edition (or as a fallback):
   ```bash
   curl -sS -X POST \
     -H "xc-token: ${NOCODB_TOKEN}" -H "Content-Type: application/json" \
     -d '<JSON>' \
     "${NOCODB_URL}/api/v3/meta/bases/${BASE_ID}/tables/<tableId>/fields"
   ```
7. Verify with `mcp__plugin_nocodb-dev_nocodb__getTableSchema` and `mcp__plugin_nocodb-dev_nocodb__queryRecords` (small page, sanity-check render).

## Reference

- `Skill nocodb-dev:field-management` — workflow + cheatsheet
- `Skill nocodb-dev:api-reference` — full type catalog (references/field-types.md)
- `Skill nocodb-dev:mcp-patterns` — `createField` over MCP vs the REST body

## Special Cases

- **Lookup / Rollup**: the underlying link field must already exist. If it doesn't, run `/nocodb-dev:add-relation` first.
- **Formula**: after creating, query 3 records to spot-check that the formula renders without `ERR`.
- **System fields** (`CreatedTime`, `LastModifiedTime`, `CreatedBy`, `LastModifiedBy`): created instantly with `{"title":"X","type":"<TypeName>"}`; populate themselves.
- **Select choices later**: use the options endpoint / `addFieldOptions` instead of resending the whole list.
