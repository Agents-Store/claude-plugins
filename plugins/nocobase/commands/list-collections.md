---
description: List all NocoBase collections
allowed-tools: ["mcp__nocobase__collection_list", "mcp__nocobase__collection_get"]
argument-hint: [--details]
---

# List Collections

List all collections (data models) in the NocoBase instance.

## Arguments
Format: `[--details]`
- --details: Show field details for each collection (optional)

Parse from "$ARGUMENTS".

## Process

1. **List collections:**
   Use `collection_list` to get all collections.

2. **Show details (if requested):**
   For each collection of interest, use `collection_get` to show fields, relations, and configuration.

3. **Present results:**
   Display collections in a structured table with name, title, and field count.

## Example Usage
```
/list-collections
/list-collections --details
```
