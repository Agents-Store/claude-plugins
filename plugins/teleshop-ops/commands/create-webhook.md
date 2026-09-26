---
description: Create a new webhook for event notifications
allowed-tools: ["mcp__teleshop__get_webhook_events", "mcp__teleshop__create_webhook", "mcp__teleshop__get_webhook_secret", "mcp__teleshop__test_webhook"]
argument-hint: <url> [<event>]
---

# Create Webhook

Create a new webhook endpoint for receiving store event notifications.

## Arguments
Format: `<url> [<event>]`
- url: Webhook endpoint URL (required)
- event: Event type to subscribe to (optional — if not provided, shows available events)

Parse from "$ARGUMENTS".

## Process

1. **If no event specified, list available events:**
   ```
   get_webhook_events()
   ```
   Show all available event types for user to choose.

2. **Create the webhook:**
   ```
   create_webhook({
     url: <url>,
     events: [<event>]
   })
   ```

3. **Get signing secret:**
   ```
   get_webhook_secret(id=<webhook-id>)
   ```
   Show secret for payload verification.

4. **Test the webhook:**
   ```
   test_webhook(id=<webhook-id>)
   ```
   Verify delivery is working.

5. **Display results:**
   Show webhook ID, URL, events, secret, and test result.

## Example Usage
```
/create-webhook https://my-server.com/webhooks
/create-webhook https://my-server.com/webhooks order.created
```

## Notes
- Always save the signing secret for payload verification
- Test webhook immediately after creation to verify your endpoint is reachable
