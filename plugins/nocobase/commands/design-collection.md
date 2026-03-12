---
description: Design a NocoBase collection schema
allowed-tools: ["mcp__nocobase__collection_list", "mcp__nocobase__collection_get"]
argument-hint: <collection-name> [--fields <field1:type,field2:type>]
---

# Design Collection

Design a NocoBase collection (data model) schema with fields and relations.

## Arguments
Format: `<collection-name> [--fields <field1:type,field2:type>]`
- collection-name: Name of the collection (required)
- --fields: Comma-separated field definitions as name:type pairs (optional)

Parse from "$ARGUMENTS".

## Process

1. **Analyze requirements:**
   - What entity does this collection represent?
   - What fields are needed?
   - What relations to other collections?

2. **Generate schema:**
   Define collection with all fields, types, validations, and relation configuration.

3. **Provide implementation guidance:**
   Show the JSON configuration or UI steps to create the collection in NocoBase.

## Example Usage
```
/design-collection "contacts" --fields "name:string,email:email,phone:phone,status:select"
/design-collection "orders"
/design-collection "products" --fields "title:string,price:decimal,category:belongsTo"
```

## Notes
This is a knowledge-only command. If NocoBase MCP tools are available in your session, they will be used to create the collection directly.
