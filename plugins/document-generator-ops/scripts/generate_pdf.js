#!/usr/bin/env node

/**
 * PDF Document Generator
 * Generates professional PDF documents using Playwright (HTML->PDF) or PDFKit.
 *
 * All HTML templates are in html_templates.js — the single source of truth
 * for PDF layout. (The pandoc DOCX engine reuses the same HTML for structure
 * only: pandoc ignores CSS, so its DOCX does not look like the PDF.)
 *
 * Engines: Playwright (default; Puppeteer is used only if Playwright is not
 * installed and Puppeteer happens to be) or PDFKit (`"engine": "pdfkit"`, no browser).
 *
 * Usage: node generate_pdf.js <input.json>
 * Input: JSON file with document data
 * Output: JSON to stdout { success, outputPath } or { success: false, error }
 */

const fs = require("fs");
const path = require("path");
const { requirePreferences, mergePreferences, normalizeMargins } = require("./utils");
const { buildHtml, esc } = require("./html_templates");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) throw new Error("Usage: node generate_pdf.js <input.json>");

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);
    const { type, engine, outputPath, data, template } = input;

    // Check preferences (soft — does not block generation)
    const prefsCheck = requirePreferences(input);

    // Auto-merge user preferences (style, company info, logo) into input
    mergePreferences(input);

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    if (engine === "pdfkit") {
      await generateWithPdfKit(outputPath, data, template);
    } else {
      await generateWithBrowser(outputPath, data, type, template);
    }

    const stats = fs.statSync(outputPath);
    const result = { success: true, outputPath: path.resolve(outputPath), size: stats.size };
    if (!prefsCheck.exists) result.warning = prefsCheck.warning;
    console.log(JSON.stringify(result));
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

// ─── Browser-based PDF generation ────────────────────────────────────────────
// Playwright first; Puppeteer only as an optional fallback if Playwright is not installed.

async function generateWithBrowser(outputPath, data, type, template) {
  const { getDefaults } = require("./html_templates");
  const styling = template?.styling || {};
  const s = getDefaults(styling);
  const muted = s.muted;
  const border = s.border;

  // Build HTML from shared templates
  const html = buildHtml(data, styling, type, template);

  // Company name for page header
  const companyName = esc(
    data.companyInfo?.name || data.company || data.contractor?.name || ""
  );

  const margins = normalizeMargins(styling.margins, "pdf");

  // Playwright first
  try {
    await generateWithPlaywright(outputPath, html, margins, styling, companyName, muted, border);
    return;
  } catch (playwrightErr) {
    // If Playwright is not installed, fall back to Puppeteer
    if (playwrightErr.code === "MODULE_NOT_FOUND") {
      try {
        await generateWithPuppeteer(outputPath, html, margins, styling, companyName, muted, border);
        return;
      } catch (puppeteerErr) {
        if (puppeteerErr.code === "MODULE_NOT_FOUND") {
          throw new Error(
            "Neither playwright nor puppeteer is installed. " +
            `Run: cd "${path.resolve(__dirname, "..")}" && npm ci`
          );
        }
        throw puppeteerErr;
      }
    }
    throw playwrightErr;
  }
}

async function generateWithPlaywright(outputPath, html, margins, styling, companyName, muted, border) {
  const { chromium } = require("playwright");

  const headerTpl = `<div style="width:100%;padding:5px 18mm 0;font-family:Inter,Arial,sans-serif;font-size:7.5px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-bottom:0.5px solid ${border};"><span style="letter-spacing:0.02em;">${companyName}</span><span>&nbsp;</span></div>`;
  const footerTpl = `<div style="width:100%;padding:0 18mm 5px;font-family:Inter,Arial,sans-serif;font-size:7.5px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-top:0.5px solid ${border};"><span>&nbsp;</span><span style="letter-spacing:0.03em;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`;

  const browser = await chromium.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  // Fonts are embedded as base64, so no network is needed: wait for load + fonts, not "networkidle" (discouraged).
  await page.setContent(html, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: outputPath,
    format: styling.pageSize || "A4",
    margin: margins,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: headerTpl,
    footerTemplate: footerTpl,
  });
  await browser.close();
}

async function generateWithPuppeteer(outputPath, html, margins, styling, companyName, muted, border) {
  const puppeteer = require("puppeteer");

  const headerTpl = `<div style="width:100%;padding:5px 18mm 0;font-family:Inter,Arial,sans-serif;font-size:7.5px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-bottom:0.5px solid ${border};"><span style="letter-spacing:0.02em;">${companyName}</span><span>&nbsp;</span></div>`;
  const footerTpl = `<div style="width:100%;padding:0 18mm 5px;font-family:Inter,Arial,sans-serif;font-size:7.5px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-top:0.5px solid ${border};"><span>&nbsp;</span><span style="letter-spacing:0.03em;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`;

  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle0" });
  await page.pdf({
    path: outputPath,
    format: styling.pageSize || "A4",
    margin: margins,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: headerTpl,
    footerTemplate: footerTpl,
  });
  await browser.close();
}

// ─── PDFKit fallback ──────────────────────────────────────────────────────────

async function generateWithPdfKit(outputPath, data, template) {
  const PDFDocument = require("pdfkit");
  const doc = new PDFDocument({ size: "A4", margin: 50 });
  const stream = fs.createWriteStream(outputPath);
  doc.pipe(stream);

  const primaryColor = template?.styling?.primaryColor || "#0F172A";
  const accent = template?.styling?.accentColor || "#6366F1";
  const muted = "#64748B";

  if (data.title) {
    doc.fontSize(24).fillColor(primaryColor).font("Helvetica-Bold").text(data.title, { align: "center" });
    doc.moveDown();
  }

  if (data.date) doc.fontSize(11).fillColor(muted).font("Helvetica").text(`Date: ${data.date}`, { align: "center" });
  if (data.author) doc.fontSize(11).fillColor(muted).text(`Author: ${data.author}`, { align: "center" });
  doc.moveDown(2);

  if (data.sections) {
    for (const section of data.sections) {
      doc.fontSize(section.level === 1 ? 16 : 13).fillColor(primaryColor).font("Helvetica-Bold").text(section.heading);
      doc.moveDown(0.3);
      doc.moveTo(doc.x, doc.y).lineTo(doc.x + 40, doc.y).strokeColor(accent).lineWidth(2).stroke();
      doc.moveDown(0.5);
      if (section.content) {
        doc.fontSize(11).fillColor("#1E293B").font("Helvetica").text(section.content);
        doc.moveDown();
      }
    }
  }

  doc.end();
  await new Promise((resolve) => stream.on("finish", resolve));
}

main();
