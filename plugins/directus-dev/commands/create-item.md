---
description: Create a new item in a Directus collection
argument-hint: <collection> <field=value> [field=value...]
---

# Create Item

## Arguments

- `collection` (required) — Collection name
- `field=value` pairs — Field values for the new item

## Process

1. Parse collection name and field=value pairs from input
2. Call `schema` tool with `keys: ["<collection>"]` to check required fields
3. Warn if any required fields are missing from the input
4. Build data object from field=value pairs
5. Call `items` tool with:
   ```json
   {
     "action": "create",
     "collection": "<collection>",
     "data": [{ "field1": "value1", "field2": "value2" }]
   }
   ```
   **Remember: data is ALWAYS an array**
6. Display the created item with its ID
7. Suggest viewing the item or creating more

## Example

Input: `posts title="My New Post" status=draft content="Post content here"`

```json
{
  "action": "create",
  "collection": "posts",
  "data": [{
    "title": "My New Post",
    "status": "draft",
    "content": "Post content here"
  }]
}
```
