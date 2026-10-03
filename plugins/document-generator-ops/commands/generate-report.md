---
description: Generate a professional report (DOCX/PDF)
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <title> [--format <docx|pdf>] [--type <annual|quarterly|project>]
---

# Generate Report

Generate a professional report with cover page, table of contents, structured sections, page numbers, and headers/footers.

## Arguments

Format: `<title> [--format <docx|pdf>] [--type <annual|quarterly|project>]`
- title: Report title (required)
- --format: Output format -- docx (default, editable) or pdf (final)
- --type: Report type hint for structure suggestions (optional)

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
   - Author name
   - Date
   - Introduction (context and purpose)
   - Findings (key data and observations)
   - Conclusions (what the data tells us)
   - Optional: methodology, analysis, recommendations, appendices

4. **Read template:**
   ```bash
   cat "${CLAUDE_PLUGIN_ROOT}/templates/report_template.json"
   ```

5. **Build JSON input:**
   Merge user data into template. Write to `.doc_input.json`.

6. **Generate document:**
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/generate_docx.js" /absolute/path/.doc_input.json
   ```

7. **Deliver result.**

## Example Usage
```
/document-generator-ops:generate-report "Q1 2026 Performance Analysis" --format pdf
/document-generator-ops:generate-report "Security Audit Findings" --type project
```
