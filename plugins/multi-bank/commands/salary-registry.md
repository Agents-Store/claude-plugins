---
description: Manage salary registries — create, check status, list types
allowed-tools: ["Bash", "Read", "Write", "Glob", "Grep", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <create|status|types> [registry-id]
---

# Salary Registry

Manage salary registries (зарплатні відомості) through bank MCP tools.

## Arguments
Format: `<action> [id]`
- `types` — list available registry types
- `create` — create a new salary registry (interactive)
- `status <registry-id>` — check registry status

Parse from "$ARGUMENTS". If empty, show available actions.

## Process

### Action: types

1. Discover salary registry type tools (keywords: `salary`, `registry`, `type`)
2. Call the types endpoint
3. Display available types in a table

### Action: create

1. **Discover salary tools:**
   - Search for tools with keywords: `salary`, `registry`, `create`
   - If not found, inform user their MCP doesn't support salary operations

2. **Collect registry details:**
   - Registry name (e.g., "Заробітна плата за березень 2026")
   - Sender IBAN — company account to send from
   - Registry type — from available types
   - Period: from date (YYYY-MM-DD) and to date (YYYY-MM-DD)

3. **Collect recipients:**
   Ask user for a list of recipients. Accept as:
   - Typed list (ПІБ, IBAN, сума)
   - JSON file path
   - CSV file path

   Each recipient needs:
   - fullName: "Прізвище Ім'я По батькові"
   - iban: recipient's IBAN
   - amount: in **kopiykas** (convert from UAH × 100)
   - inn (optional): ІПН

4. **Confirm:**
   Show summary:
   ```
   Відомість:    Заробітна плата за березень 2026
   Від рахунку:  ****0001
   Тип:          salary
   Період:       2026-03-01 — 2026-03-31
   Отримувачів:  15
   Загальна сума: ₴450 000,00
   ```
   Ask: "Підтвердити створення відомості?"

5. **Execute and report:**
   - Create registry via MCP tool
   - Return registry ID
   - Offer to check status

### Action: status

1. Call the salary registry status tool with the provided ID
2. Display current status and details
3. If still processing, offer to check again later

## Safety

- **Always confirm** before creating registries — involves real money
- **Mask IBANs and ІПН** in output
- **Show amounts in UAH**, not kopiykas
- **Verify total** — sum all recipient amounts and display before confirming
