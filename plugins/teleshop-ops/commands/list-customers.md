---
description: List store customers with optional search
allowed-tools: ["mcp__teleshop__list_customers"]
argument-hint: [--search <query>]
---

# List Customers

List customers of the Teleshop store.

## Arguments
Format: `[--search <query>]`
- --search: Search by name, phone, email, or Telegram username (optional)

Parse from "$ARGUMENTS".

## Process

1. **List customers:**
   ```
   list_customers({
     search: <search if provided>,
     sortBy: "createdAt",
     sortOrder: "DESC"
   })
   ```

2. **Display as table:**
   Show ID, name, phone, email, Telegram username, registration date.

## Example Usage
```
/list-customers
/list-customers --search John
/list-customers --search "+380991234567"
```
