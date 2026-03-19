---
description: Generate an Act of Completed Works / Акт виконаних робіт (PDF)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
argument-hint: <title> [--format <pdf|docx>]
---

# Generate Act of Completed Works

Generate a Ukrainian-format Act of Completed Works (Акт виконаних робіт) with a services table, totals, and two-party signature blocks. Data values (company names, service descriptions) can be in any language.

## Arguments

Format: `<title> [--format <pdf|docx>]`
- title: Document title or act number (required, e.g., "АКТ-001")
- --format: Output format — pdf (default) or docx

Parse from "$ARGUMENTS".

## Process

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_docx.js`.

2. **Check dependencies.**

3. **Gather required data from user:**
   - Act number (e.g., АКТ-001/2026)
   - Date and city
   - Reference to contract (optional, e.g., "Договір №001 від 01.01.2026")
   - Contractor (Виконавець): name, representative, title, registration number, address
   - Customer (Замовник): name, representative, title, registration number, address
   - Services table: each row needs description, unit (год/шт/послуга), quantity, unit price, total
   - VAT rate (0 if not VAT payer, e.g., 20 for standard VAT)
   - Currency symbol (₴ default)
   - Notes (optional)

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/act_template.json
   ```

5. **Build JSON input:**
   Use type "act" with puppeteer engine. Services is an array of rows. Write to `.doc_input.json`.

6. **Generate document:**
   For PDF (default):
   ```bash
   cd <plugin_dir> && node scripts/generate_pdf.js /absolute/path/.doc_input.json
   ```
   For DOCX:
   ```bash
   cd <plugin_dir> && node scripts/generate_docx.js /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path and size. Remind user the act must be signed by both parties.

## Example Usage
```
/generate-act "АКТ-001"
/generate-act "АКТ-002/2026" --format docx
```

## Output filename
Pattern: `act_{number}_{date}.pdf` (e.g., `act_akt-001_2026-03-19.pdf`)
