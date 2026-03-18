---
description: Convert between document formats (MD/DOCX/PDF/HTML/PPTX)
allowed-tools: ["Bash", "Read", "Glob"]
argument-hint: <input-file> --to <format>
---

# Convert Document

Convert a document between formats using pandoc.

## Arguments

Format: `<input-file> --to <format>`
- input-file: Path to the source file (required)
- --to: Target format -- pdf, docx, html, md, pptx (required)

Parse from "$ARGUMENTS".

## Supported Conversions

| From | To |
|------|----|
| Markdown (.md) | PDF, DOCX, HTML, PPTX |
| DOCX (.docx) | PDF, Markdown, HTML |
| HTML (.html) | PDF, DOCX, Markdown |

## Process

1. **Validate input file exists:**
   Use Glob or Read to confirm the file is present.

2. **Resolve plugin directory:**
   Find the plugin dir by globbing for `**/document-generator/scripts/convert.sh`.

3. **Check pandoc is installed:**
   ```bash
   which pandoc
   ```
   If missing, tell user: `brew install pandoc` (macOS) or `apt install pandoc` (Linux).

4. **Determine output filename:**
   Same name as input, with new extension. Example: `report.md` -> `report.pdf`.

5. **Run conversion:**
   ```bash
   <plugin_dir>/scripts/convert.sh <input-file> <output-file>
   ```

6. **Parse output:**
   Script returns JSON: `{ "success": true, "outputPath": "...", "size": N }`.
   Show the output file path and size.

## Example Usage
```
/convert-document report.md --to pdf
/convert-document proposal.docx --to pdf
/convert-document notes.md --to docx
```
