---
description: Create a new product category
allowed-tools: ["mcp__teleshop__create_category", "mcp__teleshop__list_categories"]
argument-hint: <title> [--parent <id>] [--orderBy cheap|expensive|novelty|popular]
---

# Create Category

Create a new product category in the Teleshop store.

## Arguments
Format: `<title> [--parent <id>] [--orderBy cheap|expensive|novelty|popular]`
- title: Category name (required)
- --parent: Parent category ID for subcategory
- --orderBy: Default product sorting (cheap, expensive, novelty, popular)

Parse from "$ARGUMENTS".

## Process

1. **If --parent not provided, list existing categories for context:**
   ```
   list_categories()
   ```

2. **Create the category:**
   ```
   create_category({
     title: <title>,
     parentId: <parent if provided>,
     orderBy: <orderBy if provided>
   })
   ```

3. **Display created category:**
   Show ID, title, parent, ordering.

## Example Usage
```
/create-category "Electronics"
/create-category "Smartphones" --parent 5
/create-category "Sale" --orderBy cheap
```
