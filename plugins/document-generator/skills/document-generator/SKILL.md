---
name: document-generator
description: Document generation process -- format selection, data collection, script invocation, and delivery. This skill should be used when generating any document (proposal, invoice, report, presentation, contract), deciding which format or engine to use, or running generation scripts.
---

# Document Generator Process

Core process skill for generating professional business documents. Defines the end-to-end workflow from user request to delivered file.

## Generation Workflow

### Step 1: CLASSIFY

Determine the document type from the user's request:

| Keywords | Document Type | Default Format |
|----------|--------------|----------------|
| proposal, bid, offer, pitch | **proposal** | DOCX |
| invoice, bill, receipt | **invoice** | PDF |
| report, analysis, findings, research | **report** | DOCX |
| presentation, slides, deck, pitch deck | **presentation** | PPTX |
| contract, agreement, NDA, terms | **contract** | DOCX |
| convert, transform, export | **conversion** | varies |

### Step 2: GATHER

Collect required data from the user. Each document type has specific required and optional fields.

Refer to the **document-templates** skill for complete field checklists per document type. It defines exactly which fields are required, which are optional, and the expected format for each.

### Step 3: SELECT FORMAT & ENGINE

| Type | Format | Engine | Script |
|------|--------|--------|--------|
| Proposal | DOCX | docx-js | `generate_docx.js` |
| Proposal (final) | PDF | puppeteer | `generate_pdf.js` |
| Invoice | PDF | puppeteer | `generate_pdf.js` |
| Invoice (simple) | PDF | pdfkit | `generate_pdf.js` (engine: "pdfkit") -- uses generic structure, not invoice fields |
| Report | DOCX | docx-js | `generate_docx.js` |
| Report (final) | PDF | puppeteer | `generate_pdf.js` |
| Presentation | PPTX | pptxgenjs | `generate_pptx.js` |
| Presentation (PDF export) | PDF | pandoc | `convert.sh` (PPTX→PDF, as follow-up) |
| Contract | DOCX | docx-js | `generate_docx.js` |
| Contract (final) | PDF | puppeteer | `generate_pdf.js` |

### Step 4: BUILD JSON Input

1. Read the template file from `<plugin_dir>/templates/{type}_template.json`
2. Merge user data into the template structure
3. Set `outputPath` to: `{cwd}/{type}_{sanitized_title}_{YYYY-MM-DD}.{ext}`
4. Write the complete JSON input to a temp file: `{cwd}/.doc_input.json`

**Input JSON structure:**
```json
{
  "type": "proposal|invoice|report|contract",
  "engine": "puppeteer|pdfkit",
  "outputPath": "./proposal_acme_2026-03-17.docx",
  "template": { "...from template file..." },
  "data": { "...user provided data..." }
}
```

### Step 5: GENERATE

Run the appropriate script via Bash:
```bash
cd <plugin_dir> && node scripts/generate_docx.js /absolute/path/to/.doc_input.json
```

**Check dependencies first:**
```bash
cd <plugin_dir> && node -e "require('docx')" 2>&1
```
If it fails, tell the user: `cd <plugin_dir> && npm install`

**Script output** (JSON to stdout):
- Success: `{ "success": true, "outputPath": "/abs/path/to/file.docx", "size": 12345 }`
- Failure: `{ "success": false, "error": "description" }`

### Step 6: DELIVER

1. Parse the script's JSON output
2. Confirm the file exists and report its path and size
3. Offer follow-up actions: "Want me to convert this to PDF?" or "Want to make changes?"

## Format Conversion

For converting between formats, use the pandoc wrapper:
```bash
<plugin_dir>/scripts/convert.sh input.md output.pdf
```

Supported conversions: MD->PDF, MD->DOCX, MD->HTML, DOCX->PDF, DOCX->MD, HTML->PDF, HTML->DOCX, MD->PPTX

## Error Handling

| Error | Resolution |
|-------|-----------|
| Module not found (docx, puppeteer, etc.) | Tell user to run `npm install` in plugin dir |
| pandoc not installed | Tell user: `brew install pandoc` (macOS) or `apt install pandoc` (Linux) |
| No PDF engine for pandoc | Tell user: `brew install wkhtmltopdf` |
| Puppeteer browser launch failed | Add `--no-sandbox` flag (already in script) |
| Output file not created | Check script stderr, verify output directory exists |

## File Naming Convention

Pattern: `{type}_{title}_{date}.{ext}`

Sanitize title: lowercase, replace spaces with underscores, remove special characters, max 50 chars.

Examples:
- `proposal_acme_consulting_2026-03-17.docx`
- `invoice_inv-001_2026-03-17.pdf`
- `report_q1_analysis_2026-03-17.docx`
- `presentation_product_launch_2026-03-17.pptx`
- `contract_service_agreement_2026-03-17.docx`
