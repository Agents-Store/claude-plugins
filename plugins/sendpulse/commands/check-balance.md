---
description: Check Sendpulse account balance and email credits
allowed-tools: mcp__sendpulse__email_balance_show, mcp__sendpulse__email_balance_show_detail
argument-hint: [--detailed]
---

# Check Balance

Check Sendpulse account balance and available email credits.

## Arguments
Format: `[--detailed]`
- --detailed: Show detailed balance breakdown (optional)

Parse from "$ARGUMENTS".

## Process

1. **Get balance:**
   ```
   email_balance_show()
   ```
   Show current credit balance.

2. **If --detailed:**
   ```
   email_balance_show_detail()
   ```
   Show breakdown by plan type, bonus credits, and expiration dates.

3. **Report result:**
   - Total available credits
   - Plan details (if detailed)

## Example Usage
```
/check-balance
/check-balance --detailed
```

## Notes
- Basic view shows just the current balance
- Detailed view includes plan breakdown and expiration
