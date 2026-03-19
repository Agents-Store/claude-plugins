#!/usr/bin/env node
/**
 * Convert DOCX → PDF via pandoc (HTML) + Puppeteer
 * Usage: node docx_to_pdf.js <input.docx> <output.pdf>
 */
const { execSync } = require("child_process");
const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");

const [, , inputDocx, outputPdf] = process.argv;
if (!inputDocx || !outputPdf) {
  console.error("Usage: node docx_to_pdf.js <input.docx> <output.pdf>");
  process.exit(1);
}

(async () => {
  // 1. Convert DOCX → HTML fragment via pandoc
  const htmlFragment = execSync(
    `pandoc "${inputDocx}" -t html --wrap=none`,
    { encoding: "utf8" }
  );

  // 2. Wrap in professional corporate CSS
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    color: #1E293B;
    line-height: 1.4;
    background: #fff;
  }

  .page {
    max-width: 170mm;
    margin: 0 auto;
    padding: 20mm 0;
  }

  /* Cover page block */
  .cover-block {
    border-top: 6px solid #2563EB;
    padding-top: 18px;
    margin-bottom: 32px;
  }

  /* Headings */
  h1 {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 18pt;
    font-weight: bold;
    color: #1E3A5F;
    margin-top: 28px;
    margin-bottom: 8px;
    padding-bottom: 5px;
    border-bottom: 1.5px solid #2563EB;
  }

  h2 {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 14pt;
    font-weight: bold;
    color: #1E3A5F;
    margin-top: 20px;
    margin-bottom: 6px;
  }

  h3 {
    font-family: Arial, sans-serif;
    font-size: 12pt;
    font-weight: bold;
    color: #1E293B;
    margin-top: 16px;
    margin-bottom: 5px;
  }

  p {
    margin-bottom: 10px;
    line-height: 1.45;
  }

  strong { font-weight: 700; }

  /* Lists */
  ul, ol {
    margin: 6px 0 10px 22px;
  }
  li {
    margin-bottom: 4px;
    line-height: 1.4;
  }
  li::marker {
    color: #2563EB;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 10.5pt;
  }
  th {
    background: #1E3A5F;
    color: #fff;
    padding: 8px 12px;
    text-align: left;
    font-size: 10pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  td {
    padding: 7px 12px;
    border-bottom: 1px solid #E2E8F0;
    color: #1E293B;
  }
  tr:nth-child(even) td {
    background: #F8FAFC;
  }

  /* Section divider after first few paragraphs (cover page effect) */
  .section-break {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 20px 0;
  }

  /* Footer-like muted text */
  .muted {
    color: #64748B;
    font-size: 9pt;
  }

  /* Code blocks */
  pre, code {
    font-family: "Courier New", monospace;
    font-size: 9pt;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    padding: 2px 4px;
    border-radius: 2px;
  }
  pre { padding: 10px 14px; margin: 10px 0; }
</style>
</head>
<body>
<div class="page">
${htmlFragment}
</div>
</body>
</html>`;

  // 3. Launch Puppeteer and render PDF
  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle0" });
  await page.pdf({
    path: outputPdf,
    format: "A4",
    margin: { top: "20mm", bottom: "20mm", left: "20mm", right: "20mm" },
    printBackground: true,
  });
  await browser.close();

  const size = fs.statSync(outputPdf).size;
  console.log(JSON.stringify({ success: true, outputPath: outputPdf, size }));
})().catch((err) => {
  console.error(JSON.stringify({ success: false, error: err.message }));
  process.exit(1);
});
