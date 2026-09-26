---
description: List products with optional search, category, status, and limit filters
allowed-tools: ["mcp__teleshop__list_products"]
argument-hint: [--search <query>] [--category <name>] [--status available|unavailable|preorder] [--limit <n>]
---

# List Products

List products from the Teleshop store with optional filters.

## Arguments
Format: `[--search <query>] [--category <name>] [--status available|unavailable|preorder] [--limit <n>]`
- --search: Search products by title
- --category: Filter by category name
- --status: Filter by sell status (available, unavailable, preorder)
- --limit: Number of products to show (default: 20)

Parse from "$ARGUMENTS".

## Process

1. **List products with provided filters:**
   ```
   list_products({
     search: <search if provided>,
     category: <category if provided>,
     sellStatus: <status if provided>,
     limit: <limit if provided, default 20>,
     sortBy: "createdAt",
     sortOrder: "DESC"
   })
   ```

2. **Display as table:**
   Show ID, SKU, title, price (with discount if any), quantity, status, category.

3. **Show pagination info:**
   Display current page, total items, total pages.

## Example Usage
```
/list-products
/list-products --search iPhone
/list-products --category Electronics --status available
/list-products --limit 50
```
