---
description: Force-sync all connected bank accounts via MCP
allowed-tools: ["Bash", "Read", "Write", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
---

# Sync Accounts

Trigger a full sync of all connected bank accounts — fetch latest balances and transactions from Monobank and PrivatBank via MCP, emit broadcast events.

## Process

1. **Discover available banks:**
   - List available MCP tools
   - Identify which banks have active MCP connections (monobank, privatbank)

2. **Sync each bank:**
   For each connected bank:
   a. Call balance/accounts MCP tool → update balances
   b. Call transactions/statements MCP tool (since last sync) → get new transactions
   c. Auto-categorize new transactions using merchant patterns
   d. Emit `balance_updated` events for each account
   e. Emit `transaction_added` events for each new transaction

3. **Check budgets:**
   For each new transaction, run budget alert checks.
   Emit `budget_alert` events for any threshold crossings.

4. **Emit sync_complete:**
   After all banks processed.

5. **Cache results:**
   Write synced data to encrypted cache for offline access.

6. **Report results:**
   ```
   Sync complete!
   • 2 banks synced (Monobank, PrivatBank)
   • 4 accounts updated
   • 28 new transactions
   • 1 budget alert (Groceries at 85%)

   Events emitted:
     balance_updated    ×4
     transaction_added  ×28
     budget_alert       ×1
     sync_complete      ×1
   ```

## Example Usage
```
/sync-accounts
```
