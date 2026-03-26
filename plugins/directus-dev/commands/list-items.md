---
description: List items from a Directus collection with optional filters
argument-hint: <collection> [--filter <field=value>] [--sort <field>] [--limit <n>]
---

# List Items

## Arguments

- `collection` (required) — Collection name
- `--filter <field=value>` — Filter by field value (e.g., `--filter status=published`)
- `--sort <field>` — Sort field (prefix `-` for descending, e.g., `--sort -date_created`)
- `--limit <n>` — Max results (default: 25)

## Process

1. Parse arguments from the input
2. Call `schema` tool with `keys: ["<collection>"]` to understand fields
3. Build query object:
   - Select the most useful fields based on schema (avoid fetching all fields on wide collections)
   - Apply filter if provided: `{ "<field>": { "_eq": "<value>" } }`
   - Apply sort if provided
   - Apply limit (default 25)
4. Call `items` tool with `action: "read"`, `collection`, and `query`
5. Display results as a formatted table
6. Show total count if available

## Example

Input: `posts --filter status=published --sort -date_created --limit 10`

```json
{
  "action": "read",
  "collection": "posts",
  "query": {
    "fields": ["id", "title", "status", "date_created"],
    "filter": { "status": { "_eq": "published" } },
    "sort": ["-date_created"],
    "limit": 10
  }
}
```
