---
description: List records from a NocoDB table with optional filtering
allowed-tools: ["mcp__nocodb-1__queryRecords", "mcp__nocodb-1__getTablesList", "mcp__nocodb-1__getTableSchema"]
argument-hint: <table-name> [where-filter]
---

# List Records

Query records from a NocoDB table with optional filtering and sorting.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `where-filter` (optional): Filter in NocoDB syntax, e.g. `(Status,eq,Active)`

## Process

1. Run `getTablesList` to resolve the table name to an ID.
2. Run `getTableSchema` to discover field names and types.
3. Run `queryRecords` with the table ID and optional where filter.
4. Display results in a formatted table showing key fields.
5. Report total count and pagination info if more records exist.

## Example Usage

```
/list-records Contacts
/list-records Orders (Status,eq,Pending)
/list-records Deals (Amount,gt,5000)~and(Stage,eq,Negotiation)
```
