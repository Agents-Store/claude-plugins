---
description: Show current balances across all connected bank accounts
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: [bank-name]
---

# Balances

Display current balances for all connected bank accounts, grouped by bank.

## Arguments
Format: `[bank-name]`
- bank-name: Optional filter — "monobank", "privatbank", or omit for all

Parse from "$ARGUMENTS".

## Process

1. **Fetch balances via MCP:**
   - List available MCP tools to discover monobank/privatbank tool names
   - Call balance/accounts tools for each connected bank
   - If a bank's MCP server is not responding, report the error and continue with others

2. **Display balances:**
   - Group by bank (Monobank, PrivatBank)
   - Show account name with masked number (****1234)
   - Show current balance in UAH
   - Calculate totals across all banks

3. **Format:**
   ```
   Account Summary
   ──────────────────────────────────────
   Monobank
     Чорна картка ****1234     ₴15 432,10
     Біла картка ****5678       ₴8 200,00

   PrivatBank
     Картка ****3456            ₴2 150,30
     Депозит ****7890          ₴50 000,00
   ──────────────────────────────────────
   Total:                     ₴75 782,40
   ```

4. **If bank-name filter provided:**
   Show only that bank's accounts.

## Example Usage
```
/balances
/balances monobank
/balances privatbank
```
