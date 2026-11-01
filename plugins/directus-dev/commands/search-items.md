---
description: Search items across a Directus collection using full-text search
argument-hint: <collection> <query>
---

# Search Items

Follow the `item-operations` skill (`${CLAUDE_PLUGIN_ROOT}/skills/item-operations/SKILL.md`) for the query syntax, filters and batch rules; read it before the first call.

## Arguments

- `collection` (required) — Collection name
- `query` (required) — Search text

## Process

1. Parse collection name and search query
2. Call `schema` tool with `keys: ["<collection>"]` to determine best display fields
3. Call `items` tool with:
   ```json
   {
     "action": "read",
     "collection": "<collection>",
     "query": {
       "search": "<query>",
       "fields": ["id", "<main_field>", "<secondary_fields>"],
       "limit": 20
     }
   }
   ```
4. Display matching items as a table
5. Show count of results found

## Example

Input: `articles machine learning`

```json
{
  "action": "read",
  "collection": "articles",
  "query": {
    "search": "machine learning",
    "fields": ["id", "title", "status", "date_created"],
    "limit": 20
  }
}
```
