---
description: List email addressbooks with subscriber counts
allowed-tools: mcp__sendpulse__email_addressbooks_list
argument-hint: [--limit <number>]
---

# List Addressbooks

List email addressbooks (mailing lists) with subscriber counts.

## Arguments
Format: `[--limit <number>]`
- --limit: Number of addressbooks to return (default: 50)

Parse from "$ARGUMENTS".

## Process

1. **List addressbooks:**
   ```
   email_addressbooks_list(limit=<limit>, offset=0)
   ```

2. **Display as table:**
   - ID
   - Name
   - Subscriber count
   - Status

## Example Usage
```
/list-addressbooks
/list-addressbooks --limit 10
```

## Notes
- Shows all mailing lists with subscriber counts
- Default limit is 50
