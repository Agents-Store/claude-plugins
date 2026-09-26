---
description: List and search transaction history across all accounts
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <days> [category] [bank]
---

# Transactions

List recent transactions with optional filtering by time range, category, and bank.

## Arguments
Format: `<days> [category] [bank]`
- days: Number of days to look back (default: 90)
- category: Optional category filter (e.g., "Dining", "Groceries")
- bank: Optional bank filter — "monobank" or "privatbank"

Parse from "$ARGUMENTS".

## Process

1. **Fetch transactions via MCP:**
   - Call transaction/statement MCP tools for each bank
   - Apply date range filter (last N days)
   - If a bank filter is specified, query only that bank

2. **Auto-categorize:**
   - Use merchant name patterns from transaction-categorization skill
   - Apply category filter if specified

3. **Display results:**
   ```
   Transactions — Last 30 days
   ──────────────────────────────────────────────────────────────
   Date        Bank         Merchant          Category      Amount
   ──────────────────────────────────────────────────────────────
   2026-03-22  Monobank     Сільпо            Groceries    -₴345,67
   2026-03-22  Monobank     Bolt              Transport    -₴89,00
   2026-03-21  PrivatBank   Rozetka           Shopping     -₴1 299,00
   ──────────────────────────────────────────────────────────────
   Showing 156 transactions | Total: -₴12 523,45
   ```

4. **Offer follow-up actions:**
   - Export: `/export-report csv 30d`
   - Set budget: `/set-budget <category> <amount>`

## Example Usage
```
/transactions 30
/transactions 90 Groceries
/transactions 7 Dining monobank
```
