---
description: Import a full catalog of categories and products from JSON data
allowed-tools: ["mcp__teleshop__import_catalog", "mcp__teleshop__list_categories", "mcp__teleshop__list_products"]
argument-hint: <json-data-or-description> [--mode merge|replace]
---

# Import Catalog

Import categories and products into the store from structured JSON data.

## Arguments
Format: `<json-data-or-description> [--mode merge|replace]`
- json-data: JSON catalog data or a description of what to import
- --mode: Import mode — "merge" (default, safe) or "replace" (full reset)

Parse from "$ARGUMENTS".

## Process

1. **Parse the input data:**
   If user provides raw JSON, use it directly.
   If user describes what to import, construct the JSON.

2. **Import the catalog:**
   ```
   import_catalog({
     options: { mode: <mode or "merge">, stockControl: true },
     categories: [...],
     products: [...]
   })
   ```

3. **Verify the import:**
   ```
   list_categories() -> Show imported categories
   list_products(limit=10) -> Show sample of imported products
   ```

4. **Report results:**
   Show count of categories and products imported.

## Example Usage
```
/import-catalog {"categories": [{"externalId": "cat1", "title": "Electronics"}], "products": [{"sku": "P1", "title": "Phone", "price": 999}]}
/import-catalog --mode replace (with JSON data)
```

## Notes
- Default mode is "merge" (adds new items, updates existing by SKU)
- "replace" mode deletes ALL existing data first — use with caution
- Max request size: 10 MB
- Image URLs are downloaded automatically by the platform
