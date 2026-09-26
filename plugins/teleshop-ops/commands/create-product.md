---
description: Create a new product in the store
allowed-tools: ["mcp__teleshop__create_product", "mcp__teleshop__list_categories"]
argument-hint: <title> <sku> <price> [--quantity <n>] [--category <id>] [--description <text>]
---

# Create Product

Create a new product in the Teleshop store.

## Arguments
Format: `<title> <sku> <price> [--quantity <n>] [--category <id>] [--description <text>]`
- title: Product title (required)
- sku: Unique product SKU (required)
- price: Product price (required)
- --quantity: Available quantity (default: 0)
- --category: Category ID to assign
- --description: Product description

Parse from "$ARGUMENTS".

## Process

1. **If no category provided, list available categories:**
   ```
   list_categories()
   ```
   Show categories so user can choose.

2. **Create the product:**
   ```
   create_product({
     title: <title>,
     sku: <sku>,
     price: <price>,
     quantity: <quantity or 0>,
     categoryId: <category if provided>,
     description: <description or title>,
     sellStatus: "available",
     isActive: true,
     stockControl: true
   })
   ```

3. **Display created product details:**
   Show ID, SKU, title, price, quantity, category.

## Example Usage
```
/create-product "iPhone 15 Pro" "IPHONE-15-PRO" 999.99
/create-product "Red T-Shirt" "TSHIRT-RED" 29.99 --quantity 100 --category 5
/create-product "Wireless Mouse" "MOUSE-001" 49.99 --quantity 50 --description "Ergonomic wireless mouse"
```
