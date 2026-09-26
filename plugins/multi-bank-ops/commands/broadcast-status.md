---
description: Show broadcast system status and active subscribers
allowed-tools: ["Bash", "Read", "Glob"]
---

# Broadcast Status

Display the current state of the broadcast event system — active subscribers, recent events, and delivery statistics.

## Process

1. **Read event log:**
   ```bash
   tail -50 ~/.multi-bank/events.jsonl
   ```
   Parse recent events for statistics.

2. **Display status:**
   ```
   Broadcast System Status
   ──────────────────────────────────────
   Event Log: ~/.multi-bank/events.jsonl
   Total Events: 1,247

   Recent Events (last 24h):
     balance_updated    ×12
     transaction_added  ×45
     budget_alert       ×3
     sync_complete      ×2

   Last Sync: 2026-03-23T14:30:00Z
   Last Event: 2026-03-23T14:30:05Z
   ──────────────────────────────────────

   Delivery Mechanisms:
     File-based (events.jsonl): Active
     WebSocket (ws://localhost:8765): Not running
     HTTP Polling: Not running
   ```

3. **Show last 5 events:**
   Display the 5 most recent events from the log with type, timestamp, and key payload fields.

4. **Suggest actions:**
   - Start WebSocket server for real-time subscribers
   - Review broadcast-pattern skill for setup guide
   - Check specific event type: `grep "budget_alert" events.jsonl`

## Example Usage
```
/broadcast-status
```
