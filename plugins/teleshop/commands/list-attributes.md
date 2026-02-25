---
description: List all product attributes with their values
allowed-tools: ["mcp__teleshop__list_attributes", "mcp__teleshop__get_attribute"]
argument-hint: [--search <query>]
---

# List Attributes

List all product attributes in the Teleshop store.

## Arguments
Format: `[--search <query>]`
- --search: Search attributes by name (optional)

Parse from "$ARGUMENTS".

## Process

1. **List all attributes:**
   ```
   list_attributes({
     search: <search if provided>,
     sortBy: "name",
     sortOrder: "ASC"
   })
   ```

2. **For each attribute, get details with values:**
   ```
   get_attribute(id=<each-attribute-id>)
   ```

3. **Display as table:**
   Show ID, name, type, isVariant flag, and values list.

## Example Usage
```
/list-attributes
/list-attributes --search Color
```

## Notes
- Types: select (dropdown), color (color picker), text (free text)
- Attributes with isVariant=true can create product variants
