---
description: Show budget utilization and active alerts
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: [category]
---

# Budget Status

Display spending progress against all budgets, or a specific category.

## Arguments
Format: `[category]`
- category: Optional — show only this category's budget

Parse from "$ARGUMENTS".

## Process

1. **Load data:**
   - Decrypt budgets.enc for budget definitions
   - Decrypt transactions.enc for spending data

2. **Calculate spending per budget:**
   For each active budget:
   - Determine current period date range
   - Sum transactions matching category and period
   - Calculate percentage used
   - Determine remaining budget

3. **Display status table:**
   ```
   Budget Status — March 2026
   ─────────────────────────────────────────────────
   Category     Budget    Spent     Left      Status
   ─────────────────────────────────────────────────
   Dining       ₴5 000    ₴4 757    ₴243      95% !!
   Groceries    ₴8 000    ₴4 231    ₴3 769    53% !
   Transport    ₴2 000    ₴895      ₴1 105    45%
   Shopping     ₴3 000    ₴3 124    -₴124     104% !!!
   ─────────────────────────────────────────────────

   Legend: (none)=<50%  !=50-74%  !!=75-99%  !!!=100%+
   ```

4. **If specific category:**
   Show detailed view with:
   - Daily spending trend
   - Top merchants in this category
   - Days remaining in period
   - Projected end-of-period spending

## Example Usage
```
/budget-status
/budget-status Dining
```
