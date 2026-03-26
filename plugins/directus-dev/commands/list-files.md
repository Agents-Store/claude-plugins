---
description: List files in Directus with optional folder or type filter
allowed-tools: ["mcp__directus__files", "mcp__directus__folders"]
argument-hint: [--folder <name>] [--type <mime-prefix>]
---

# List Files

## Arguments

- `--folder <name>` — Filter by folder name
- `--type <mime-prefix>` — Filter by MIME type prefix (e.g., `image`, `application/pdf`)

## Process

1. If `--folder` provided:
   - Call `folders` tool with `action: "read"` to find folder UUID by name
   - Use folder UUID in file filter

2. Build file query:
   ```json
   {
     "action": "read",
     "query": {
       "fields": ["id", "title", "filename_download", "type", "filesize", "width", "height", "folder.name"],
       "filter": {},
       "sort": ["-uploaded_on"],
       "limit": 25
     }
   }
   ```
   - Add folder filter: `{ "folder": { "_eq": "<uuid>" } }`
   - Add type filter: `{ "type": { "_starts_with": "<prefix>/" } }`

3. Call `files` tool with the query
4. Display as table: title, filename, type, size, dimensions, folder
5. Format filesize as human-readable (KB, MB)

## Example

Input: `--type image --folder Products`

Lists all image files in the "Products" folder.
