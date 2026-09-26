---
description: List all product categories with optional search
allowed-tools: ["mcp__teleshop__list_categories"]
argument-hint: [--search <query>]
---

# List Categories

List all product categories in the Teleshop store.

## Arguments
Format: `[--search <query>]`
- --search: Search categories by title (optional)

Parse from "$ARGUMENTS".

## Process

1. **List categories:**
   ```
   list_categories({
     search: <search if provided>,
     sortBy: "position",
     sortOrder: "ASC"
   })
   ```

2. **Display as hierarchy:**
   Show categories with indentation for subcategories.
   Include ID, title, product ordering, parent.

## Example Usage
```
/list-categories
/list-categories --search Electronics
```
