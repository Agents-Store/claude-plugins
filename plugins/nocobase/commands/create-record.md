---
description: Create a record in a NocoBase collection
allowed-tools: ["mcp__nocobase__data_create", "mcp__nocobase__collection_get"]
argument-hint: <collection> <field1=value1> [field2=value2] ...
---

# Create Record

Create a new record in a NocoBase collection.

## Arguments
Format: `<collection> <field1=value1> [field2=value2] ...`
- collection: Target collection name (required)
- field=value: Field name and value pairs (at least one required)

Parse from "$ARGUMENTS".

## Process

1. **Verify collection:**
   Use `collection_get` to check the collection exists and get available fields.

2. **Create record:**
   Use `data_create` with the collection name and field values.

3. **Confirm result:**
   Show the created record with its ID.

## Example Usage
```
/create-record contacts name="John Doe" email="john@example.com" status="Active"
/create-record orders total=1500 status="Draft"
```
