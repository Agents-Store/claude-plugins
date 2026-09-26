---
description: Browse electronic documents (EDO) — inbox, outbox, all documents
allowed-tools: ["Bash", "Read", "Glob", "Grep", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <inbox|outbox|all> [date-range]
---

# Electronic Document Journal

Browse electronic documents exchanged with bank counterparties via MCP tools.

## Arguments
Format: `<view> [start-date] [end-date]`
- `inbox` — incoming documents
- `outbox` — outgoing documents
- `all` — all documents

Optional date range: `2026-03-01 2026-03-31` (defaults to last 30 days)

Parse from "$ARGUMENTS". If empty, default to "all" for last 30 days.

## Process

1. **Discover EDO tools:**
   - Search for tools with keywords: `edoc`, `document`, `journal`, `inbox`, `outbox`
   - If not found, inform user that their MCP server doesn't support EDO

2. **Fetch documents:**
   - Convert dates to the format expected by the tool (check schema — typically YYYY-MM-DD)
   - Call the appropriate journal endpoint (inbox/outbox/all)
   - Handle pagination if results exceed page limit

3. **Display results:**
   Present as a table:
   ```
   | # | Дата       | Тип    | Статус   | Від/Кому (ОКПО) | Сума       |
   |---|-----------|--------|----------|------------------|------------|
   | 1 | 2026-03-20 | Акт    | Підписано | ****5678        | ₴15 000,00 |
   | 2 | 2026-03-19 | Рахунок | Очікує   | ****1234        | ₴8 500,00  |
   ```

4. **Offer actions:**
   - View specific document details
   - Check signature info
   - Delete document (with confirmation)

## Safety

- **Mask ОКПО/ЄДРПОУ** — show only last 4 digits unless user requests full code
- Confirm before deleting documents
