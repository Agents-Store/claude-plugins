---
description: Prepare a payment to a recipient via bank MCP tools
allowed-tools: ["Bash", "Read", "Glob", "Grep", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <recipient-iban> <amount-uah> <destination>
---

# Prepare Payment

Prepare a payment through the bank's MCP server. The payment will be sent to the user's mobile app for signing.

## Arguments
Format: `<recipient-iban> <amount-uah> <destination>` or interactive (no arguments).

Parse from "$ARGUMENTS". If empty or incomplete, ask user for each field.

## Process

1. **Discover payment tools:**
   - Search available MCP tools for keywords: `payment`, `prepare`, `pay`
   - If no payment tools found, inform user that their MCP server doesn't support payments

2. **Collect payment details:**
   - Sender IBAN — ask user which account to send from (list accounts first)
   - Recipient IBAN — validate UA + 27 digits format
   - Recipient ЄДРПОУ — 8-digit company code
   - Recipient name — legal entity name
   - Amount — in UAH (convert to kopiykas: × 100)
   - Destination — payment purpose (6–420 characters)
   - External reference (optional) — for tracking

3. **Confirm with user:**
   Display a summary table:
   ```
   Від:          ****0001 (Monobank)
   Кому:         ****5678 (Назва отримувача)
   ЄДРПОУ:       12345678
   Сума:         ₴10 000,00
   Призначення:  Оплата за послуги за березень 2026
   ```
   Ask: "Підтвердити платіж? Після підготовки його потрібно підписати у мобільному додатку."

4. **Execute payment:**
   - Call the prepare-payment MCP tool with collected parameters
   - Amount must be in kopiykas (integer)
   - Currency: "980" (UAH)

5. **Report result:**
   - Show payment ID for tracking
   - Remind user to sign in mobile app
   - Offer to check payment status

## Budget Payments

If user mentions "бюджетний платіж", "податки", or "ПДВ":
- Ask for `payCode` (3-character code)
- Ask for `additionalInfo` (6–130 characters)
- Include both in the payment call

## Safety

- **Always confirm** before executing — payments are irreversible after signing
- **Mask IBANs** — show only last 4 digits
- **Display amounts in UAH**, not kopiykas
- Warn: "Після підпису платіж не можна скасувати"
