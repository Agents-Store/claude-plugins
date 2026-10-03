---
description: Create a new view for a NocoDB table
allowed-tools: ["mcp__plugin_nocodb-ops_nocodb__getTablesList", "mcp__plugin_nocodb-ops_nocodb__getTableSchema", "mcp__plugin_nocodb-ops_nocodb__queryRecords"]
argument-hint: <table-name> <view-type> [title]
---

# Create View

Describe how to create a new view for a NocoDB table. This plugin's MCP tools are data tools and do not create views, so guide the user through the NocoDB web interface -- or hand the schema work to the **nocodb-dev** plugin (`/nocodb-dev:create-view`), which builds views over MCP on Cloud / licensed servers and over REST otherwise.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `view-type` (required): grid, kanban, gallery, form, calendar, timeline, gantt, map, or list
- `title` (optional): Name for the new view

## Process

1. Run `getTablesList` to resolve the table name.
2. Run `getTableSchema` to list existing views and columns.
3. Based on view type, recommend:
   - **Grid**: default working view, suggest useful filters and sorts
   - **Kanban**: identify SingleSelect columns suitable for grouping
   - **Gallery**: identify Attachment columns for cover images
   - **Form**: suggest which fields to include as required
   - **Calendar / Timeline**: identify Date/DateTime columns (a start and, optionally, an end)
   - **Gantt**: identify start and end Date columns
   - **Map**: identify a geographic (Geometry) column
   - **List**: identify the linked tables to nest
4. Provide step-by-step instructions for creating the view in the NocoDB UI.
5. If the user wants it scripted, point to `/nocodb-dev:create-view` (MCP `createView`, or the `POST /api/v3/meta/bases/{baseId}/tables/{tableId}/views` curl recipe) -- there is no `nc` command.

## Example Usage

```
/create-view Deals kanban "Deal Pipeline"
/create-view Contacts form "New Contact Form"
/create-view Events calendar "Event Schedule"
```
