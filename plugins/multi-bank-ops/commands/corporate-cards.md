---
description: List corporate cards with balances and status
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: [open|closed|all]
---

# Corporate Cards

List corporate cards from connected bank MCP servers.

## Arguments
Format: `[filter]`
- `open` — show only active cards (default)
- `closed` — show only closed cards
- `all` — show all cards

Parse from "$ARGUMENTS". If empty, default to "open".

## Process

1. **Discover corporate card tools:**
   - Search for tools with keywords: `corporate`, `card`, `картк`
   - If not found, inform user that their MCP server doesn't support corporate card listing

2. **Fetch cards:**
   - Pass filter: `o` for open, `c` for closed, empty for all
   - Parse response — may include multiple corporations with their cards

3. **Display results:**
   ```
   Корпоративні картки:

   | # | Картка      | Статус  | Баланс     | Валюта |
   |---|------------|---------|------------|--------|
   | 1 | ****1234   | Активна | ₴25 000,00 | UAH    |
   | 2 | ****5678   | Активна | $1 200,00  | USD    |
   | 3 | ****9012   | Закрита | ₴0,00      | UAH    |
   ```

4. **Offer related actions:**
   - View transactions for a specific card
   - Check balance history

## Safety

- **Always mask card numbers** — show only last 4 digits
- Never display full card numbers in output
