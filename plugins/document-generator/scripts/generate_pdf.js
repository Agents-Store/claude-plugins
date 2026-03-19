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
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";

  let html = "";
  if (type === "invoice") {
    html = buildInvoiceHtml(data, styling, template);
  } else if (type === "contract") {
    html = buildContractHtml(data, styling, template);
  } else if (type === "act") {
    html = buildActHtml(data, styling, template);
  } else {
    html = buildGenericHtml(data, styling);
  }

  // Company name for page header — extracted from data regardless of document type
  const companyName = esc(
    data.companyInfo?.name || data.company || data.contractor?.name || ""
  );

  // Custom header/footer: shows company name + page numbers WITHOUT the file:// URL
  const headerTpl = `<div style="width:100%;padding:5px 18mm 0;font-family:Inter,Arial,sans-serif;font-size:8px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid ${border};"><span>${companyName}</span><span>&nbsp;</span></div>`;
  const footerTpl = `<div style="width:100%;padding:0 18mm 5px;font-family:Inter,Arial,sans-serif;font-size:8px;color:${muted};display:flex;justify-content:space-between;align-items:center;border-top:1px solid ${border};"><span>&nbsp;</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`;

  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "networkidle0" });
  await page.pdf({
    path: outputPath,
    format: styling.pageSize || "A4",
    margin: {
      top: styling.margins?.top || "28mm",
      bottom: styling.margins?.bottom || "22mm",
      left: styling.margins?.left || "18mm",
      right: styling.margins?.right || "18mm",
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: headerTpl,
    footerTemplate: footerTpl,
  });
  await browser.close();
}

// Font styles — Inter + PT Serif embedded as base64 (Cyrillic+Latin).
// Fonts are loaded from scripts/fonts.js which is a plain JS file distributed with the plugin.
// This makes fonts work fully offline for all users who install via marketplace.
function fontLinks() {
  try {
    const fonts = require("./fonts");
    const face = (family, weight, latinB64, cyrillicB64) => {
      let css = "";
      if (cyrillicB64) {
        css += `@font-face{font-family:'${family}';font-weight:${weight};font-style:normal;unicode-range:U+0400-04FF,U+0500-052F,U+2DE0-2DFF,U+A640-A69F;src:url('data:font/woff2;base64,${cyrillicB64}') format('woff2');}`;
      }
      css += `@font-face{font-family:'${family}';font-weight:${weight};font-style:normal;src:url('data:font/woff2;base64,${latinB64}') format('woff2');}`;
      return css;
    };
    return `<style>
${face("Inter", 400, fonts.interLatin400, fonts.interCyrillic400)}
${face("Inter", 700, fonts.interLatin700, fonts.interCyrillic700)}
${face("PT Serif", 400, fonts.ptSerifLatin400, fonts.ptSerifCyrillic400)}
${face("PT Serif", 700, fonts.ptSerifLatin700, fonts.ptSerifCyrillic700)}
</style>`;
  } catch (_) {
    // Fallback: Google Fonts CDN (if fonts.js is missing for any reason)
    return `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=PT+Serif:wght@400;700&display=swap" rel="stylesheet">`;
  }
}

// Logo HTML helper — accepts base64 data URI or URL
function logoHtml(data) {
  const src = data.logoBase64
    ? `data:image/png;base64,${data.logoBase64}`
    : data.logoUrl || "";
  if (!src) return "";
  return `<img src="${src}" alt="logo" style="max-height:56px;max-width:160px;object-fit:contain;display:block;margin-bottom:6px;">`;
}

// ─── Invoice ──────────────────────────────────────────────────────────────────

function buildInvoiceHtml(data, styling, template) {
  const primary = styling.primaryColor || "#1E3A5F";
  const accent = styling.accentColor || "#2563EB";
  const textColor = styling.textColor || "#1E293B";
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const highlightBg = styling.highlightBg || "#EFF6FF";
  const fontBody = `'Inter', Arial, sans-serif`;
  const fontHeading = `'PT Serif', Georgia, serif`;
  const currency = template?.currencySymbol || data.currencySymbol || "$";

  const items = data.items || [];
  const subtotal = data.subtotal ?? items.reduce((sum, i) => sum + (i.total || i.quantity * i.unitPrice || 0), 0);
  const tax = data.tax ?? 0;
  const discount = data.discount ?? 0;
  const total = data.total ?? subtotal + tax - discount;

  const companyInfo = data.companyInfo || {};
  const recipient = data.recipientInfo || {};
  const logo = logoHtml(data);

  const itemRows = items
    .map(
      (item, idx) => `
    <tr style="background: ${idx % 2 === 0 ? "#FFFFFF" : bgLight};">
      <td style="padding: 13px 16px; border-bottom: 1px solid ${border}; color: ${textColor};">${esc(item.description)}</td>
      <td style="padding: 13px 16px; text-align: center; border-bottom: 1px solid ${border}; color: ${muted};">${esc(item.quantity)}</td>
      <td style="padding: 13px 16px; text-align: right; border-bottom: 1px solid ${border}; color: ${muted};">${currency}${formatNum(item.unitPrice)}</td>
      <td style="padding: 13px 16px; text-align: right; border-bottom: 1px solid ${border}; color: ${textColor}; font-weight: 600;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 13px; line-height: 1.5; }

  .top-bar { background: ${primary}; height: 6px; }

  .header { display: flex; justify-content: space-between; align-items: flex-start; padding: 28px 0 22px; border-bottom: 1px solid ${border}; margin-bottom: 28px; }
  .company-name { font-family: ${fontHeading}; font-size: 21px; font-weight: bold; color: ${primary}; margin-bottom: 6px; }
  .company-details { color: ${muted}; font-size: 12px; line-height: 1.7; }
  .invoice-badge { text-align: right; }
  .invoice-badge h1 { font-family: ${fontHeading}; font-size: 32px; color: ${primary}; letter-spacing: 2px; margin-bottom: 8px; }
  .invoice-badge .meta { color: ${muted}; font-size: 12px; line-height: 1.8; }
  .invoice-badge .meta strong { color: ${textColor}; }

  .info-row { display: flex; justify-content: space-between; margin-bottom: 28px; gap: 36px; }
  .info-card { flex: 1; padding: 18px 22px; background: ${bgLight}; border-radius: 6px; border-left: 4px solid ${accent}; }
  .info-card .label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: ${muted}; font-weight: 700; margin-bottom: 6px; }
  .info-card .name { font-size: 14px; font-weight: 700; color: ${textColor}; margin-bottom: 4px; }
  .info-card .detail { color: ${muted}; font-size: 12px; line-height: 1.6; }

  table.items { width: 100%; border-collapse: collapse; margin-bottom: 22px; }
  table.items thead tr { background: ${primary}; }
  table.items th { color: #FFFFFF; padding: 11px 16px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
  table.items th:nth-child(2) { text-align: center; }
  table.items th:nth-child(3), table.items th:nth-child(4) { text-align: right; }

  .totals-wrapper { display: flex; justify-content: flex-end; margin-bottom: 28px; }
  .totals-box { width: 300px; }
  .totals-row { display: flex; justify-content: space-between; padding: 7px 14px; font-size: 13px; }
  .totals-row .label { color: ${muted}; }
  .totals-row .value { color: ${textColor}; }
  .totals-row.grand { background: ${primary}; color: #FFFFFF; border-radius: 5px; padding: 13px 14px; margin-top: 6px; font-size: 17px; font-weight: 700; }
  .totals-row.grand .label, .totals-row.grand .value { color: #FFFFFF; }

  .payment-card { padding: 22px; background: ${highlightBg}; border-radius: 6px; border: 1px solid ${border}; margin-bottom: 22px; }
  .payment-card h3 { font-family: ${fontHeading}; font-size: 14px; color: ${primary}; margin-bottom: 10px; }
  .payment-card .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .payment-card .field-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: ${muted}; font-weight: 700; }
  .payment-card .field-value { font-size: 13px; color: ${textColor}; font-weight: 500; }

  .notes { color: ${muted}; font-size: 11px; line-height: 1.6; padding-top: 14px; border-top: 1px solid ${border}; }
  .bottom-bar { background: ${primary}; height: 4px; margin-top: 28px; }
</style></head><body>

<div class="top-bar"></div>

<div class="header">
  <div>
    ${logo}
    <div class="company-name">${esc(companyInfo.name) || "Company Name"}</div>
    <div class="company-details">
      ${companyInfo.address ? esc(companyInfo.address) + "<br>" : ""}
      ${companyInfo.phone ? esc(companyInfo.phone) : ""}${companyInfo.email ? " &middot; " + esc(companyInfo.email) : ""}
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

// ─── Contract ─────────────────────────────────────────────────────────────────

function buildContractHtml(data, styling) {
  const primary = styling.primaryColor || "#1E293B";
  const accent = styling.accentColor || "#1E3A5F";
  const textColor = styling.textColor || "#1E293B";
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const fontBody = `'PT Serif', Georgia, serif`;
  const fontHeading = `'PT Serif', Georgia, serif`;
  const fontMeta = `'Inter', Arial, sans-serif`;

  const companyInfo = data.companyInfo || {};
  const party1 = data.party1 || {};
  const party2 = data.party2 || {};
  const logo = logoHtml(data);

  const clausesHtml = (data.clauses || [])
    .map((clause) => {
      const paras = (clause.paragraphs || [clause.content]).filter(Boolean);
      return `
    <div style="margin-bottom: 22px;">
      <div style="font-family: ${fontHeading}; font-size: 13px; font-weight: bold; color: ${primary}; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 2px solid ${accent}; display: inline-block;">
        ${esc(clause.number ? clause.number + ". " : "")}${esc(clause.title)}
      </div>
      ${paras.map((p, i) => `<p style="margin: 0 0 8px; font-size: 12px; line-height: 1.75; color: ${textColor}; ${clause.numbered !== false && paras.length > 1 ? "text-indent: 0; padding-left: 20px;" : ""}">${clause.number && paras.length > 1 ? `<span style="font-family:${fontMeta};font-size:11px;color:${muted};margin-right:6px;">${clause.number}.${i + 1}</span>` : ""}${esc(p)}</p>`).join("")}
    </div>`;
    })
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 12px; line-height: 1.65; }
  .top-bar { background: ${primary}; height: 6px; }
  .contract-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 22px 0 18px; border-bottom: 2px solid ${primary}; margin-bottom: 22px; }
  .company-block { max-width: 55%; }
  .company-name { font-family: ${fontHeading}; font-size: 17px; font-weight: bold; color: ${primary}; margin-bottom: 4px; }
  .company-meta { font-family: ${fontMeta}; color: ${muted}; font-size: 11px; line-height: 1.6; }
  .contract-id-block { text-align: right; }
  .contract-title { font-family: ${fontHeading}; font-size: 18px; font-weight: bold; color: ${primary}; margin-bottom: 6px; }
  .contract-number { font-family: ${fontMeta}; font-size: 12px; color: ${muted}; }
  .date-city { font-family: ${fontMeta}; text-align: center; color: ${muted}; font-size: 11px; margin-bottom: 22px; padding: 7px 0; border-bottom: 1px solid ${border}; }
  .section-label { font-family: ${fontMeta}; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: ${muted}; font-weight: 700; margin-bottom: 10px; }
  .parties-grid { display: flex; gap: 18px; margin-bottom: 26px; }
  .party-card { flex: 1; padding: 15px 18px; background: ${bgLight}; border-left: 4px solid ${accent}; border-radius: 4px; }
  .party-role { font-family: ${fontMeta}; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: ${muted}; font-weight: 700; margin-bottom: 5px; }
  .party-name { font-size: 13px; font-weight: bold; color: ${textColor}; margin-bottom: 3px; }
  .party-detail { font-family: ${fontMeta}; font-size: 11px; color: ${muted}; line-height: 1.55; }
  .clauses-section { margin-bottom: 32px; }
  .sig-block { margin-top: 36px; padding-top: 20px; border-top: 2px solid ${primary}; }
  .sig-grid { display: flex; gap: 40px; margin-top: 16px; }
  .sig-col { flex: 1; }
  .sig-party { font-weight: bold; font-size: 13px; color: ${textColor}; margin-bottom: 3px; }
  .sig-detail { font-family: ${fontMeta}; font-size: 11px; color: ${muted}; line-height: 1.5; margin-bottom: 2px; }
  .sig-line { border-bottom: 1px solid ${textColor}; margin-top: 30px; }
  .sig-lbl { font-family: ${fontMeta}; font-size: 10px; color: ${muted}; margin-top: 3px; }
  .seal-line { border-bottom: 1px solid ${border}; margin-top: 18px; }
  .bottom-bar { background: ${primary}; height: 4px; margin-top: 28px; }
</style></head><body>

<div class="top-bar"></div>

<div class="contract-header">
  <div class="company-block">
    ${logo}
    <div class="company-name">${esc(companyInfo.name)}</div>
    <div class="company-meta">
      ${companyInfo.address ? esc(companyInfo.address) + "<br>" : ""}
      ${companyInfo.reg ? "Reg No: " + esc(companyInfo.reg) + "<br>" : ""}
      ${companyInfo.email ? esc(companyInfo.email) : ""}
    </div>
  </div>
  <div class="contract-id-block">
    <div class="contract-title">${esc(data.title || "Service Agreement")}</div>
    ${data.number ? `<div class="contract-number">No. ${esc(data.number)}</div>` : ""}
  </div>
</div>

<div class="date-city">
  ${data.city ? esc(data.city) + " &nbsp;&middot;&nbsp; " : ""}${esc(data.date)}
  ${data.governingLaw ? " &nbsp;&middot;&nbsp; Governing Law: " + esc(data.governingLaw) : ""}
</div>

<div class="section-label">Parties to the Agreement</div>
<div class="parties-grid">
  <div class="party-card">
    <div class="party-role">Party 1 / Contractor</div>
    <div class="party-name">${esc(party1.name)}</div>
    <div class="party-detail">
      ${party1.address ? esc(party1.address) + "<br>" : ""}
      ${party1.reg ? "Reg No: " + esc(party1.reg) + "<br>" : ""}
      ${party1.representative ? "Rep: " + esc(party1.representative) : ""}${party1.title ? ", " + esc(party1.title) : ""}
    </div>
  </div>
  <div class="party-card">
    <div class="party-role">Party 2 / Customer</div>
    <div class="party-name">${esc(party2.name)}</div>
    <div class="party-detail">
      ${party2.address ? esc(party2.address) + "<br>" : ""}
      ${party2.reg ? "Reg No: " + esc(party2.reg) + "<br>" : ""}
      ${party2.representative ? "Rep: " + esc(party2.representative) : ""}${party2.title ? ", " + esc(party2.title) : ""}
    </div>
  </div>
</div>

<div class="clauses-section">
${clausesHtml}
</div>

<div class="sig-block">
  <div class="section-label">Signatures</div>
  <div class="sig-grid">
    <div class="sig-col">
      <div class="sig-party">${esc(party1.name)}</div>
      ${party1.representative ? `<div class="sig-detail">${esc(party1.representative)}${party1.title ? ", " + esc(party1.title) : ""}</div>` : ""}
      ${party1.reg ? `<div class="sig-detail">Reg: ${esc(party1.reg)}</div>` : ""}
      <div class="sig-line"></div>
      <div class="sig-lbl">Signature / Date</div>
      <div class="seal-line"></div>
      <div class="sig-lbl">Seal / Stamp</div>
    </div>
    <div class="sig-col">
      <div class="sig-party">${esc(party2.name)}</div>
      ${party2.representative ? `<div class="sig-detail">${esc(party2.representative)}${party2.title ? ", " + esc(party2.title) : ""}</div>` : ""}
      ${party2.reg ? `<div class="sig-detail">Reg: ${esc(party2.reg)}</div>` : ""}
      <div class="sig-line"></div>
      <div class="sig-lbl">Signature / Date</div>
      <div class="seal-line"></div>
      <div class="sig-lbl">Seal / Stamp</div>
    </div>
  </div>
</div>

<div class="bottom-bar"></div>

</body></html>`;
}

// ─── Act of Completed Works (Акт виконаних робіт) ────────────────────────────

function buildActHtml(data, styling, template) {
  const primary = styling.primaryColor || "#1E293B";
  const accent = styling.accentColor || "#1E3A5F";
  const textColor = styling.textColor || "#1E293B";
  const muted = styling.mutedColor || "#64748B";
  const border = styling.borderColor || "#E2E8F0";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const fontBody = `'PT Serif', Georgia, serif`;
  const fontMeta = `'Inter', Arial, sans-serif`;
  const currency = template?.currencySymbol || data.currencySymbol || "₴";

  const contractor = data.contractor || {};
  const customer = data.customer || {};
  const services = data.services || [];
  const total = data.totalAmount ?? services.reduce((s, r) => s + (r.total || r.quantity * r.unitPrice || 0), 0);
  const vatRate = data.vatRate ?? 0;
  const vatAmount = vatRate ? total * (vatRate / 100) : 0;

  // Intro paragraph
  const contractorName = party1Label(contractor);
  const customerName = party1Label(customer);
  const contractRef = data.contractRef ? ` відповідно до ${esc(data.contractRef)},` : "";
  const introText = `Ми, що нижче підписалися, ${contractorName} (надалі — <strong>Виконавець</strong>) та ${customerName} (надалі — <strong>Замовник</strong>), склали цей акт про те, що${contractRef} Виконавець виконав, а Замовник прийняв наступні роботи (послуги):`;

  const serviceRows = services
    .map(
      (s, idx) => `
    <tr style="background:${idx % 2 === 0 ? "#fff" : bgLight}">
      <td style="padding:10px 12px;border-bottom:1px solid ${border};text-align:center;font-family:${fontMeta};font-size:11px;">${idx + 1}</td>
      <td style="padding:10px 12px;border-bottom:1px solid ${border};">${esc(s.description)}</td>
      <td style="padding:10px 12px;border-bottom:1px solid ${border};text-align:center;font-family:${fontMeta};font-size:11px;">${esc(s.unit || "—")}</td>
      <td style="padding:10px 12px;border-bottom:1px solid ${border};text-align:right;font-family:${fontMeta};font-size:11px;">${esc(s.quantity)}</td>
      <td style="padding:10px 12px;border-bottom:1px solid ${border};text-align:right;font-family:${fontMeta};font-size:11px;">${formatNum(s.unitPrice)}</td>
      <td style="padding:10px 12px;border-bottom:1px solid ${border};text-align:right;font-family:${fontMeta};font-size:11px;font-weight:600;">${formatNum(s.total || s.quantity * s.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 12px; line-height: 1.7; }
  .act-header { text-align: center; margin-bottom: 26px; padding-bottom: 20px; border-bottom: 2px solid ${primary}; }
  .act-title { font-family: ${fontBody}; font-size: 20px; font-weight: bold; color: ${primary}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .act-number { font-family: ${fontMeta}; font-size: 13px; color: ${textColor}; margin-bottom: 4px; }
  .act-datecity { font-family: ${fontMeta}; font-size: 12px; color: ${muted}; }
  .intro { margin-bottom: 20px; font-size: 12px; line-height: 1.8; }
  table.services { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
  table.services th { background: ${primary}; color: #fff; padding: 10px 12px; text-align: left; font-family: ${fontMeta}; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
  table.services th:nth-child(3), table.services th:nth-child(4), table.services th:nth-child(5), table.services th:nth-child(6) { text-align: right; }
  .totals { margin-bottom: 24px; }
  .total-row { font-family: ${fontMeta}; font-size: 12px; display: flex; justify-content: flex-end; gap: 32px; padding: 6px 0; color: ${muted}; }
  .total-row.grand { background: ${primary}; color: #fff; padding: 10px 16px; border-radius: 4px; margin-top: 6px; font-size: 14px; font-weight: 700; }
  .total-row.grand span { color: #fff; }
  .confirm-box { margin-bottom: 24px; padding: 14px 18px; background: ${bgLight}; border-left: 4px solid ${accent}; font-size: 12px; line-height: 1.7; }
  .section-label { font-family: ${fontMeta}; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: ${muted}; font-weight: 700; margin-bottom: 10px; }
  .sig-grid { display: flex; gap: 40px; margin-top: 12px; }
  .sig-col { flex: 1; }
  .sig-party { font-weight: bold; font-size: 13px; margin-bottom: 3px; }
  .sig-detail { font-family: ${fontMeta}; font-size: 11px; color: ${muted}; line-height: 1.5; margin-bottom: 2px; }
  .sig-line { border-bottom: 1px solid ${textColor}; margin-top: 30px; }
  .sig-lbl { font-family: ${fontMeta}; font-size: 10px; color: ${muted}; margin-top: 3px; }
  .seal-line { border-bottom: 1px solid ${border}; margin-top: 16px; }
</style></head><body>

<div class="act-header">
  <div class="act-title">Акт виконаних робіт</div>
  ${data.actNumber ? `<div class="act-number">${esc(data.actNumber)}</div>` : ""}
  <div class="act-datecity">
    ${data.city ? "м. " + esc(data.city) + " &nbsp;&middot;&nbsp; " : ""}${esc(data.date)}
  </div>
</div>

<div class="intro">${introText}</div>

<table class="services">
  <thead>
    <tr>
      <th style="text-align:center;width:40px;">№</th>
      <th>Найменування послуги / роботи</th>
      <th style="text-align:right;">Од.</th>
      <th style="text-align:right;">Кількість</th>
      <th style="text-align:right;">Ціна</th>
      <th style="text-align:right;">Сума</th>
    </tr>
  </thead>
  <tbody>${serviceRows}</tbody>
</table>

<div class="totals">
  ${vatRate ? `<div class="total-row"><span>ПДВ (${vatRate}%)</span><span>${currency}${formatNum(vatAmount)}</span></div>` : ""}
  <div class="total-row grand"><span>Всього до сплати</span><span>${currency}${formatNum(total + vatAmount)}</span></div>
</div>

<div class="confirm-box">
  Вищезазначені роботи (послуги) виконані в повному обсязі, у встановлені строки та з належною якістю.
  Замовник до Виконавця претензій щодо якості та обсягу виконаних робіт не має.
  ${data.notes ? "<br>" + esc(data.notes) : ""}
</div>

<div class="section-label">Підписи сторін</div>
<div class="sig-grid">
  <div class="sig-col">
    <div class="sig-party">ВИКОНАВЕЦЬ</div>
    <div class="sig-detail">${esc(contractor.name)}</div>
    ${contractor.representative ? `<div class="sig-detail">${esc(contractor.representative)}${contractor.title ? ", " + esc(contractor.title) : ""}</div>` : ""}
    ${contractor.reg ? `<div class="sig-detail">ЄДРПОУ/ФОП: ${esc(contractor.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">Підпис / Дата</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">Печатка</div>
  </div>
  <div class="sig-col">
    <div class="sig-party">ЗАМОВНИК</div>
    <div class="sig-detail">${esc(customer.name)}</div>
    ${customer.representative ? `<div class="sig-detail">${esc(customer.representative)}${customer.title ? ", " + esc(customer.title) : ""}</div>` : ""}
    ${customer.reg ? `<div class="sig-detail">ЄДРПОУ/ФОП: ${esc(customer.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">Підпис / Дата</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">Печатка</div>
  </div>
</div>

</body></html>`;
}

// ─── Generic (report, proposal, etc.) ────────────────────────────────────────

function buildGenericHtml(data, styling) {
  const primary = styling.primaryColor || "#1E3A5F";
  const accent = styling.accentColor || "#2563EB";
  const textColor = styling.textColor || "#1E293B";
  const bgLight = styling.backgroundColor || "#F8FAFC";
  const fontBody = `'Inter', Arial, sans-serif`;
  const fontHeading = `'PT Serif', Georgia, serif`;

  const sections = (data.sections || [])
    .map(
      (s, idx) => `
    <div style="margin-bottom: 32px; ${idx % 2 === 1 ? `background: ${bgLight}; padding: 22px; border-radius: 6px;` : ""}">
      <h${s.level || 1} style="font-family: ${fontHeading}; color: ${primary}; margin: 0 0 4px; font-size: ${s.level === 1 ? "20px" : s.level === 2 ? "16px" : "14px"};">${esc(s.heading)}</h${s.level || 1}>
      <div style="width: 38px; height: 3px; background: ${accent}; margin-bottom: 14px; border-radius: 2px;"></div>
      ${s.content ? s.content.split("\n\n").map((p) => `<p style="margin: 0 0 11px; line-height: 1.75; color: ${textColor}; font-size: 13px;">${esc(p)}</p>`).join("") : ""}
      ${s.bullets ? `<ul style="padding-left: 20px; margin: 8px 0;">${s.bullets.map((b) => `<li style="margin: 6px 0; color: ${textColor}; line-height: 1.65; font-size: 13px;">${esc(b)}</li>`).join("")}</ul>` : ""}
    </div>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; line-height: 1.65; font-size: 13px; }
</style></head><body>

<div style="background: ${primary}; padding: 44px 32px; margin-bottom: 32px; border-radius: 0 0 10px 10px;">
  <h1 style="font-family: ${fontHeading}; color: #FFFFFF; font-size: 30px; margin-bottom: 8px;">${esc(data.title)}</h1>
  ${data.subtitle ? `<p style="color: rgba(255,255,255,0.75); font-size: 16px; margin-bottom: 4px;">${esc(data.subtitle)}</p>` : ""}
  ${data.author || data.date ? `<p style="color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 14px; font-family: '${fontBody}';">${esc(data.author)}${data.date ? " &middot; " + esc(data.date) : ""}</p>` : ""}
</div>

${sections}

</body></html>`;
}

// ─── PDFKit fallback ──────────────────────────────────────────────────────────

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

// ─── Helpers ──────────────────────────────────────────────────────────────────

function esc(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatNum(n) {
  if (n === undefined || n === null) return "0.00";
  return Number(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function party1Label(party) {
  if (!party.name) return "—";
  let label = `<strong>${esc(party.name)}</strong>`;
  if (party.representative) label += `, в особі ${esc(party.representative)}`;
  if (party.title) label += ` (${esc(party.title)})`;
  return label;
}

main();
