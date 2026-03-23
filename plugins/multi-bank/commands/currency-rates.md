---
description: Show current or historical currency exchange rates
allowed-tools: ["Bash", "Read", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: [history <start-date> <end-date>]
---

# Currency Rates

Show currency exchange rates from connected bank MCP servers.

## Arguments
Format: no arguments (current rates) or `history <start-date> <end-date>`

Parse from "$ARGUMENTS". If empty, show current rates.

## Process

### Current Rates (no arguments)

1. **Discover rate tools:**
   - Search for tools with keywords: `currency`, `rate`, `курс`
   - If not found, inform user that their MCP server doesn't support currency rates

2. **Fetch and display:**
   ```
   Курси валют (станом на 23.03.2026):

   | Валюта | Купівля  | Продаж   |
   |--------|----------|----------|
   | USD/UAH | 41.20   | 41.80    |
   | EUR/UAH | 44.50   | 45.30    |
   ```

3. If multiple banks connected, show comparison:
   ```
   | Валюта  | Monobank     | PrivatBank   |
   |---------|-------------|--------------|
   | USD buy  | 41.20      | 41.15        |
   | USD sell | 41.80      | 41.85        |
   ```

### History (with dates)

1. Parse start/end dates from arguments
2. Note: max 15 days per request — split if needed
3. Convert dates to format expected by tool (check schema)
4. Display as table or trend summary

## Notes

- Not all MCP servers provide currency rate tools
- History is limited to 15 days per request
