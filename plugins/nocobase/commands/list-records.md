---
description: List records from a NocoBase collection
allowed-tools: ["mcp__nocobase__data_list", "mcp__nocobase__collection_get"]
argument-hint: <collection> [--limit <n>] [--filter <field=value>]
---

# List Records

List records from a NocoBase collection with optional filtering.

## Arguments
Format: `<collection> [--limit <n>] [--filter <field=value>]`
- collection: Target collection name (required)
- --limit: Maximum records to return (optional, default: 20)
- --filter: Filter by field value (optional)

Parse from "$ARGUMENTS".

## Process

1. **Get collection info:**
   Use `collection_get` to understand available fields.

2. **List records:**
   Use `data_list` with the collection name, limit, and filter parameters.

3. **Present results:**
   Display records in a formatted table with key fields.

## Example Usage
```
/list-records contacts
/list-records orders --limit 50 --filter status=Draft
/list-records products --filter category=Electronics
```
