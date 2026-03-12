---
description: List records from a NocoDB table with optional filters
allowed-tools: ["mcp__nocodb__list_records", "mcp__nocodb__list_tables"]
argument-hint: <table> [--where <filter>] [--sort <field>] [--limit <n>]
---

# List Records

List records from a NocoDB table with optional filtering, sorting, and pagination.

## Arguments
Format: `<table> [--where <filter>] [--sort <field>] [--limit <n>]`
- table: Table name or ID (required)
- --where: Filter in NocoDB format `(field,op,value)` (optional)
- --sort: Sort field, prefix with `-` for DESC (optional)
- --limit: Max records to return, default 25 (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve table:**
   ```
   list_tables()
   ```
   Find table by name or ID.

2. **List records:**
   ```
   list_records({
     table_id: <resolved_table_id>,
     where: <filter or empty>,
     sort: <sort or empty>,
     limit: <limit or 25>,
     offset: 0
   })
   ```

3. **Display results:**
   Show records in a table format with key fields. Include total count and pagination info.

## Filter Format
- Single: `(Status,eq,Active)`
- Combined: `(Status,eq,Active)~and(Amount,gt,1000)`
- Operators: eq, neq, gt, lt, gte, lte, like, is, isnot

## Example Usage
```
/list-records "Contacts"
/list-records "Orders" --where "(Status,eq,New)" --sort "-CreatedAt" --limit 10
/list-records "Products" --where "(Price,gt,100)~and(InStock,eq,true)"
```
