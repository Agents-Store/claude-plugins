---
description: Send a transactional email via SMTP
allowed-tools: mcp__sendpulse__smtp_emails_send, mcp__sendpulse__smtp_senders_list, mcp__sendpulse__smtp_unsubscribes_is_unsubscribed
argument-hint: <to-email> <subject> <body>
---

# Send SMTP Email

Send a transactional email via SMTP with delivery checks.

## Arguments
Format: `<to-email> <subject> <body>`
- to-email: Recipient email address
- subject: Email subject line
- body: Email body (HTML or plain text)

Parse from "$ARGUMENTS".

## Process

1. **Check unsubscribe status:**
   ```
   smtp_unsubscribes_is_unsubscribed(email=<to-email>)
   ```
   If unsubscribed, warn user and stop.

2. **List senders:**
   ```
   smtp_senders_list()
   ```
   Use first available sender or ask user to choose.

3. **Send email:**
   ```
   smtp_emails_send(email={
     subject: <subject>,
     from: {name: <sender-name>, email: <sender-email>},
     to: [{email: <to-email>}],
     html: <body>
   })
   ```

4. **Report result:**
   - Message ID
   - Delivery status
   - Sender used

## Example Usage
```
/send-smtp-email customer@example.com "Order Confirmed" "<h1>Thank you!</h1><p>Your order has been confirmed.</p>"
/send-smtp-email user@example.com "Password Reset" "Click here to reset your password: ..."
```

## Notes
- Checks unsubscribe status before sending
- If recipient is unsubscribed, warns and does not send
- Body can be HTML or plain text
