---
description: Add a column to a NocoDB table
allowed-tools: ["mcp__nocodb__create_column", "mcp__nocodb__list_tables", "mcp__nocodb__list_columns"]
argument-hint: <table> <column-name> <type> [--options <opt1,opt2>]
---

# Create Column

Add a new column (field) to a NocoDB table.

## Arguments
Format: `<table> <column-name> <type> [--options <opt1,opt2>]`
- table: Table name or ID (required)
- column-name: Name for the new column (required)
- type: Column type — SingleLineText, Number, SingleSelect, Email, URL, Date, Checkbox, Currency, LinkToAnotherRecord, Lookup, Rollup, Formula (required)
- --options: For SingleSelect/MultiSelect — comma-separated options (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```

2. **Check existing columns:**
   ```
   list_columns(table_id)
   ```
   Warn if column with same name exists.

3. **Create column:**
   ```
   create_column({
     table_id: <resolved_table_id>,
     name: <column-name>,
     type: <type>,
     options: <options if SingleSelect/MultiSelect>
   })
   ```

4. **Display result:**
   Show column ID, name, and type.

## Example Usage
```
/create-column "Contacts" "Phone" PhoneNumber
/create-column "Orders" "Priority" SingleSelect --options "Low,Medium,High,Critical"
/create-column "Products" "Price" Currency
```
