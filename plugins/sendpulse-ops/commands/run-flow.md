---
description: Run a chatbot automation flow for a contact
allowed-tools: mcp__sendpulse__chatbots_flows_list, mcp__sendpulse__chatbots_flows_run, mcp__sendpulse__chatbots_bots_list
argument-hint: <flow-id> <contact-id>
---

# Run Flow

Run a chatbot automation flow for a specific contact.

## Arguments
Format: `<flow-id> <contact-id>`
- flow-id: The automation flow ID (optional — lists flows if omitted)
- contact-id: The chatbot contact ID

Parse from "$ARGUMENTS".

## Process

1. **If no flow-id, list available bots and flows:**
   ```
   chatbots_bots_list()
   ```
   Ask user to select a bot.

   ```
   chatbots_flows_list(bot_id=<bot-id>)
   ```
   Show available flows. Ask user to select.

2. **Run the flow:**
   ```
   chatbots_flows_run(
     flow_id=<flow-id>,
     contact_id=<contact-id>
   )
   ```

3. **Report result:**
   - Flow name
   - Contact ID
   - Execution status

## Example Usage
```
/run-flow flow_welcome contact_abc123
/run-flow
```

## Notes
- If flow-id not provided, lists all bots and their flows
- The flow runs asynchronously — results depend on flow configuration
