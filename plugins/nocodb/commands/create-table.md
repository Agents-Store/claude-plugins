---
description: Create a new table in NocoDB
allowed-tools: ["mcp__nocodb__create_table", "mcp__nocodb__list_tables"]
argument-hint: <table-name> [--columns <col1:type,col2:type>]
---

# Create Table

Create a new table in NocoDB.

## Arguments
Format: `<table-name> [--columns <col1:type,col2:type>]`
- table-name: Name of the table to create (required)
- --columns: Comma-separated column definitions as name:type pairs (optional)

Parse from "$ARGUMENTS".

## Process

1. **Check existing tables:**
   ```
   list_tables()
   ```
   If table with same name exists, warn user and stop.

2. **Create the table:**
   ```
   create_table({
     name: <table-name>,
     columns: <parsed columns or default [Title:SingleLineText]>
   })
   ```

3. **Display created table details:**
   Show table ID, name, and columns.

## Example Usage
```
/create-table "Contacts"
/create-table "Orders" --columns "Title:SingleLineText,Amount:Number,Status:SingleSelect,Email:Email"
/create-table "Products" --columns "Name:SingleLineText,Price:Currency,InStock:Checkbox"
```
