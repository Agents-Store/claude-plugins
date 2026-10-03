#!/bin/bash

# Document Format Converter
# Converts between document formats using pandoc.
#
# Usage: ./convert.sh <input-file> <output-file>
# Supported: MD->PDF, MD->DOCX, MD->HTML, DOCX->PDF, DOCX->MD, HTML->PDF, HTML->DOCX
#
# PDF engine fallback chain (best to least):
#   1. weasyprint  — best CSS support, ideal for styled HTML->PDF
#   2. typst       — lightweight, no LaTeX installation needed
#   3. pdflatex    — LaTeX-based, good for academic docs (needs extra setup for Cyrillic)
#   4. (none)      — for a DOCX input suggests docx_to_pdf.js (Playwright) as alternative
# wkhtmltopdf is not used: the pandoc manual marks it deprecated.
#
# DOCX output: pandoc takes headings, lists and tables from the source, but the
# look (fonts, colours, spacing) comes only from assets/reference.docx. Pandoc
# ignores CSS, so an HTML source's styling does not reach the DOCX.
#
# Output: JSON to stdout { success, outputPath } or { success: false, error }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT="${1:-}"
OUTPUT="${2:-}"

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
  echo '{"success": false, "error": "Usage: ./convert.sh <input-file> <output-file>"}'
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  INPUT_SAFE=$(echo "$INPUT" | sed 's/["\]/\\&/g')
  echo "{\"success\": false, \"error\": \"Input file not found: $INPUT_SAFE\"}"
  exit 1
fi

if ! command -v pandoc &> /dev/null; then
  # Detect platform for install instructions
  if [[ "$OSTYPE" == "darwin"* ]]; then
    INSTALL_CMD="brew install pandoc"
  elif [[ "$OSTYPE" == "linux"* ]]; then
    INSTALL_CMD="sudo apt install -y pandoc"
  else
    INSTALL_CMD="See https://pandoc.org/installing.html"
  fi
  echo "{\"success\": false, \"error\": \"pandoc is not installed. Install with: $INSTALL_CMD\"}"
  exit 1
fi

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT")
mkdir -p "$OUTPUT_DIR"

# Determine output and input formats from extensions
OUTPUT_EXT="${OUTPUT##*.}"
OUTPUT_EXT=$(echo "$OUTPUT_EXT" | tr '[:upper:]' '[:lower:]')
INPUT_EXT="${INPUT##*.}"
INPUT_EXT=$(echo "$INPUT_EXT" | tr '[:upper:]' '[:lower:]')

PANDOC_ARGS=""

# Check for reference doc (for DOCX output)
REFERENCE_DOC="$SCRIPT_DIR/../assets/reference.docx"

case "$OUTPUT_EXT" in
  pdf)
    # PDF engine fallback chain: weasyprint > typst > pdflatex
    if command -v weasyprint &> /dev/null; then
      PANDOC_ARGS="--pdf-engine=weasyprint"
    elif command -v typst &> /dev/null; then
      PANDOC_ARGS="--pdf-engine=typst"
    elif command -v pdflatex &> /dev/null; then
      PANDOC_ARGS=""
    else
      # No pandoc PDF engine — suggest alternatives
      if [[ "$OSTYPE" == "darwin"* ]]; then
        INSTALL_CMDS="brew install weasyprint (recommended) or brew install typst"
      elif [[ "$OSTYPE" == "linux"* ]]; then
        INSTALL_CMDS="sudo apt install -y weasyprint (recommended) or install typst from https://github.com/typst/typst/releases"
      else
        INSTALL_CMDS="pip install weasyprint (recommended)"
      fi

      # DOCX input: the Playwright-based converter needs no pandoc PDF engine
      if [ -f "$SCRIPT_DIR/docx_to_pdf.js" ] && [ "$INPUT_EXT" = "docx" ]; then
        echo "{\"success\": false, \"error\": \"No pandoc PDF engine found. Use the Playwright converter instead. Run: node $SCRIPT_DIR/docx_to_pdf.js \\\"$INPUT\\\" \\\"$OUTPUT\\\"\", \"fallback\": \"playwright\", \"fallbackCmd\": \"node $SCRIPT_DIR/docx_to_pdf.js \\\"$INPUT\\\" \\\"$OUTPUT\\\"\"}"
        exit 1
      fi

      echo "{\"success\": false, \"error\": \"No PDF engine found for pandoc. Install one: $INSTALL_CMDS\"}"
      exit 1
    fi
    ;;
  docx)
    # The reference doc is the only source of DOCX styling (pandoc ignores CSS)
    if [ -f "$REFERENCE_DOC" ]; then
      PANDOC_ARGS="--reference-doc=$REFERENCE_DOC"
    fi
    ;;
  html)
    PANDOC_ARGS="--standalone"
    ;;
  md|markdown)
    PANDOC_ARGS=""
    ;;
  pptx)
    PANDOC_ARGS=""
    ;;
  *)
    echo "{\"success\": false, \"error\": \"Unsupported output format: .$OUTPUT_EXT\"}"
    exit 1
    ;;
esac

# Run pandoc
ERR_FILE=$(mktemp)
if pandoc "$INPUT" -o "$OUTPUT" $PANDOC_ARGS 2>"$ERR_FILE"; then
  OUTPUT_ABS=$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")
  SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat --printf="%s" "$OUTPUT" 2>/dev/null || echo "0")
  rm -f "$ERR_FILE"
  echo "{\"success\": true, \"outputPath\": \"$OUTPUT_ABS\", \"size\": $SIZE}"
else
  ERR=$(cat "$ERR_FILE" 2>/dev/null || echo "Unknown error")
  ERR_ESCAPED=$(echo "$ERR" | head -1 | sed 's/"/\\"/g')
  rm -f "$ERR_FILE"
  echo "{\"success\": false, \"error\": \"pandoc failed: $ERR_ESCAPED\"}"
  exit 1
fi
