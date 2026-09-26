---
description: List all connected chatbots with their channels and statistics
allowed-tools: mcp__sendpulse__chatbots_bots_list, mcp__sendpulse__chatbots_bots_statistics_show, mcp__sendpulse__chatbots_account_show
argument-hint: [--stats]
---

# List Bots

List all connected chatbots with their channels, and optionally show statistics.

## Arguments
Format: `[--stats]`
- --stats: Include subscriber count and engagement stats for each bot (optional)

Parse from "$ARGUMENTS".

## Process

1. **List all bots:**
   ```
   chatbots_bots_list()
   ```

2. **Display as table:**
   Show bot ID, name, channel type.

3. **If --stats flag provided, get statistics for each bot:**
   ```
   chatbots_bots_statistics_show(bot_id=<each-bot-id>)
   ```
   Add subscriber count and message stats to the table.

4. **Optionally show account info:**
   ```
   chatbots_account_show()
   ```
   Show plan limits and message usage.

## Example Usage
```
/list-bots
/list-bots --stats
```

## Notes
- Without --stats, only basic bot info is shown (faster)
- With --stats, makes one API call per bot — may be slower for many bots
