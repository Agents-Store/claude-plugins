---
description: Search records in a NocoDB table
allowed-tools: ["mcp__nocodb__search_records", "mcp__nocodb__list_tables"]
argument-hint: <table-name> <query>
---

# Search Records

Search for records across all fields in a NocoDB table.

## Arguments
Format: `<table-name> <query>`
- table-name: Name or ID of the table (required)
- query: Search query text (required)

Parse from "$ARGUMENTS".

## Process

1. **Find table:**
   Use `list_tables` to resolve table name to ID.

2. **Search:**
   Use `search_records` with the query.

3. **Present results:**
   Display matching records in a formatted table.

## Example Usage
```
/search-records contacts "john doe"
/search-records orders "pending"
```
