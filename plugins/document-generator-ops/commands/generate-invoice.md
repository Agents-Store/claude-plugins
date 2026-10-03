---
description: Generate a professional invoice (PDF)
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <invoice-number> [--company <name>] [--client <name>]
---

# Generate Invoice

Generate a professional PDF invoice with company header, itemized table, tax calculation, and payment details.

## Arguments

Format: `<invoice-number> [--company <name>] [--client <name>]`
- invoice-number: Invoice reference number (required)
- --company: Your company name (optional)
- --client: Client name (optional)

Parse from "$ARGUMENTS".

## Process

1. **Plugin directory:**
   Scripts and templates live under `${CLAUDE_PLUGIN_ROOT}` (Claude Code substitutes it with the installed plugin path). Use it as is; do not search for the plugin.

2. **Check dependencies:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.js"
   ```
   If `ready` is false, show what is missing and ask permission to run the listed `installCommands`.

3. **Gather required data from user:**
   - Company info: name, address, email, phone
   - Client info: name, address, email
   - Date and due date
   - Line items: description, quantity, unit price for each
   - Tax rate or amount (if applicable)
   - Discount (if applicable)
   - Payment details: bank, IBAN, SWIFT (optional)
   - Notes (optional)

4. **Read template:**
   ```bash
   cat "${CLAUDE_PLUGIN_ROOT}/templates/invoice_template.json"
   ```

5. **Build JSON input:**
   Calculate totals: `item.total = qty * unitPrice`, `subtotal = sum(totals)`, `total = subtotal + tax - discount`.
   Write to `.doc_input.json`.

6. **Generate PDF:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_pdf.js" /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Parse output, show file path, size, and invoice summary table.

## Example Usage
```
/document-generator-ops:generate-invoice "INV-2026-001" --company "TechCo" --client "Acme Corp"
/document-generator-ops:generate-invoice "INV-042"
```
