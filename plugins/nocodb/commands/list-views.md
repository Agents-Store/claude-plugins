---
description: List views for a NocoDB table
allowed-tools: ["mcp__nocodb__list_views", "mcp__nocodb__list_tables"]
argument-hint: <table>
---

# List Views

List all views for a NocoDB table.

## Arguments
Format: `<table>`
- table: Table name or ID (required)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```

2. **List views:**
   ```
   list_views(table_id)
   ```

3. **Display results:**
   Show view ID, name, and type for each view.

## Example Usage
```
/list-views "Contacts"
/list-views "Orders"
```
