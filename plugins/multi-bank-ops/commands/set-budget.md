---
description: Create or update a budget threshold with alerts
allowed-tools: ["Bash", "Read", "Write", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <category> <amount> [period]
---

# Set Budget

Create or update a spending budget for a category with automatic alert thresholds.

## Arguments
Format: `<category> <amount> [period]`
- category: Spending category (Dining, Groceries, Shopping, Transportation, etc.)
- amount: Budget limit in UAH
- period: Budget period — weekly, monthly (default), quarterly, yearly

Parse from "$ARGUMENTS".

## Process

1. **Validate category:**
   Check against known categories from transaction-categorization skill.
   If unknown category, warn but allow (user may have custom categories).

2. **Create budget definition:**
   ```json
   {
     "id": "budget_<category>_<period>",
     "category": "<category>",
     "amount": <amount>,
     "currency": "UAH",
     "period": "<period>",
     "thresholds": [50, 75, 90, 100],
     "accountFilter": [],
     "enabled": true
   }
   ```

3. **Check for existing budget:**
   - Decrypt budgets.enc
   - If budget for same category+period exists, update it
   - If new, add to the array

4. **Store encrypted:**
   Re-encrypt and write budgets.enc

5. **Confirm:**
   ```
   Budget created!
     Category: Dining
     Limit: ₴5 000,00/month
     Alerts at: 50%, 75%, 90%, 100%
     Tracking: All accounts
     Period: Mar 1 - Mar 31, 2026
   ```

6. **Show current spending if available:**
   If transactions exist for this category in the current period, show progress.

## Example Usage
```
/set-budget Dining 5000
/set-budget Groceries 8000 monthly
/set-budget Entertainment 1500 weekly
/set-budget Travel 20000 quarterly
```
