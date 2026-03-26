---
description: Create a new Directus collection with optional fields
allowed-tools: ["mcp__directus__collections", "mcp__directus__fields", "mcp__directus__schema"]
argument-hint: <name> [--fields <field1:type,field2:type>] [--icon <icon>]
---

# Create Collection

## Arguments

- `name` (required) — Collection name (snake_case recommended)
- `--fields <field1:type,...>` — Comma-separated field definitions (e.g., `title:string,content:text,price:decimal`)
- `--icon <icon>` — Material icon name (default: `box`)

## Process

1. Parse arguments
2. Call `schema` tool (no params) to check collection doesn't already exist
3. Call `collections` tool to create the collection:
   ```json
   {
     "action": "create",
     "data": [{
       "collection": "<name>",
       "schema": {},
       "meta": {
         "icon": "<icon>",
         "display_template": "{{<first_string_field>}}"
       }
     }]
   }
   ```
4. If `--fields` provided, parse and create fields:
   ```json
   {
     "action": "create",
     "collection": "<name>",
     "data": [
       { "field": "<name>", "type": "<type>", "meta": { "interface": "<auto-mapped>" } }
     ]
   }
   ```
   Auto-map types to interfaces: string→input, text→input-rich-text-md, integer→input, decimal→input, boolean→boolean, datetime→datetime, json→input-code
5. Display the created collection and its fields
6. Suggest adding relations or more fields

## Example

Input: `products --fields name:string,description:text,price:decimal,active:boolean --icon inventory_2`
