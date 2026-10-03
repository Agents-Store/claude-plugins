---
description: Generate a professional business proposal (DOCX/PDF)
allowed-tools: ["Bash", "Read", "Write"]
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

1. **Plugin directory:**
   Scripts and templates live under `${CLAUDE_PLUGIN_ROOT}` (Claude Code substitutes it with the installed plugin path). Use it as is; do not search for the plugin.

2. **Check dependencies:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/check_deps.js"
   ```
   If `ready` is false, show what is missing and ask permission to run the listed `installCommands`. (`ready` covers Node, the npm modules and the Playwright browser; pandoc and the PDF engines are optional extras listed in `missing`.)

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
   cat "${CLAUDE_PLUGIN_ROOT}/templates/proposal_template.json"
   ```

5. **Build JSON input:**
   Merge user data into the template structure. Write to `.doc_input.json` in current directory.

6. **Generate document:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_docx.js" /absolute/path/.doc_input.json
   ```
   For PDF format, run `node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_pdf.js" /absolute/path/.doc_input.json` instead.

7. **Deliver result:**
   Parse JSON output, show file path and size. Clean up temp input file. Offer to convert to another format.

## Example Usage
```
/document-generator-ops:generate-proposal "Cloud Migration Strategy" --company "TechCo Solutions"
/document-generator-ops:generate-proposal "Q2 Marketing Campaign" --format pdf
```
