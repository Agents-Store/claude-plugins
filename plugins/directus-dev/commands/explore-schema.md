---
description: Explore the Directus schema — list all collections or get detailed field info for a specific collection
allowed-tools: ["mcp__directus__schema", "mcp__directus__system-prompt"]
argument-hint: [collection-name]
---

# Explore Schema

Explore the Directus data model.

## Process

1. If this is the first call in the session, call `system-prompt` tool first (no params)

2. **No argument provided:**
   - Call `schema` tool with no parameters (discovery mode)
   - Display all collections as a table: name, icon, notes
   - Group by collection folders if present
   - Show total collection count

3. **Collection name provided:**
   - Call `schema` tool with `keys: ["<collection-name>"]`
   - Display fields as a table: name, type, interface, required, notes
   - List relations: field → related collection (type)
   - Show display template if set

## Output Format

**Discovery mode:**
```
| Collection | Icon | Notes |
|-----------|------|-------|
| posts     | article | Blog posts |
| authors   | person  | Content authors |
```

**Detailed mode:**
```
## posts

| Field | Type | Interface | Required |
|-------|------|-----------|----------|
| title | string | input | Yes |
| content | text | rich-text-md | No |

Relations:
- author → authors (M2O)
- tags ↔ tags (M2M via posts_tags)
```
