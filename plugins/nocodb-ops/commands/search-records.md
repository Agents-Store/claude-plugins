---
description: Search records in a NocoDB table by keyword
allowed-tools: ["mcp__nocodb-1__queryRecords", "mcp__nocodb-1__getTablesList", "mcp__nocodb-1__getTableSchema"]
argument-hint: <table-name> <query>
---

# Search Records

Search for records containing a keyword across text fields.

## Arguments

Parse from "$ARGUMENTS":
- `table-name` (required): Name or ID of the table
- `query` (required): Search text to find

## Process

1. Run `getTablesList` to resolve the table name to an ID.
2. Run `getTableSchema` to identify text fields (SingleLineText, LongText, Email, URL, PhoneNumber).
3. Build a `where` filter using `like` operator across text fields combined with `~or`.
4. Run `queryRecords` with the constructed filter.
5. Display matching records in a formatted table.

## Example Usage

```
/search-records Contacts "john doe"
/search-records Orders "pending"
/search-records Products "widget"
```
