---
description: List orders with optional status, payment type, and search filters
allowed-tools: ["mcp__teleshop__list_orders"]
argument-hint: [--status <status>] [--payment <type>] [--search <query>]
---

# List Orders

List orders from the Teleshop store with optional filters.

## Arguments
Format: `[--status <status>] [--payment <type>] [--search <query>]`
- --status: Filter by status (created, processing, awaiting, shipped, ready, completed, canceled)
- --payment: Filter by payment type (offlineCard, offlineCash, onlinePayment, cardPrepay, cardPartialPrepay, telegramStars)
- --search: Search by customer name, phone, or email

Parse from "$ARGUMENTS".

## Process

1. **List orders with filters:**
   ```
   list_orders({
     status: <status if provided>,
     paymentType: <payment if provided>,
     search: <search if provided>,
     sortBy: "createdAt",
     sortOrder: "DESC"
   })
   ```

2. **Display as table:**
   Show order number, status, customer name, total amount, payment status (paid/unpaid), payment type, date.

3. **Show summary:**
   Total orders found, orders by status breakdown.

## Example Usage
```
/list-orders
/list-orders --status created
/list-orders --status processing --payment onlinePayment
/list-orders --search "John"
```
