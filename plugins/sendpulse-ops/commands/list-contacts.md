---
description: List CRM contacts
allowed-tools: mcp__sendpulse__crm_contacts_list
argument-hint: [--limit <number>]
---

# List Contacts

List CRM contacts with optional limit.

## Arguments
Format: `[--limit <number>]`
- --limit: Number of contacts to return (default: 50)

Parse from "$ARGUMENTS".

## Process

1. **List contacts:**
   ```
   crm_contacts_list(limit=<limit>, offset=0)
   ```

2. **Display as table:**
   - Name
   - Email
   - Phone
   - ID

## Example Usage
```
/list-contacts
/list-contacts --limit 20
```

## Notes
- Default limit is 50
- Results are paginated — use offset for more
