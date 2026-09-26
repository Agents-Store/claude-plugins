#!/usr/bin/env node

/**
 * PDF Reader
 * Extracts text content from PDF files using pdf-parse.
 *
 * Usage: node read_pdf.js <input.json>
 * Input: JSON file with { inputPath: "path/to/file.pdf" }
 * Output: JSON to stdout { success, text, pages, info }
 */

const fs = require("fs");
const path = require("path");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) throw new Error("Usage: node read_pdf.js <input.json>");

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);

    if (!input.inputPath) throw new Error("inputPath is required");
    if (!fs.existsSync(input.inputPath)) throw new Error(`File not found: ${input.inputPath}`);

    const pdfParse = require("pdf-parse");
    const dataBuffer = fs.readFileSync(input.inputPath);
    const result = await pdfParse(dataBuffer);

    console.log(
      JSON.stringify({
        success: true,
        text: result.text,
        pages: result.numpages,
        info: {
          title: result.info?.Title || null,
          author: result.info?.Author || null,
          subject: result.info?.Subject || null,
          creator: result.info?.Creator || null,
          producer: result.info?.Producer || null,
          creationDate: result.info?.CreationDate || null,
        },
      })
    );
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

main();
