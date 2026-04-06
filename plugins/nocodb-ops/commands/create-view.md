---
description: Create a new view for a NocoDB table
allowed-tools: ["mcp__nocodb-1__getTablesList", "mcp__nocodb-1__getTableSchema", "mcp__nocodb-1__queryRecords"]
argument-hint: <table-name> <view-type> [title]
---

# Create View

Describe how to create a new view for a NocoDB table. Since NocoDB MCP does not expose view management tools directly, guide the user through the NocoDB web interface or CLI.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `view-type` (required): grid, kanban, gallery, form, or calendar
- `title` (optional): Name for the new view

## Process

1. Run `getTablesList` to resolve the table name.
2. Run `getTableSchema` to list existing views and columns.
3. Based on view type, recommend:
   - **Grid**: default working view, suggest useful filters and sorts
   - **Kanban**: identify SingleSelect columns suitable for grouping
   - **Gallery**: identify Attachment columns for cover images
   - **Form**: suggest which fields to include as required
   - **Calendar**: identify Date/DateTime columns
4. Provide step-by-step instructions for creating the view in the NocoDB UI.
5. If CLI is available, show the `nc view:create` command.

## Example Usage

```
/create-view Deals kanban "Deal Pipeline"
/create-view Contacts form "New Contact Form"
/create-view Events calendar "Event Schedule"
```
