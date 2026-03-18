---
description: Generate a professional business proposal (DOCX/PDF)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
argument-hint: <title> [--format <docx|pdf>] [--company <name>]
---

# Generate Proposal

Generate a professional business proposal with cover page, table of contents, structured sections, and branded formatting.

## Arguments

Format: `<title> [--format <docx|pdf>] [--company <name>]`
- title: Proposal title (required)
- --format: Output format -- docx (default, editable) or pdf (final version)
- --company: Your company name for branding (optional)

Parse from "$ARGUMENTS".

## Process

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_docx.js`.

2. **Check dependencies:**
   ```bash
   cd <plugin_dir> && node -e "require('docx')" 2>&1
   ```
   If missing, tell user to run `npm install` in plugin dir.

3. **Gather required data from user:**
   - Recipient (client name/company)
   - Executive summary (what is this proposal about?)
   - Problem statement (what problem does it solve?)
   - Proposed solution (what do you propose?)
   - Timeline (phases, milestones, duration)
   - Pricing (breakdown of costs)
   - Optional: about us, terms, branding colors

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/proposal_template.json
   ```

5. **Build JSON input:**
   Merge user data into the template structure. Write to `.doc_input.json` in current directory.

6. **Generate document:**
   ```bash
   cd <plugin_dir> && node scripts/generate_docx.js /absolute/path/.doc_input.json
   ```
   For PDF format, use `scripts/generate_pdf.js` instead.

7. **Deliver result:**
   Parse JSON output, show file path and size. Clean up temp input file. Offer to convert to another format.

## Example Usage
```
/generate-proposal "Cloud Migration Strategy" --company "TechCo Solutions"
/generate-proposal "Q2 Marketing Campaign" --format pdf
```
