---
description: Generate a Non-Disclosure Agreement (NDA) — PDF
allowed-tools: ["Bash", "Read", "Write", "Glob"]
argument-hint: [--type <mutual|unilateral>] [--party1 <name>] [--party2 <name>]
---

# Generate NDA

Generate a professional Non-Disclosure Agreement with standard legal clauses and signature blocks.

## Arguments

Format: `[--type <mutual|unilateral>] [--party1 <name>] [--party2 <name>]`
- --type: NDA type -- mutual (default, both parties bound) or unilateral (one-way)
- --party1: Disclosing party name (optional)
- --party2: Receiving party name (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_pdf.js`.

2. **Check dependencies.**

3. **Gather required data from user:**
   - NDA type: mutual (default) or unilateral
   - Date and jurisdiction (governing law)
   - Party 1 (Disclosing Party): name, address, representative, title
   - Party 2 (Receiving Party): name, address, representative, title
   - Optional customization:
     - Definition of confidential information (default provided)
     - Term duration (default: 2 years)
     - Survival period (default: 3 years)
     - Additional clauses
   - Most clauses have professional defaults -- only ask for party info and customizations

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/nda_template.json
   ```

5. **Build JSON input:**
   Set `"type": "nda"` and `"ndaType": "mutual"` or `"unilateral"`.
   Default clauses are built-in -- only override if user requests specific wording.
   Write to `.doc_input.json`.

6. **Generate PDF:**
   ```bash
   cd <plugin_dir> && node scripts/generate_pdf.js /absolute/path/.doc_input.json
   ```

7. **Deliver result:**
   Show file path and size. Remind user this is a template -- recommend legal review before signing.

## Example Usage
```
/generate-nda --type mutual --party1 "Acme Corp" --party2 "TechStart Inc"
/generate-nda --type unilateral
/generate-nda
```
