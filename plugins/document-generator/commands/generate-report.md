---
description: Generate a professional report (DOCX/PDF)
allowed-tools: ["Bash", "Read", "Write", "Glob"]
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

1. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/generate_docx.js`.

2. **Check dependencies.**

3. **Gather required data from user:**
   - Author name
   - Date
   - Introduction (context and purpose)
   - Findings (key data and observations)
   - Conclusions (what the data tells us)
   - Optional: methodology, analysis, recommendations, appendices

4. **Read template:**
   ```bash
   cat <plugin_dir>/templates/report_template.json
   ```

5. **Build JSON input:**
   Merge user data into template. Write to `.doc_input.json`.

6. **Generate document:**
   ```bash
   cd <plugin_dir> && node scripts/generate_docx.js /absolute/path/.doc_input.json
   ```

7. **Deliver result.**

## Example Usage
```
/generate-report "Q1 2026 Performance Analysis" --format pdf
/generate-report "Security Audit Findings" --type project
```
