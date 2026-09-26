---
description: Send a chatbot campaign on a specific channel
allowed-tools: mcp__sendpulse__chatbots_bots_list, mcp__sendpulse__chatbots_bots_campaigns_t_send, mcp__sendpulse__chatbots_bots_campaigns_m_send, mcp__sendpulse__chatbots_bots_campaigns_wa_send, mcp__sendpulse__chatbots_bots_campaigns_i_send, mcp__sendpulse__chatbots_bots_campaigns_v_send
argument-hint: <channel> <bot-id> [message]
---

# Send Campaign

Send a chatbot campaign to all subscribers on a specific channel.

## Arguments
Format: `<channel> <bot-id> [message]`
- channel: telegram, whatsapp, instagram, messenger, or viber
- bot-id: The bot ID (optional — will list bots if omitted)
- message: The message text to send (optional — will prompt if omitted)

Parse from "$ARGUMENTS".

## Process

1. **List bots if needed:**
   ```
   chatbots_bots_list()
   ```
   Show available bots with their channels. Ask user to select if bot-id not provided.

2. **Map channel to tool:**
   - telegram → `chatbots_bots_campaigns_t_send`
   - messenger → `chatbots_bots_campaigns_m_send`
   - whatsapp → `chatbots_bots_campaigns_wa_send`
   - instagram → `chatbots_bots_campaigns_i_send`
   - viber → `chatbots_bots_campaigns_v_send`

3. **Send campaign:**
   ```
   chatbots_bots_campaigns_{channel}_send(
     bot_id=<bot-id>,
     messages=[{"type": "text", "text": "<message>"}]
   )
   ```

4. **Report result:**
   - Campaign status
   - Bot name and channel
   - Estimated audience size

## Example Usage
```
/send-campaign telegram bot_abc "New arrivals are here! Check our latest collection."
/send-campaign whatsapp
/send-campaign instagram bot_ig_001 "Flash sale: 30% off everything today!"
```

## Notes
- If no bot-id provided, lists all bots and asks user to choose
- If no message provided, prompts user for message content
- Channel names are case-insensitive
