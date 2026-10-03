---
description: Set up a Link between two NocoDB tables, optionally with a Lookup
argument-hint: [from-table] [to-table] [cardinality]
allowed-tools: [Read, Write, Bash, Skill]
---

# Add Relation

Connect two NocoDB tables with a Link field. Optionally add a Lookup so the linked record's display name is visible on the other side.

## Steps

1. Resolve both table IDs via `mcp__plugin_nocodb-dev_nocodb__getTablesList`.
2. Decide the cardinality (`relation_type`):
   - **bt** (belongs-to) — many-to-one. Each row on the "from" side links to one row on the "to" side. (Order belongs to Customer.)
   - **hm** (has-many) — one-to-many. Each row on the "from" side links to many rows on the "to" side. (Customer has-many Orders.)
   - **mm** (many-to-many) — both sides link to many. (Tags ↔ Articles.)
   - **oo** (one-to-one) — each row links to exactly one row on the other side.
3. Snapshot both tables before:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <fromTableId>
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <toTableId>
   ```
4. Create the link field on the "from" table. On Cloud / licensed, `listTools category: "fields"` then `callTool name: "createField"` with `arguments: { tableId: "<fromTableId>", field: { … } }`; on Community Edition (or as a fallback) use REST with the same object as the body:
   ```bash
   curl -sS -X POST \
     -H "xc-token: ${NOCODB_TOKEN}" -H "Content-Type: application/json" \
     -d '{
       "title": "<linkName>",
       "type":  "LinkToAnotherRecord",
       "options": { "relation_type": "<bt|hm|mm|oo>", "related_table_id": "<toTableId>" }
     }' \
     "${NOCODB_URL}/api/v3/meta/bases/${BASE_ID}/tables/<fromTableId>/fields"
   ```
5. Verify the inverse link auto-appeared on the "to" table:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <toTableId>
   ```
6. (Optional) Ask the user if they want a Lookup that surfaces a field from the linked side. If yes:
   - Find the link's field ID on the "from" side (from step 5's snapshot).
   - Find the field ID to look up on the "to" side.
   - Create it with the same `createField` call (or REST `POST`) using:
     ```json
     {
       "title": "<lookupTitle>",
       "type":  "Lookup",
       "options": {
         "related_field_id": "<fromLinkFieldId>",
         "related_table_lookup_field_id": "<toFieldId>"
       }
     }
     ```
7. Verify both fields appear in the schema, and (optionally) link one record to confirm.

## Reference

- `Skill nocodb-dev:field-management` — workflow + payloads
- `Skill nocodb-dev:mcp-patterns` — the MCP-first contract (Cloud / licensed) and the REST fallback
- `Skill nocodb-dev:cli-reference` — `curl` recipes for relations (`references/relations-links.md`)
- `Skill nocodb-dev:examples` — CRM and e-commerce relation walkthroughs (`references/scenarios/`)

## Watch Out

- For `mm`, NocoDB creates a hidden join table. If you need per-relation metadata (quantity, line price), use an explicit join table (see `examples/references/scenarios/ecommerce-relations.md`).
- `options` needs both `relation_type` and `related_table_id`; flat keys outside `options` are rejected.
- Don't try to PATCH a Lookup config to point at a not-yet-existing link — NocoDB rejects with 400.
