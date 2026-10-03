---
description: Generate an Act of Completed Works (PDF)
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <title> [--format <pdf|docx>]
---

# Generate Act of Completed Works

Generate a professional Act of Completed Works with a services table, totals, and two-party signature blocks. Supports any language for all data values (company names, service descriptions, labels). The document language is determined by the `language` field in the input data.

## Arguments

Format: `<title> [--format <pdf|docx>]`
- title: Document title or act number (required, e.g., "ACT-001")
- --format: Output format — pdf (default) or docx

Parse from "$ARGUMENTS".

## Process

1. **Plugin directory:**
   Scripts and templates live under `${CLAUDE_PLUGIN_ROOT}` (Claude Code substitutes it with the installed plugin path). Use it as is; do not search for the plugin.

2. **Check dependencies:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.js"
   ```
   If `ready` is false, show what is missing and ask permission to run the listed `installCommands`. (`ready` covers Node, the npm modules and the Playwright browser; pandoc and the PDF engines are optional extras listed in `missing`.)

3. **Gather required data from user:**
   - Act number (e.g., ACT-001/2026)
   - Date and city
   - Reference to contract (optional, e.g., "Contract No. 001 dated 01.01.2026")
   - Contractor (service provider): name, representative, title, registration number, address
   - Customer (client): name, representative, title, registration number, address
   - Services table: each row needs description, unit (hrs/pcs/service), quantity, unit price, total
   - VAT rate (0 if not VAT payer, e.g., 20 for standard VAT)
   - Currency symbol ($ default)
   - Notes (optional)

4. **Read template:**
   ```bash
   cat "${CLAUDE_PLUGIN_ROOT}/templates/act_template.json"
   ```

5. **Build JSON input:**
   Use type "act" with playwright engine. Services is an array of rows. Write to `.doc_input.json`.

6. **Generate document:**
   For PDF (default):
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_pdf.js" /absolute/path/.doc_input.json
   ```
   For DOCX:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_docx.js" /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path and size. Remind user the act must be signed by both parties.

## Example Usage
```
/document-generator-ops:generate-act "ACT-001"
/document-generator-ops:generate-act "ACT-002/2026" --format docx
```

## Output filename
Pattern: `act_{number}_{date}.pdf` (e.g., `act_akt-001_2026-03-19.pdf`)
