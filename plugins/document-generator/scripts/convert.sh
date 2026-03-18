#!/bin/bash

# Document Format Converter
# Converts between document formats using pandoc.
#
# Usage: ./convert.sh <input-file> <output-file>
# Supported: MD->PDF, MD->DOCX, MD->HTML, DOCX->PDF, DOCX->MD, HTML->PDF, HTML->DOCX
#
# Output: JSON to stdout { success, outputPath } or { success: false, error }

set -euo pipefail

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
  echo '{"success": false, "error": "pandoc is not installed. Install with: brew install pandoc (macOS) or apt install pandoc (Linux)"}'
  exit 1
fi

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT")
mkdir -p "$OUTPUT_DIR"

# Determine output format from extension
OUTPUT_EXT="${OUTPUT##*.}"
OUTPUT_EXT=$(echo "$OUTPUT_EXT" | tr '[:upper:]' '[:lower:]')

PANDOC_ARGS=""

case "$OUTPUT_EXT" in
  pdf)
    # Check for PDF engine
    if command -v wkhtmltopdf &> /dev/null; then
      PANDOC_ARGS="--pdf-engine=wkhtmltopdf"
    elif command -v weasyprint &> /dev/null; then
      PANDOC_ARGS="--pdf-engine=weasyprint"
    elif command -v pdflatex &> /dev/null; then
      PANDOC_ARGS=""
    else
      echo '{"success": false, "error": "No PDF engine found. Install one of: wkhtmltopdf, weasyprint, or pdflatex. Example: brew install wkhtmltopdf"}'
      exit 1
    fi
    ;;
  docx)
    PANDOC_ARGS=""
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
