---
description: List records from a NocoDB table with optional filtering
allowed-tools: ["mcp__plugin_nocodb-ops_nocodb__queryRecords", "mcp__plugin_nocodb-ops_nocodb__getTablesList", "mcp__plugin_nocodb-ops_nocodb__getTableSchema"]
argument-hint: <table-name> [where-filter]
---

# List Records

Query records from a NocoDB table with optional filtering and sorting.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `where-filter` (optional): Filter in NocoDB `where` syntax, e.g. `(Status,eq,Active)` (translate it to the structured `filter` when it has dates or special characters)

## Process

1. Run `getTablesList` to resolve the table name to an ID.
2. Run `getTableSchema` to discover field names and types.
3. Run `queryRecords` with the table ID and the optional filter. If the user names an order, pass `sort` as an **array of objects**: `[{ "field": "Created", "direction": "desc" }]` (not `"-Created"`). `pageSize` defaults to 50 and is capped at 200.
4. Date comparisons need a sub-operator -- `(Due,gte,exactDate,2026-06-01)`; ranges are two bounds, never `btw`.
5. Display results in a formatted table showing key fields.
6. Report total count (`countRecords` with the same filter) and pagination info if more records exist.

## Example Usage

```
/list-records Contacts
/list-records Orders (Status,eq,Pending)
/list-records Deals (Amount,gt,5000)~and(Stage,eq,Negotiation)
```
