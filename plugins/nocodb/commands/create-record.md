---
description: Create a new record in a NocoDB table
allowed-tools: ["mcp__nocodb__create_record", "mcp__nocodb__list_tables", "mcp__nocodb__list_columns"]
argument-hint: <table> [--data <field1=value1,field2=value2>]
---

# Create Record

Create a new record in a NocoDB table.

## Arguments
Format: `<table> [--data <field1=value1,field2=value2>]`
- table: Table name or ID (required)
- --data: Comma-separated field=value pairs (optional, will prompt if missing)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```
   Find table by name or ID. If not found, show available tables.

2. **Get columns if no data provided:**
   ```
   list_columns(table_id)
   ```
   Show column names and types to help user provide data.

3. **Create record:**
   ```
   create_record({
     table_id: <resolved_table_id>,
     data: { <field>: <value>, ... }
   })
   ```

4. **Display created record:**
   Show record ID and field values.

## Example Usage
```
/create-record "Contacts" --data "Name=John Doe,Email=john@example.com,Status=Active"
/create-record "Orders" --data "Title=Order 001,Amount=1500,Status=New"
```
