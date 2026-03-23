---
description: Export financial report as CSV or PDF
allowed-tools: ["Bash", "Read", "Write", "Glob", "mcp__monobank__*", "mcp__privatbank__*"]
argument-hint: <format> [date-range]
---

# Export Report

Generate and export a financial report in CSV or PDF format.

## Arguments
Format: `<format> [date-range]`
- format: `csv` or `pdf`
- date-range: Time period — `30d`, `90d`, `ytd`, `last-month`, `2026-Q1`, `2026-03`, or explicit `YYYY-MM-DD to YYYY-MM-DD`

Parse from "$ARGUMENTS". Default date-range: `90d`.

## Process

1. **Resolve plugin directory:**
   ```
   Glob: multi-bank/scripts/export_csv.js → parent dir
   ```

2. **Check dependencies:**
   For PDF: verify pdfkit is installed (`node -e "require('pdfkit')"`)
   If missing, ask permission to `npm install`.

3. **Ask output location:**
   "Where should I save the file?" Default: current working directory.

4. **Prepare data:**
   - Decrypt transactions.enc and accounts.enc
   - Parse date range using shortcuts from report-export skill
   - Filter and aggregate transactions

5. **Build input JSON:**
   Write to temp file following the format in report-export skill.

6. **Run export script:**
   ```bash
   node <plugin_dir>/scripts/export_csv.js /tmp/export_input.json
   # or
   node <plugin_dir>/scripts/export_pdf.js /tmp/report_input.json
   ```

7. **Verify and report:**
   - Check script output JSON for success
   - Report file path and size
   - Clean up temp input file

## Example Usage
```
/export-report csv 90d
/export-report pdf 2026-Q1
/export-report csv last-month
/export-report pdf ytd
```
