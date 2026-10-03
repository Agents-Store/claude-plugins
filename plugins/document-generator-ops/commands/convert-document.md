---
description: Convert between document formats (MD/DOCX/PDF/HTML/PPTX)
allowed-tools: ["Bash", "Read"]
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
   Use Read (or `test -f <input-file>` via Bash) to confirm the file is present.

2. **Plugin directory:**
   The converter is `${CLAUDE_PLUGIN_ROOT}/scripts/convert.sh` (Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` with the installed plugin path). Do not search for the plugin.

3. **Check pandoc is installed:**
   ```bash
   which pandoc
   ```
   If missing, tell user: `brew install pandoc` (macOS) or `apt install pandoc` (Linux).

4. **Determine output filename:**
   Same name as input, with new extension. Example: `report.md` -> `report.pdf`.

5. **Run conversion:**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/convert.sh" <input-file> <output-file>
   ```

6. **Parse output:**
   Script returns JSON: `{ "success": true, "outputPath": "...", "size": N }`.
   Show the output file path and size.
   For `--to pdf` the script needs a pandoc PDF engine (WeasyPrint, Typst or pdflatex); if none is found it says what to install. A DOCX source can also go through the Playwright converter it names in `fallbackCmd`.
   For `--to docx`, pandoc takes the structure (headings, lists, tables) from the source; the look comes from the plugin's `assets/reference.docx`. Pandoc ignores CSS, so do not promise that an HTML or PDF-styled source keeps its styling in the DOCX.

## Example Usage
```
/document-generator-ops:convert-document report.md --to pdf
/document-generator-ops:convert-document proposal.docx --to pdf
/document-generator-ops:convert-document notes.md --to docx
```
