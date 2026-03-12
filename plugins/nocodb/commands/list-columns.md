---
description: List columns in a NocoDB table
allowed-tools: ["mcp__nocodb__list_columns", "mcp__nocodb__list_tables"]
argument-hint: <table>
---

# List Columns

List all columns (fields) in a NocoDB table.

## Arguments
Format: `<table>`
- table: Table name or ID (required)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```

2. **List columns:**
   ```
   list_columns(table_id)
   ```

3. **Display results:**
   Show column ID, name, type, and key config (options for select, formula for formula fields, etc.).

## Example Usage
```
/list-columns "Contacts"
/list-columns "Orders"
```
