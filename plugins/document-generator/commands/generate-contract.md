---
description: Generate a contract or agreement (DOCX)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
argument-hint: <title> [--type <service|nda|employment>]
---

# Generate Contract

Generate a professional contract with numbered clauses, party details, and signature blocks.

## Arguments

Format: `<title> [--type <service|nda|employment>]`
- title: Contract title (required)
- --type: Contract type for suggested clause structure (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_docx.js`.

2. **Check dependencies.**

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
   cat <plugin_dir>/templates/contract_template.json
   ```

5. **Build JSON input:**
   Structure clauses with numbered format. Each clause can have multiple paragraphs (sub-clauses). Write to `.doc_input.json`.

6. **Generate DOCX:**
   ```bash
   cd <plugin_dir> && node scripts/generate_docx.js /absolute/path/.doc_input.json
   ```
   Note: Contracts always generate as DOCX (needs edits and signatures).

7. **Deliver result:**
   Show file path and size. Remind user this is a template -- recommend legal review before signing.

## Example Usage
```
/generate-contract "Service Agreement" --type service
/generate-contract "Non-Disclosure Agreement" --type nda
/generate-contract "Employment Contract"
```
