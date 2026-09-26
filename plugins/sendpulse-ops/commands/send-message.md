---
description: Send a direct message to a chatbot contact on any channel
allowed-tools: mcp__sendpulse__chatbots_contacts_show, mcp__sendpulse__chatbots_contacts_messages_t_send, mcp__sendpulse__chatbots_contacts_messages_m_send, mcp__sendpulse__chatbots_contacts_messages_wa_send, mcp__sendpulse__chatbots_contacts_messages_i_send, mcp__sendpulse__chatbots_contacts_messages_v_send, mcp__sendpulse__chatbots_contacts_messages_lc_send
argument-hint: <contact-id> <message>
---

# Send Message

Send a direct message to a chatbot contact. Auto-detects the correct channel.

## Arguments
Format: `<contact-id> <message>`
- contact-id: The chatbot contact ID
- message: The text message to send

Parse from "$ARGUMENTS".

## Process

1. **Get contact details:**
   ```
   chatbots_contacts_show(contact_id=<contact-id>)
   ```
   Determine the contact's channel type.

2. **Send message on correct channel:**
   Route to the appropriate tool based on channel:
   - Telegram → `chatbots_contacts_messages_t_send`
   - Messenger → `chatbots_contacts_messages_m_send`
   - WhatsApp → `chatbots_contacts_messages_wa_send`
   - Instagram → `chatbots_contacts_messages_i_send`
   - Viber → `chatbots_contacts_messages_v_send`
   - Live Chat → `chatbots_contacts_messages_lc_send`

   ```
   chatbots_contacts_messages_{channel}_send(
     contact_id=<contact-id>,
     messages=[{"type": "text", "text": "<message>"}]
   )
   ```

3. **Report result:**
   - Contact name and channel
   - Delivery status

## Example Usage
```
/send-message contact_abc123 "Hi! Your order has been shipped."
/send-message contact_xyz "Reminder: your appointment is tomorrow at 10am."
```

## Notes
- Channel is auto-detected from contact data
- If contact not found, an error is returned
- Message is sent as plain text
