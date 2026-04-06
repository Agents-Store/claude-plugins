#!/usr/bin/env node
/**
 * Convert DOCX -> PDF via pandoc (HTML) + Puppeteer
 *
 * Uses the shared html_templates.js design system for consistent styling
 * with all other document outputs (PDF, DOCX pandoc engine).
 *
 * Usage: node docx_to_pdf.js <input.docx> <output.pdf> [--margins "top,bottom,left,right"]
 *
 * Margins: CSS units ("28mm,22mm,18mm,18mm") or twips ("1440,1440,1080,1080").
 * Default: 28mm top, 22mm bottom, 18mm left/right.
 */
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const { normalizeMargins } = require("./utils");
const { fontLinks, getDefaults, getBaseStyles } = require("./html_templates");

const args = process.argv.slice(2);
const inputDocx = args.find((a) => !a.startsWith("--"));
const outputPdf = args.filter((a) => !a.startsWith("--"))[1];
const marginsArg = args.indexOf("--margins") !== -1 ? args[args.indexOf("--margins") + 1] : null;

if (!inputDocx || !outputPdf) {
  console.error("Usage: node docx_to_pdf.js <input.docx> <output.pdf> [--margins top,bottom,left,right]");
  process.exit(1);
}

// Parse margin argument
let margins = null;
if (marginsArg) {
  const parts = marginsArg.split(",").map((s) => s.trim());
  if (parts.length === 4) {
    margins = {
      top: isNaN(Number(parts[0])) ? parts[0] : Number(parts[0]),
      bottom: isNaN(Number(parts[1])) ? parts[1] : Number(parts[1]),
      left: isNaN(Number(parts[2])) ? parts[2] : Number(parts[2]),
      right: isNaN(Number(parts[3])) ? parts[3] : Number(parts[3]),
    };
  }
}

const pdfMargins = normalizeMargins(margins, "pdf");

(async () => {
  // 1. Check pandoc
  try {
    execSync("which pandoc", { encoding: "utf-8" });
  } catch (_) {
    throw new Error(
      "pandoc is not installed. Install with: brew install pandoc (macOS) or apt install pandoc (Linux)"
    );
  }

  // 2. Convert DOCX -> HTML fragment via pandoc
  const htmlFragment = execSync(`pandoc "${inputDocx}" -t html --wrap=none`, {
    encoding: "utf8",
  });

  // 3. Wrap in the plugin's shared design system CSS
  const s = getDefaults({});

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
${fontLinks()}
<style>
  ${getBaseStyles(s)}

  .page {
    max-width: 170mm;
    margin: 0 auto;
    padding: 20mm 0;
  }

  /* Headings — matching the shared template system */
  h1 {
    font-family: ${s.fontHeading};
    font-size: 18pt;
    font-weight: bold;
    color: ${s.primary};
    margin-top: 28px;
    margin-bottom: 8px;
    padding-bottom: 5px;
    border-bottom: 1.5px solid ${s.accent};
  }

  h2 {
    font-family: ${s.fontHeading};
    font-size: 14pt;
    font-weight: bold;
    color: ${s.primary};
    margin-top: 20px;
    margin-bottom: 6px;
  }

  h3 {
    font-family: ${s.fontBody};
    font-size: 12pt;
    font-weight: bold;
    color: ${s.textColor};
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

  /* Tables — navy header with alternating rows */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 10.5pt;
  }
  th {
    background: linear-gradient(135deg, ${s.primary}, ${s.accentDark || s.primary});
    color: #fff;
    padding: 10px 14px;
    text-align: left;
    font-size: 9pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  th:first-child { border-radius: 6px 0 0 0; }
  th:last-child { border-radius: 0 6px 0 0; }
  td {
    padding: 9px 14px;
    border-bottom: 0.5px solid ${s.borderLight || s.border};
    color: ${s.textColor};
    font-variant-numeric: tabular-lining-nums;
  }
  tr:nth-child(even) td {
    background: rgba(0, 0, 0, 0.015);
  }

  /* Code blocks */
  pre, code {
    font-family: "Courier New", monospace;
    font-size: 9pt;
    background: ${s.bgLight};
    border: 1px solid ${s.border};
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

  // 4. Render PDF — try Playwright first, fall back to Puppeteer
  let browser, page;
  try {
    const { chromium } = require("playwright");
    browser = await chromium.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle" });
  } catch (e) {
    if (e.code === "MODULE_NOT_FOUND") {
      const puppeteer = require("puppeteer");
      browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
      page = await browser.newPage();
      await page.setContent(html, { waitUntil: "networkidle0" });
    } else { throw e; }
  }
  await page.pdf({
    path: outputPdf,
    format: "A4",
    margin: pdfMargins,
    printBackground: true,
  });
  await browser.close();

  const size = fs.statSync(outputPdf).size;
  console.log(JSON.stringify({ success: true, outputPath: outputPdf, size }));
})().catch((err) => {
  console.error(JSON.stringify({ success: false, error: err.message }));
  process.exit(1);
});
