---
description: Create a new record in a NocoDB table
allowed-tools: ["mcp__nocodb-1__createRecords", "mcp__nocodb-1__getTablesList", "mcp__nocodb-1__getTableSchema"]
argument-hint: <table-name> <field=value pairs>
---

# Create Record

Create a new record in a NocoDB table.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- Field values: key=value pairs or JSON object

## Process

1. Run `getTablesList` to resolve the table name to an ID.
2. Run `getTableSchema` to discover required fields and types.
3. Map the provided field values to the table schema.
4. Run `createRecords` with the mapped data.
5. Confirm creation and display the new record.

## Example Usage

```
/create-record Contacts Name="Jane Smith" Email="jane@example.com" Status=Active
/create-record Orders Product="Widget A" Quantity=10 Status=Pending
```
