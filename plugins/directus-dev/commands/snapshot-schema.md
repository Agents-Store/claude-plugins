---
description: Get a schema snapshot — shows complete data model for one or more collections
allowed-tools: ["mcp__directus__schema", "mcp__directus__relations"]
argument-hint: [collection1 collection2 ...]
---

# Snapshot Schema

Get a detailed view of the Directus data model.

## Arguments

- `collection1 collection2 ...` (optional) — Specific collections to snapshot. If omitted, shows discovery overview.

## Process

1. **No arguments:**
   - Call `schema` tool (discovery mode) to list all collections
   - Display collections grouped by folders
   - Show collection count and notes

2. **With collection names:**
   - Call `schema` tool with `keys: ["collection1", "collection2", ...]`
   - For each collection, display:
     - Fields table: name, type, interface, required, default, notes
     - Relations: field → target collection (type, on_delete)
     - Meta: icon, display_template, singleton, versioning, archive settings
   - Call `relations` tool with `action: "read"` for full relation details

3. Format output for easy reading — this is useful for understanding what to migrate or document.

## Example

Input: `posts authors categories`

Shows detailed schema for posts, authors, and categories including all fields, relations, and meta configuration.
