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
  const margins = styling.margins || { top: "20mm", bottom: "20mm", left: "18mm", right: "18mm" };

  let html = "";

  if (type === "invoice") {
    html = buildInvoiceHtml(data, styling, template);
  } else {
    html = buildGenericHtml(data, styling);
  }

  const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle0" });
  await page.pdf({
    path: outputPath,
    format: styling.pageSize || "A4",
    margin: margins,
    printBackground: true,
    displayHeaderFooter: false,
  });
  await browser.close();
}

function buildInvoiceHtml(data, styling, template) {
  const primary = styling.primaryColor || "#1E3A5F";
  const accent = styling.accentColor || "#2563EB";
  const textColor = styling.textColor || "#1E293B";
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const highlightBg = styling.highlightBg || "#EFF6FF";
  const fontBody = styling.fontFamily || "'Helvetica Neue', Helvetica, Arial, sans-serif";
  const fontHeading = styling.fontHeading || "Georgia, 'Times New Roman', serif";
  const currency = template?.currencySymbol || data.currencySymbol || "$";

  const items = data.items || [];
  const subtotal = data.subtotal ?? items.reduce((sum, i) => sum + (i.total || i.quantity * i.unitPrice || 0), 0);
  const tax = data.tax ?? 0;
  const discount = data.discount ?? 0;
  const total = data.total ?? subtotal + tax - discount;

  const companyInfo = data.companyInfo || {};
  const recipient = data.recipientInfo || {};

  const itemRows = items
    .map(
      (item, idx) => `
    <tr style="background: ${idx % 2 === 0 ? "#FFFFFF" : bgLight};">
      <td style="padding: 14px 16px; border-bottom: 1px solid ${border}; color: ${textColor};">${esc(item.description)}</td>
      <td style="padding: 14px 16px; text-align: center; border-bottom: 1px solid ${border}; color: ${muted};">${esc(item.quantity)}</td>
      <td style="padding: 14px 16px; text-align: right; border-bottom: 1px solid ${border}; color: ${muted};">${currency}${formatNum(item.unitPrice)}</td>
      <td style="padding: 14px 16px; text-align: right; border-bottom: 1px solid ${border}; color: ${textColor}; font-weight: 600;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 13px; line-height: 1.5; }

  .top-bar { background: ${primary}; height: 6px; }

  .header { display: flex; justify-content: space-between; align-items: flex-start; padding: 32px 0 24px; border-bottom: 1px solid ${border}; margin-bottom: 32px; }
  .company-name { font-family: ${fontHeading}; font-size: 22px; font-weight: bold; color: ${primary}; margin-bottom: 6px; }
  .company-details { color: ${muted}; font-size: 12px; line-height: 1.7; }
  .invoice-badge { text-align: right; }
  .invoice-badge h1 { font-family: ${fontHeading}; font-size: 32px; color: ${primary}; letter-spacing: 2px; margin-bottom: 8px; }
  .invoice-badge .meta { color: ${muted}; font-size: 12px; line-height: 1.8; }
  .invoice-badge .meta strong { color: ${textColor}; }

  .info-row { display: flex; justify-content: space-between; margin-bottom: 32px; gap: 40px; }
  .info-card { flex: 1; padding: 20px 24px; background: ${bgLight}; border-radius: 8px; border-left: 4px solid ${accent}; }
  .info-card .label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: ${muted}; font-weight: 700; margin-bottom: 8px; }
  .info-card .name { font-size: 15px; font-weight: 700; color: ${textColor}; margin-bottom: 4px; }
  .info-card .detail { color: ${muted}; font-size: 12px; line-height: 1.6; }

  table.items { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
  table.items thead tr { background: ${primary}; }
  table.items th { color: #FFFFFF; padding: 12px 16px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
  table.items th:nth-child(2) { text-align: center; }
  table.items th:nth-child(3), table.items th:nth-child(4) { text-align: right; }

  .totals-wrapper { display: flex; justify-content: flex-end; margin-bottom: 32px; }
  .totals-box { width: 320px; }
  .totals-row { display: flex; justify-content: space-between; padding: 8px 16px; font-size: 13px; }
  .totals-row .label { color: ${muted}; }
  .totals-row .value { color: ${textColor}; }
  .totals-row.grand { background: ${primary}; color: #FFFFFF; border-radius: 6px; padding: 14px 16px; margin-top: 8px; font-size: 18px; font-weight: 700; }
  .totals-row.grand .label, .totals-row.grand .value { color: #FFFFFF; }

  .payment-card { padding: 24px; background: ${highlightBg}; border-radius: 8px; border: 1px solid ${border}; margin-bottom: 24px; }
  .payment-card h3 { font-family: ${fontHeading}; font-size: 14px; color: ${primary}; margin-bottom: 12px; }
  .payment-card .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .payment-card .field-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: ${muted}; font-weight: 700; }
  .payment-card .field-value { font-size: 13px; color: ${textColor}; font-weight: 500; }

  .notes { color: ${muted}; font-size: 11px; line-height: 1.6; padding-top: 16px; border-top: 1px solid ${border}; }

  .bottom-bar { background: ${primary}; height: 4px; margin-top: 32px; }
</style></head><body>

<div class="top-bar"></div>

<div class="header">
  <div>
    <div class="company-name">${esc(companyInfo.name) || "Company Name"}</div>
    <div class="company-details">
      ${companyInfo.address ? esc(companyInfo.address) + "<br>" : ""}
      ${esc(companyInfo.phone)}${companyInfo.email ? " &middot; " + esc(companyInfo.email) : ""}
    </div>
  </div>
  <div class="invoice-badge">
    <h1>INVOICE</h1>
    <div class="meta">
      <strong>${esc(data.invoiceNumber)}</strong><br>
      Issued: ${esc(data.date)}<br>
      Due: ${esc(data.dueDate)}
    </div>
  </div>
</div>

<div class="info-row">
  <div class="info-card">
    <div class="label">Bill To</div>
    <div class="name">${esc(recipient.name)}</div>
    <div class="detail">
      ${esc(recipient.address)}${recipient.email ? "<br>" + esc(recipient.email) : ""}
    </div>
  </div>
  <div class="info-card">
    <div class="label">Invoice Summary</div>
    <div class="name">${currency}${formatNum(total)}</div>
    <div class="detail">
      ${items.length} item${items.length !== 1 ? "s" : ""} &middot; Due ${esc(data.dueDate) || "on receipt"}
    </div>
  </div>
</div>

<table class="items">
  <thead>
    <tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr>
  </thead>
  <tbody>${itemRows}</tbody>
</table>

<div class="totals-wrapper">
  <div class="totals-box">
    <div class="totals-row"><span class="label">Subtotal</span><span class="value">${currency}${formatNum(subtotal)}</span></div>
    ${tax ? `<div class="totals-row"><span class="label">Tax</span><span class="value">${currency}${formatNum(tax)}</span></div>` : ""}
    ${discount ? `<div class="totals-row"><span class="label">Discount</span><span class="value">-${currency}${formatNum(discount)}</span></div>` : ""}
    <div class="totals-row grand"><span class="label">Total Due</span><span class="value">${currency}${formatNum(total)}</span></div>
  </div>
</div>

${
  data.paymentDetails
    ? `<div class="payment-card">
  <h3>Payment Details</h3>
  <div class="grid">
    ${data.paymentDetails.bank ? `<div><div class="field-label">Bank</div><div class="field-value">${esc(data.paymentDetails.bank)}</div></div>` : ""}
    ${data.paymentDetails.accountName ? `<div><div class="field-label">Account</div><div class="field-value">${esc(data.paymentDetails.accountName)}</div></div>` : ""}
    ${data.paymentDetails.iban ? `<div><div class="field-label">IBAN</div><div class="field-value">${esc(data.paymentDetails.iban)}</div></div>` : ""}
    ${data.paymentDetails.swift ? `<div><div class="field-label">SWIFT</div><div class="field-value">${esc(data.paymentDetails.swift)}</div></div>` : ""}
  </div>
</div>`
    : ""
}

${data.notes ? `<div class="notes">${esc(data.notes)}</div>` : ""}

<div class="bottom-bar"></div>

</body></html>`;
}

function buildGenericHtml(data, styling) {
  const primary = styling.primaryColor || "#1E3A5F";
  const accent = styling.accentColor || "#2563EB";
  const textColor = styling.textColor || "#1E293B";
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const fontBody = styling.fontFamily || "'Helvetica Neue', Helvetica, Arial, sans-serif";
  const fontHeading = styling.fontHeading || "Georgia, 'Times New Roman', serif";

  const sections = (data.sections || [])
    .map(
      (s, idx) => `
    <div style="margin-bottom: 32px; ${idx % 2 === 1 ? `background: ${bgLight}; padding: 24px; border-radius: 8px;` : ""}">
      <h${s.level || 1} style="font-family: ${fontHeading}; color: ${primary}; margin: 0 0 4px; font-size: ${s.level === 1 ? "20px" : s.level === 2 ? "16px" : "14px"};">${s.heading}</h${s.level || 1}>
      <div style="width: 40px; height: 3px; background: ${accent}; margin-bottom: 16px; border-radius: 2px;"></div>
      ${s.content ? s.content.split("\n\n").map((p) => `<p style="margin: 0 0 12px; line-height: 1.7; color: ${textColor};">${esc(p)}</p>`).join("") : ""}
      ${s.bullets ? `<ul style="padding-left: 20px; margin: 8px 0;">${s.bullets.map((b) => `<li style="margin: 6px 0; color: ${textColor}; line-height: 1.6;">${esc(b)}</li>`).join("")}</ul>` : ""}
    </div>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; line-height: 1.6; font-size: 13px; }
</style></head><body>

<div style="background: ${primary}; padding: 48px 32px; margin-bottom: 32px; border-radius: 0 0 12px 12px;">
  <h1 style="font-family: ${fontHeading}; color: #FFFFFF; font-size: 32px; margin-bottom: 8px;">${esc(data.title)}</h1>
  ${data.subtitle ? `<p style="color: rgba(255,255,255,0.7); font-size: 16px; margin-bottom: 4px;">${esc(data.subtitle)}</p>` : ""}
  ${data.author || data.date ? `<p style="color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 16px;">${esc(data.author)}${data.date ? " &middot; " + esc(data.date) : ""}</p>` : ""}
</div>

${sections}

</body></html>`;
}

async function generateWithPdfKit(outputPath, data, template) {
  const PDFDocument = require("pdfkit");
  const doc = new PDFDocument({ size: "A4", margin: 50 });
  const stream = fs.createWriteStream(outputPath);
  doc.pipe(stream);

  const primaryColor = template?.styling?.primaryColor || "#1E3A5F";
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
      doc.moveTo(doc.x, doc.y).lineTo(doc.x + 40, doc.y).strokeColor("#2563EB").lineWidth(2).stroke();
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

function esc(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function formatNum(n) {
  if (n === undefined || n === null) return "0.00";
  return Number(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

main();
