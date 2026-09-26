---
description: List all configured webhooks with their status
allowed-tools: ["mcp__teleshop__list_webhooks", "mcp__teleshop__get_webhook_stats"]
argument-hint:
---

# List Webhooks

List all configured webhooks in the Teleshop store.

## Process

1. **List all webhooks:**
   ```
   list_webhooks()
   ```

2. **Optionally get stats for each:**
   ```
   get_webhook_stats(id=<each-webhook-id>)
   ```

3. **Display as table:**
   Show ID, URL, events, enabled/disabled, delivery success rate.

## Example Usage
```
/list-webhooks
```
