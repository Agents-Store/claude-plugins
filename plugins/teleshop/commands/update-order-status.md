---
description: Update the status of an order (created, processing, shipped, completed, etc.)
allowed-tools: ["mcp__teleshop__get_order", "mcp__teleshop__update_order_status"]
argument-hint: <order-id> <status>
---

# Update Order Status

Change the status of an order in the Teleshop store.

## Arguments
Format: `<order-id> <status>`
- order-id: The order ID (required)
- status: New status — created, processing, awaiting, shipped, ready, completed, canceled (required)

Parse from "$ARGUMENTS".

## Process

1. **Get current order details:**
   ```
   get_order(id=<order-id>)
   ```
   Show current status, customer name, total amount.

2. **Update the status:**
   ```
   update_order_status(id=<order-id>, status=<status>)
   ```

3. **Confirm the change:**
   Show order number with old status → new status.

## Example Usage
```
/update-order-status 456 processing
/update-order-status 789 shipped
/update-order-status 123 completed
```

## Notes
- Valid statuses: created, processing, awaiting, shipped, ready, completed, canceled
- Status flow: created → processing → awaiting → shipped → ready → completed
- Orders can be canceled from most statuses
