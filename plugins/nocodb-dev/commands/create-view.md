---
description: Create a Grid / Form / Gallery / Kanban / Calendar / Map view
argument-hint: [table-name-or-id] [view-type] [view-title]
allowed-tools: [Read, Write, Bash, Skill]
---

# Create NocoDB View

Create a new view on an existing table. Each view type has different prerequisites — see the **view-management** skill.

## Steps

1. Resolve the target table ID.
2. Snapshot existing views and the field list:
   ```
   mcp__nocodb__getTableSchema  tableId: <tableId>
   ```
3. Confirm the view title isn't already used on this table.
4. Pick the view type and validate prerequisites:
   - **Grid / Form** — no prerequisites
   - **Gallery** — needs an Attachment field for the cover image (recommended)
   - **Kanban** — needs a SingleSelect field; capture its column ID for `fk_grp_col_id`
   - **Calendar** — needs a Date or DateTime field; capture for `calendar_range[].fk_from_column_id`
   - **Map** — needs a Geometry field; capture for `fk_geo_data_col_id`
5. Run `nc view:create:<type> <baseId> <tableId> '<JSON>'` per **cli-reference**.
6. Verify with `mcp__nocodb__getTableSchema` — the new view appears in `views`.

## Reference

- `Skill nocodb-dev:view-management` — full workflow + payload shape per type
- `Skill nocodb-dev:cli-reference` — `nc view:create:*` syntax

## Notes

- View create / update / delete requires NocoDB Enterprise (self-hosted or cloud).
- After creating a view, you can add filters and sorts via `nc filter:create <viewId> '...'` and `nc sort:create <viewId> '...'`.
