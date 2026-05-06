---
description: Add a field of any of the 30 supported types to a NocoDB table
argument-hint: [table-name-or-id] [field-title] [field-type]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB Field

Add a field to an existing table. Choose any of the 30 supported types — see the **field-management** skill and `api-reference/references/field-types.md` for per-type payloads.

## Steps

1. Resolve the target table ID — `nc table:list <baseId>` if name was passed, or prompt.
2. Snapshot existing columns:
   ```
   mcp__nocodb__getTableSchema  tableId: <tableId>
   ```
3. Confirm the new field title isn't already taken.
4. Determine the field type. Common pairings:
   - "phone" → `PhoneNumber`
   - "money / price / amount" → `Currency`
   - "status / stage" → `SingleSelect` (gather options)
   - "tags / categories (many)" → `MultiSelect` (gather options)
   - "image / file / attachment" → `Attachment`
   - "linked record" → `Links` (ask cardinality: bt / hm / mm)
   - "computed value" → `Formula` (gather expression)
   - "auto-incrementing id" → `Number` with `cdf` default and unique constraint
5. Build the payload (per `field-types.md`).
6. Run `nc field:create <baseId> <tableId> '<JSON>'`.
7. Verify with `mcp__nocodb__getTableSchema` and `mcp__nocodb__queryRecords` (small page, sanity-check render).

## Reference

- `Skill nocodb-dev:field-management` — workflow + cheatsheet
- `Skill nocodb-dev:api-reference` — full type catalog (references/field-types.md)
- `Skill nocodb-dev:cli-reference` — `nc field:create` syntax

## Special Cases

- **Lookup / Rollup**: the underlying link field must already exist. If it doesn't, run `/nocodb-dev:add-relation` first.
- **Formula**: after creating, query 3 records to spot-check that the formula renders without `ERR`.
- **System fields** (`CreatedTime`, `LastModifiedTime`, `CreatedBy`, `LastModifiedBy`): created instantly with `{"title":"X","type":"<TypeName>"}`; populate themselves.
