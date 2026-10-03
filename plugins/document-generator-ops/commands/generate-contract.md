---
description: Generate a contract or agreement (DOCX/PDF)
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <title> [--format <docx|pdf>] [--type <service|nda|employment>]
---

# Generate Contract

Generate a professional contract with numbered clauses, party details, and signature blocks.

## Arguments

Format: `<title> [--format <docx|pdf>] [--type <service|nda|employment>]`
- title: Contract title (required)
- --format: Output format -- docx (default, editable) or pdf (final version)
- --type: Contract type for suggested clause structure (optional)

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
   - Contract number (optional)
   - Date
   - Party 1: name, address, registration number
   - Party 2: name, address, registration number
   - Clause content:
     - Definitions (key terms)
     - Scope of services
     - Payment terms (amount, schedule, method)
     - Duration and termination conditions
     - Confidentiality terms
     - Governing law (jurisdiction)
   - Optional: IP rights, liability limits, force majeure, dispute resolution

4. **Read template:**
   ```bash
   cat "${CLAUDE_PLUGIN_ROOT}/templates/contract_template.json"
   ```

5. **Build JSON input:**
   Structure clauses with numbered format. Each clause can have multiple paragraphs (sub-clauses). Write to `.doc_input.json`.

6. **Generate document:**
   For DOCX (default):
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_docx.js" /absolute/path/.doc_input.json
   ```
   For PDF (final version):
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_pdf.js" /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path and size. Remind user this is a template -- recommend legal review before signing.

## Example Usage
```
/document-generator-ops:generate-contract "Service Agreement" --type service
/document-generator-ops:generate-contract "Non-Disclosure Agreement" --type nda
/document-generator-ops:generate-contract "Employment Contract"
```
