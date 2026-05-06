---
description: Set up a Link between two NocoDB tables, optionally with a Lookup
argument-hint: [from-table] [to-table] [cardinality]
allowed-tools: [Read, Write, Bash, Skill]
---

# Add Relation

Connect two NocoDB tables with a Link field. Optionally add a Lookup so the linked record's display name is visible on the other side.

## Steps

1. Resolve both table IDs via `mcp__nocodb__getTablesList` or `nc table:list`.
2. Decide the cardinality:
   - **bt** (belongs-to) — many-to-one. Each row on the "from" side links to one row on the "to" side. (Order belongs to Customer.)
   - **hm** (has-many) — one-to-many. Each row on the "from" side links to many rows on the "to" side. (Customer has-many Orders.)
   - **mm** (many-to-many) — both sides link to many. (Tags ↔ Articles.)
3. Snapshot both tables before:
   ```
   mcp__nocodb__getTableSchema  tableId: <fromTableId>
   mcp__nocodb__getTableSchema  tableId: <toTableId>
   ```
4. Create the link field on the "from" table:
   ```bash
   nc field:create <baseId> <fromTableId> '{
     "title": "<linkName>",
     "type":  "Links",
     "linked_table_id": "<toTableId>",
     "type_of_relation": "<bt|hm|mm>"
   }'
   ```
5. Verify the inverse link auto-appeared on the "to" table:
   ```
   mcp__nocodb__getTableSchema  tableId: <toTableId>
   ```
6. (Optional) Ask the user if they want a Lookup that surfaces a column from the linked side. If yes:
   - Find the link's column ID on the "from" side (from step 5's snapshot).
   - Find the column ID to look up on the "to" side.
   - Run:
     ```bash
     nc field:create <baseId> <fromTableId> '{
       "title": "<lookupTitle>",
       "type":  "Lookup",
       "fk_relation_column_id": "<fromLinkColumnId>",
       "fk_lookup_column_id":   "<toColumnId>"
     }'
     ```
7. Verify both fields appear in the schema, and (optionally) link one record to confirm.

## Reference

- `Skill nocodb-dev:field-management` — workflow + payloads
- `Skill nocodb-dev:cli-reference` — `nc field:create` syntax
- `Skill nocodb-dev:examples` — CRM and e-commerce relation walkthroughs (`references/scenarios/`)

## Watch Out

- For `mm`, NocoDB creates a hidden join table. If you need per-relation metadata (quantity, line price), use an explicit join table (see `examples/references/scenarios/ecommerce-relations.md`).
- Don't try to PATCH a Lookup config to point at a not-yet-existing link — NocoDB rejects with 400.
