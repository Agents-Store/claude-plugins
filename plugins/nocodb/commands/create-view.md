---
description: Create a new view for a NocoDB table
allowed-tools: ["mcp__nocodb__create_view", "mcp__nocodb__list_tables", "mcp__nocodb__list_columns"]
argument-hint: <table> <view-name> <type> [--group-by <field>]
---

# Create View

Create a new view (Grid, Kanban, Gallery, Form, Calendar) for a NocoDB table.

## Arguments
Format: `<table> <view-name> <type> [--group-by <field>]`
- table: Table name or ID (required)
- view-name: Name for the new view (required)
- type: View type — Grid, Kanban, Gallery, Form, Calendar (required)
- --group-by: For Kanban — the SingleSelect field to group by (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```

2. **Get columns (for Kanban/Calendar config):**
   ```
   list_columns(table_id)
   ```
   For Kanban, find the SingleSelect field. For Calendar, find the Date field.

3. **Create view:**
   ```
   create_view({
     table_id: <resolved_table_id>,
     title: <view-name>,
     type: <type>
   })
   ```

4. **Display result:**
   Show view ID, name, and type.

## Example Usage
```
/create-view "Contacts" "All Contacts" Grid
/create-view "Deals" "Pipeline" Kanban --group-by "Stage"
/create-view "Products" "Catalog" Gallery
/create-view "Leads" "Lead Form" Form
```
