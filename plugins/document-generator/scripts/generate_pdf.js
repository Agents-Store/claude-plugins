#!/usr/bin/env node

/**
 * PDF Document Generator
 * Generates professional PDF documents using Puppeteer (HTML->PDF) or PDFKit.
 *
 * Usage: node generate_pdf.js <input.json>
 * Input: JSON file with document data
 * Output: JSON to stdout { success, outputPath } or { success: false, error }
 */

const fs = require("fs");
const path = require("path");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) throw new Error("Usage: node generate_pdf.js <input.json>");

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);
    const { type, engine, outputPath, data, template } = input;

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    if (engine === "pdfkit") {
      await generateWithPdfKit(outputPath, data, template);
    } else {
      await generateWithPuppeteer(outputPath, data, type, template);
    }

    const stats = fs.statSync(outputPath);
    console.log(JSON.stringify({ success: true, outputPath: path.resolve(outputPath), size: stats.size }));
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

async function generateWithPuppeteer(outputPath, data, type, template) {
  const puppeteer = require("puppeteer");
  const styling = template?.styling || {};
  const primaryColor = styling.primaryColor || "#2563EB";
  const accentColor = styling.accentColor || "#F59E0B";
  const fontFamily = styling.fontFamily || "Helvetica, Arial, sans-serif";
  const margins = styling.margins || { top: "20mm", bottom: "20mm", left: "15mm", right: "15mm" };

  let html = "";

  if (type === "invoice") {
    html = buildInvoiceHtml(data, primaryColor, accentColor, fontFamily, template);
  } else {
    html = buildGenericHtml(data, primaryColor, fontFamily);
  }

  const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle0" });
  await page.pdf({
    path: outputPath,
    format: styling.pageSize || "A4",
    margin: margins,
    printBackground: true,
  });
  await browser.close();
}

function buildInvoiceHtml(data, primaryColor, accentColor, fontFamily, template) {
  const currency = template?.currencySymbol || data.currencySymbol || "$";
  const items = data.items || [];
  const subtotal = data.subtotal ?? items.reduce((sum, i) => sum + (i.total || i.quantity * i.unitPrice || 0), 0);
  const tax = data.tax ?? 0;
  const discount = data.discount ?? 0;
  const total = data.total ?? subtotal + tax - discount;

  const itemRows = items
    .map(
      (item, idx) => `
    <tr style="background: ${idx % 2 === 0 ? "#fff" : "#F8FAFC"}">
      <td style="padding: 10px 12px; border-bottom: 1px solid #E5E7EB;">${item.description || ""}</td>
      <td style="padding: 10px 12px; text-align: center; border-bottom: 1px solid #E5E7EB;">${item.quantity || ""}</td>
      <td style="padding: 10px 12px; text-align: right; border-bottom: 1px solid #E5E7EB;">${currency}${formatNum(item.unitPrice)}</td>
      <td style="padding: 10px 12px; text-align: right; border-bottom: 1px solid #E5E7EB;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  const companyInfo = data.companyInfo || {};
  const recipient = data.recipientInfo || {};

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body { font-family: ${fontFamily}; color: #1F2937; margin: 0; padding: 0; font-size: 14px; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; }
  .company-name { font-size: 24px; font-weight: bold; color: ${primaryColor}; }
  .invoice-title { font-size: 36px; font-weight: bold; color: ${primaryColor}; text-align: right; }
  .meta-table { margin-bottom: 30px; }
  .meta-table td { padding: 4px 12px; }
  .meta-label { font-weight: bold; color: #6B7280; }
  .info-block { display: flex; justify-content: space-between; margin-bottom: 30px; }
  .info-section h3 { margin: 0 0 8px; color: ${primaryColor}; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
  .info-section p { margin: 2px 0; color: #4B5563; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
  table.items th { background: ${primaryColor}; color: white; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  table.items th:nth-child(2) { text-align: center; }
  table.items th:nth-child(3), table.items th:nth-child(4) { text-align: right; }
  .totals { width: 300px; margin-left: auto; }
  .totals tr td { padding: 6px 12px; }
  .totals .total-row { font-size: 18px; font-weight: bold; color: ${primaryColor}; border-top: 2px solid ${primaryColor}; }
  .payment-section { margin-top: 40px; padding: 20px; background: #F8FAFC; border-radius: 8px; }
  .payment-section h3 { margin: 0 0 12px; color: ${primaryColor}; }
  .notes { margin-top: 30px; color: #6B7280; font-size: 12px; }
</style></head><body>

<div class="header">
  <div>
    <div class="company-name">${companyInfo.name || "Company Name"}</div>
    <p style="color: #6B7280; margin: 4px 0;">${companyInfo.address || ""}</p>
    <p style="color: #6B7280; margin: 4px 0;">${companyInfo.phone || ""} ${companyInfo.email ? "| " + companyInfo.email : ""}</p>
  </div>
  <div class="invoice-title">INVOICE</div>
</div>

<div class="info-block">
  <div class="info-section">
    <h3>Bill To</h3>
    <p><strong>${recipient.name || ""}</strong></p>
    <p>${recipient.address || ""}</p>
    <p>${recipient.email || ""}</p>
  </div>
  <div class="info-section" style="text-align: right;">
    <table class="meta-table">
      <tr><td class="meta-label">Invoice #:</td><td><strong>${data.invoiceNumber || ""}</strong></td></tr>
      <tr><td class="meta-label">Date:</td><td>${data.date || ""}</td></tr>
      <tr><td class="meta-label">Due Date:</td><td>${data.dueDate || ""}</td></tr>
    </table>
  </div>
</div>

<table class="items">
  <thead>
    <tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr>
  </thead>
  <tbody>${itemRows}</tbody>
</table>

<table class="totals">
  <tr><td class="meta-label">Subtotal:</td><td style="text-align: right;">${currency}${formatNum(subtotal)}</td></tr>
  ${tax ? `<tr><td class="meta-label">Tax:</td><td style="text-align: right;">${currency}${formatNum(tax)}</td></tr>` : ""}
  ${discount ? `<tr><td class="meta-label">Discount:</td><td style="text-align: right;">-${currency}${formatNum(discount)}</td></tr>` : ""}
  <tr class="total-row"><td>Total:</td><td style="text-align: right;">${currency}${formatNum(total)}</td></tr>
</table>

${
  data.paymentDetails
    ? `<div class="payment-section">
  <h3>Payment Details</h3>
  ${data.paymentDetails.bank ? `<p><strong>Bank:</strong> ${data.paymentDetails.bank}</p>` : ""}
  ${data.paymentDetails.iban ? `<p><strong>IBAN:</strong> ${data.paymentDetails.iban}</p>` : ""}
  ${data.paymentDetails.swift ? `<p><strong>SWIFT:</strong> ${data.paymentDetails.swift}</p>` : ""}
  ${data.paymentDetails.accountName ? `<p><strong>Account:</strong> ${data.paymentDetails.accountName}</p>` : ""}
</div>`
    : ""
}

${data.notes ? `<div class="notes"><p>${data.notes}</p></div>` : ""}

</body></html>`;
}

function buildGenericHtml(data, primaryColor, fontFamily) {
  const sections = (data.sections || [])
    .map(
      (s) => `
    <h${s.level || 1} style="color: ${primaryColor}; margin-top: 30px;">${s.heading}</h${s.level || 1}>
    ${s.content ? s.content.split("\n\n").map((p) => `<p>${p}</p>`).join("") : ""}
    ${s.bullets ? "<ul>" + s.bullets.map((b) => `<li>${b}</li>`).join("") + "</ul>" : ""}
  `
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body { font-family: ${fontFamily}; color: #1F2937; line-height: 1.6; font-size: 14px; }
  h1 { font-size: 28px; color: ${primaryColor}; }
  h2 { font-size: 20px; color: ${primaryColor}; }
  h3 { font-size: 16px; color: ${primaryColor}; }
  p { margin: 8px 0; }
  ul { padding-left: 20px; }
  li { margin: 4px 0; }
</style></head><body>
  <h1 style="text-align: center; margin-bottom: 40px;">${data.title || ""}</h1>
  ${data.author ? `<p style="text-align: center; color: #6B7280;">${data.author}${data.date ? " | " + data.date : ""}</p>` : ""}
  ${sections}
</body></html>`;
}

async function generateWithPdfKit(outputPath, data, template) {
  const PDFDocument = require("pdfkit");
  const doc = new PDFDocument({ size: "A4", margin: 50 });
  const stream = fs.createWriteStream(outputPath);
  doc.pipe(stream);

  const primaryColor = template?.styling?.primaryColor || "#2563EB";

  // Title
  if (data.title) {
    doc.fontSize(24).fillColor(primaryColor).text(data.title, { align: "center" });
    doc.moveDown();
  }

  // Meta
  if (data.date) doc.fontSize(11).fillColor("#6B7280").text(`Date: ${data.date}`, { align: "center" });
  if (data.author) doc.fontSize(11).fillColor("#6B7280").text(`Author: ${data.author}`, { align: "center" });
  doc.moveDown(2);

  // Sections
  if (data.sections) {
    for (const section of data.sections) {
      doc
        .fontSize(section.level === 1 ? 16 : 13)
        .fillColor(primaryColor)
        .text(section.heading);
      doc.moveDown(0.5);
      if (section.content) {
        doc.fontSize(11).fillColor("#1F2937").text(section.content);
        doc.moveDown();
      }
    }
  }

  doc.end();
  await new Promise((resolve) => stream.on("finish", resolve));
}

function formatNum(n) {
  if (n === undefined || n === null) return "0.00";
  return Number(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

main();
