---
description: Create a Grid / Form / Gallery / Kanban / Calendar / Map / Gantt / Timeline / List view
argument-hint: [table-name-or-id] [view-type] [view-title]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB View

Create a new view on an existing table. Each view type has different prerequisites — see the **view-management** skill.

## Steps

1. Resolve the target table ID.
2. Snapshot existing views and the field list:
   ```
   mcp__plugin_nocodb-dev_nocodb__getTableSchema  tableId: <tableId>
   ```
3. Confirm the view title isn't already used on this table.
4. Pick the view type and validate prerequisites:
   - **Grid / Form** — no prerequisites
   - **Gallery** — needs an Attachment field for the cover image (recommended); capture its ID for `options.cover_field_id`
   - **Kanban** — needs a SingleSelect field; capture its ID for `options.stack_by.field_id`
   - **Calendar / Timeline** — needs a Date or DateTime field; capture for `options.date_ranges[].start_date_field_id` (and the end field)
   - **Gantt** — needs start/end Date fields; `options.date_dependency` is required (`null` takes the table default)
   - **List** — needs linked tables; describe them in `options.levels`
   - **Map** — needs a Geometry field; capture for `options.geo_data_field_id`
5. Create the view. On Cloud / licensed: `listTools category: "views"`, then `callTool name: "createView"` with `arguments: { tableId, title, type, lock_type?, options?, fields? }`. On Community Edition (or as a fallback) — payloads per **view-management**:
   ```bash
   curl -sS -X POST \
     -H "xc-token: ${NOCODB_TOKEN}" -H "Content-Type: application/json" \
     -d '{ "title": "<viewTitle>", "type": "<type>", "options": { … } }' \
     "${NOCODB_URL}/api/v3/meta/bases/${BASE_ID}/tables/<tableId>/views"
   ```
6. Verify with `mcp__plugin_nocodb-dev_nocodb__getTableSchema` — the new view appears in `views`.

## Reference

- `Skill nocodb-dev:view-management` — full workflow + payload shape per type
- `Skill nocodb-dev:cli-reference` — `curl` recipes (`references/view-filter-sort.md`)

## Notes

- The view APIs need cloud Enterprise or a licensed self-hosted deployment (Business plan and above).
- After creating a view, add filters and sorts: MCP `createFilter` / `addSort`, or REST `POST …/views/{viewId}/filters` with `{ "field_id", "operator", "value" }` and `POST …/views/{viewId}/sorts` with `{ "field_id", "direction" }`.
