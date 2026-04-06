---
description: Generate a professional invoice (PDF)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
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

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_pdf.js`.

2. **Check dependencies:**
   ```bash
   cd <plugin_dir> && node -e "require('playwright')" 2>&1
   ```

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
   cat <plugin_dir>/templates/invoice_template.json
   ```

5. **Build JSON input:**
   Calculate totals: `item.total = qty * unitPrice`, `subtotal = sum(totals)`, `total = subtotal + tax - discount`.
   Write to `.doc_input.json`.

6. **Generate PDF:**
   ```bash
   cd <plugin_dir> && node scripts/generate_pdf.js /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Parse output, show file path, size, and invoice summary table.

## Example Usage
```
/generate-invoice "INV-2026-001" --company "TechCo" --client "Acme Corp"
/generate-invoice "INV-042"
```
