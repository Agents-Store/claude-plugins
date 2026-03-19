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
  } else if (type === "proposal" || type === "report") {
    html = buildSectionDocumentHtml(data, styling, type);
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
  const currency = template?.currencySymbol || styling.currencySymbol || data.currencySymbol || "$";

  const items = data.items || [];
  const subtotal = data.subtotal ?? items.reduce((sum, i) => sum + (i.total || i.quantity * i.unitPrice || 0), 0);
  const tax = data.tax ?? 0;
  const discount = data.discount ?? 0;
  const total = data.total ?? subtotal + tax - discount;

  const companyInfo = data.companyInfo || {};
  const recipient = data.recipient || data.recipientInfo || {};
  const logo = logoHtml(data);

  const itemRows = items
    .map(
      (item, idx) => `
    <tr style="background: ${idx % 2 === 0 ? "#FFFFFF" : bgLight};">
      <td style="padding: 10px 14px; border-bottom: 1px solid ${border}; color: ${textColor};">${esc(item.description)}</td>
      <td style="padding: 10px 14px; text-align: center; border-bottom: 1px solid ${border}; color: ${muted};">${esc(item.quantity)}</td>
      <td style="padding: 10px 14px; text-align: right; border-bottom: 1px solid ${border}; color: ${muted};">${currency}${formatNum(item.unitPrice)}</td>
      <td style="padding: 10px 14px; text-align: right; border-bottom: 1px solid ${border}; color: ${textColor}; font-weight: 600;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 13px; line-height: 1.5; }

  .top-bar { background: ${primary}; height: 5px; }

  /* Header: company block left, invoice meta right */
  .header { display: flex; justify-content: space-between; align-items: flex-start; padding: 22px 0 18px; border-bottom: 1px solid ${border}; margin-bottom: 22px; }
  .company-name { font-family: ${fontHeading}; font-size: 20px; font-weight: 700; color: ${primary}; margin-bottom: 5px; }
  .company-details { color: ${muted}; font-size: 11.5px; line-height: 1.75; }
  .invoice-meta { text-align: right; }
  .invoice-label { font-family: ${fontHeading}; font-size: 26px; font-weight: 700; color: ${primary}; letter-spacing: 0.06em; margin-bottom: 3px; }
  .invoice-num { font-size: 12.5px; font-weight: 700; color: ${textColor}; margin-bottom: 10px; }
  .invoice-dates { font-size: 11.5px; line-height: 2; }
  .d-label { display: inline-block; min-width: 44px; font-size: 9px; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700; color: ${muted}; }
  .d-value { color: ${textColor}; font-weight: 500; }

  /* Bill To: plain text section, no colored box */
  .bill-section { display: flex; gap: 40px; margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px solid ${border}; }
  .bill-col { flex: 1; }
  .bill-col-right { flex: 0 0 auto; text-align: right; }
  .field-label { font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; color: ${muted}; margin-bottom: 5px; }
  .field-name { font-size: 14px; font-weight: 700; color: ${textColor}; margin-bottom: 3px; }
  .field-detail { font-size: 12px; color: ${muted}; line-height: 1.65; }

  /* Items table */
  table.items { width: 100%; border-collapse: collapse; }
  table.items thead tr { background: ${primary}; }
  table.items th { color: #FFFFFF; padding: 9px 14px; text-align: left; font-size: 10.5px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
  table.items th:nth-child(2) { text-align: center; }
  table.items th:nth-child(3), table.items th:nth-child(4) { text-align: right; }

  /* Totals: line-based, right-aligned — no filled boxes */
  .totals-section { display: flex; flex-direction: column; align-items: flex-end; padding: 16px 0 20px; }
  .total-line { display: flex; justify-content: space-between; width: 290px; padding: 4px 0; font-size: 12.5px; }
  .t-label { color: ${muted}; }
  .t-value { color: ${textColor}; }
  .total-divider { width: 290px; border: none; border-top: 1.5px solid ${textColor}; margin: 8px 0 4px; }
  .total-line.grand .t-label { font-size: 13px; font-weight: 700; color: ${textColor}; text-transform: uppercase; letter-spacing: 0.04em; }
  .total-line.grand .t-value { font-size: 15px; font-weight: 700; color: ${primary}; }

  /* Payment section: plain with top separator, no colored background */
  .payment-section { border-top: 1px solid ${border}; padding-top: 14px; }
  .payment-section .section-heading { font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; color: ${muted}; margin-bottom: 10px; }
  .payment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 28px; }
  .p-label { font-size: 9px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; color: ${muted}; margin-bottom: 2px; }
  .p-value { font-size: 12px; color: ${textColor}; }

  .notes { color: ${muted}; font-size: 11px; line-height: 1.6; padding-top: 12px; margin-top: 14px; border-top: 1px solid ${border}; }
  .bottom-bar { background: ${primary}; height: 4px; margin-top: 18px; }
</style></head><body>

<div class="top-bar"></div>

<div class="header">
  <div>
    ${logo}
    <div class="company-name">${esc(companyInfo.name) || "Company Name"}</div>
    <div class="company-details">
      ${companyInfo.address ? esc(companyInfo.address) + "<br>" : ""}${companyInfo.phone ? esc(companyInfo.phone) : ""}${companyInfo.email ? " &middot; " + esc(companyInfo.email) : ""}
    </div>
  </div>
  <div class="invoice-meta">
    <div class="invoice-label">INVOICE</div>
    <div class="invoice-num">${esc(data.invoiceNumber)}</div>
    <div class="invoice-dates">
      <div><span class="d-label">Issued</span>&ensp;<span class="d-value">${esc(data.date)}</span></div>
      <div><span class="d-label">Due</span>&ensp;<span class="d-value">${esc(data.dueDate)}</span></div>
    </div>
  </div>
</div>

<div class="bill-section">
  <div class="bill-col">
    <div class="field-label">Bill To</div>
    <div class="field-name">${esc(recipient.name)}</div>
    <div class="field-detail">${esc(recipient.address)}${recipient.email ? "<br>" + esc(recipient.email) : ""}</div>
  </div>
  <div class="bill-col-right">
    <div class="field-label">Amount Due</div>
    <div class="field-name" style="font-size:18px;color:${primary};">${currency}${formatNum(total)}</div>
    <div class="field-detail">${items.length} item${items.length !== 1 ? "s" : ""} &middot; Due ${esc(data.dueDate) || "on receipt"}</div>
  </div>
</div>

<table class="items">
  <thead>
    <tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr>
  </thead>
  <tbody>${itemRows}</tbody>
</table>

<div class="totals-section">
  <div class="total-line"><span class="t-label">Subtotal</span><span class="t-value">${currency}${formatNum(subtotal)}</span></div>
  ${tax ? `<div class="total-line"><span class="t-label">Tax</span><span class="t-value">${currency}${formatNum(tax)}</span></div>` : ""}
  ${discount ? `<div class="total-line"><span class="t-label">Discount</span><span class="t-value">&minus;${currency}${formatNum(discount)}</span></div>` : ""}
  <div class="total-divider"></div>
  <div class="total-line grand"><span class="t-label">Total Due</span><span class="t-value">${currency}${formatNum(total)}</span></div>
</div>

<div style="page-break-inside:avoid;">
${
  data.paymentDetails
    ? `<div class="payment-section">
  <div class="section-heading">Payment Details</div>
  <div class="payment-grid">
    ${data.paymentDetails.bank ? `<div><div class="p-label">Bank</div><div class="p-value">${esc(data.paymentDetails.bank)}</div></div>` : ""}
    ${data.paymentDetails.accountName ? `<div><div class="p-label">Account Name</div><div class="p-value">${esc(data.paymentDetails.accountName)}</div></div>` : ""}
    ${data.paymentDetails.iban ? `<div><div class="p-label">IBAN</div><div class="p-value">${esc(data.paymentDetails.iban)}</div></div>` : ""}
    ${data.paymentDetails.swift ? `<div><div class="p-label">SWIFT / BIC</div><div class="p-value">${esc(data.paymentDetails.swift)}</div></div>` : ""}
  </div>
</div>`
    : ""
}
${data.notes ? `<div class="notes">${esc(data.notes)}</div>` : ""}
<div class="bottom-bar"></div>
</div>

</body></html>`;
}

// ─── Contract ─────────────────────────────────────────────────────────────────
// Design based on professional legal document standards (BigLaw / corporate MSA):
//   • Serif body font at ~11pt with 1.4 line-height
//   • Justified text with hyphenation
//   • Dark navy full-width article bars, white uppercase text
//   • Section numbers (1.1) inline with paragraph, hanging indent
//   • Recital paragraph auto-generated from party data
//   • "IN WITNESS WHEREOF" preamble before signatures
//   • Two-column signature block: By / Name / Title / Date

function buildContractHtml(data, styling, template) {
  const primary   = styling.primaryColor    || "#1E2D3D";  // deep navy
  const textColor = styling.textColor       || "#1A1A1A";  // near-black (not pure #000)
  const muted     = styling.mutedColor      || "#4A4A4A";
  const border    = styling.borderColor     || "#D4D4D4";
  const fontBody  = `'PT Serif', Georgia, serif`;
  const fontUi    = `'Inter', Arial, sans-serif`;

  // Support both data.party1/party2 and data.parties.{key} map formats
  const partiesMap = data.parties ? Object.values(data.parties) : null;
  const party1 = data.party1 || (partiesMap && partiesMap[0]) || {};
  const party2 = data.party2 || (partiesMap && partiesMap[1]) || {};
  const logo   = logoHtml(data);

  // Full-width article header bar
  const articleBar = (text) =>
    `<div style="background:${primary};color:#fff;font-family:${fontUi};font-size:9.5px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;padding:7px 12px;margin:18px 0 12px;page-break-after:avoid;">${esc(text)}</div>`;

  // Compact party info block — no colored badges, just clean hierarchy
  const partyBlock = (label, p) => `
    <div>
      <div style="font-family:${fontUi};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:${muted};margin-bottom:5px;">${esc(label)}</div>
      ${p.name ? `<div style="font-family:${fontBody};font-size:13px;font-weight:700;color:${textColor};margin-bottom:3px;">${esc(p.name)}</div>` : ""}
      ${p.address ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};line-height:1.5;margin-bottom:1px;">Address: ${esc(p.address)}</div>` : ""}
      ${p.reg ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};margin-bottom:1px;">Registration No: ${esc(p.reg)}</div>` : ""}
      ${p.representative ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};">Representative: ${esc(p.representative)}${p.title ? `, ${esc(p.title)}` : ""}</div>` : ""}
    </div>`;

  // Clause sections with inline numbered paragraphs + hanging indent
  const clausesHtml = (data.clauses || [])
    .map((clause) => {
      const paras = (clause.paragraphs || [clause.content]).filter(Boolean);
      const barTitle = `${clause.number ? "Article " + clause.number + ".  " : ""}${clause.title || ""}`;
      const parasHtml = paras.map((p, i) => {
        const multiPara = clause.number && paras.length > 1;
        const num = multiPara ? `${clause.number}.${i + 1}` : "";
        const indent = multiPara ? "style='padding-left:2.2em;text-indent:-2.2em;'" : "";
        const numSpan = num ? `<span style="font-family:${fontUi};font-size:10px;font-weight:700;color:${textColor};display:inline-block;min-width:2.2em;">${num}</span>` : "";
        return `<p ${indent} style="font-family:${fontBody};font-size:13px;line-height:1.45;color:${textColor};text-align:justify;-webkit-hyphens:auto;hyphens:auto;margin:0 0 9px;orphans:3;widows:3;">${numSpan}${esc(p)}</p>`;
      }).join("");
      return `
      <div style="margin-bottom:4px;page-break-inside:avoid;">
        ${articleBar(barTitle)}
        ${parasHtml}
      </div>`;
    })
    .join("\n");

  // Signature column — By / Name / Title / Date with proper spacing
  const sigLine = (label) => `
    <div style="margin-bottom:16px;">
      <div style="font-family:${fontBody};font-size:12px;color:${textColor};padding-bottom:18px;border-bottom:0.75px solid ${textColor};margin-bottom:3px;">${esc(label)}:</div>
      <div style="font-family:${fontUi};font-size:8px;color:${muted};text-transform:uppercase;letter-spacing:0.1em;"></div>
    </div>`;

  const sigCol = (partyLabel, p) => {
    const partyName = (p.name || partyLabel).toUpperCase();
    return `
    <div style="flex:1;">
      <div style="font-family:${fontUi};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:${muted};margin-bottom:6px;">${esc(partyLabel)}</div>
      <div style="font-family:${fontBody};font-size:11.5px;font-weight:700;color:${textColor};margin-bottom:22px;">${partyName}</div>
      ${sigLine("By")}
      ${sigLine("Name")}
      ${sigLine("Title")}
      ${sigLine("Date")}
    </div>`;
  };

  // Auto-generate recital intro paragraph
  const p1n = party1.name ? `<strong>${esc(party1.name.toUpperCase())}</strong>` : "<strong>CONTRACTOR</strong>";
  const p1e = party1.entity ? `, a ${esc(party1.entity)}` : "";
  const p1a = party1.address ? `, with its principal place of business at ${esc(party1.address)}` : "";
  const p1r = `<strong>"${esc(party1.role || "Contractor")}"</strong>`;
  const p2n = party2.name ? `<strong>${esc(party2.name.toUpperCase())}</strong>` : "<strong>CUSTOMER</strong>";
  const p2e = party2.entity ? `, a ${esc(party2.entity)}` : "";
  const p2a = party2.address ? `, with its principal place of business at ${esc(party2.address)}` : "";
  const p2r = `<strong>"${esc(party2.role || "Customer")}"</strong>`;

  const recital = `This ${esc(data.title || "Service Provision Agreement")} (this <strong>"Agreement"</strong>) is entered into as of ${esc(data.date)}${data.city ? ` in ${esc(data.city)}` : ""} by and between: ${p1n}${p1e}${p1a} (${p1r}); and ${p2n}${p2e}${p2a} (${p2r}).`;

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 13px; line-height: 1.45; background: #fff; }
</style></head><body>

<!-- ═══ TITLE BLOCK ═══ -->
<div style="text-align:center;padding:24px 0 10px;border-bottom:2.5px solid ${primary};margin-bottom:14px;">
  ${logo ? `<div style="margin-bottom:10px;display:flex;justify-content:center;">${logo}</div>` : ""}
  <div style="font-family:${fontBody};font-size:19px;font-weight:700;color:${primary};letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">
    ${esc(data.title || "SERVICE PROVISION AGREEMENT")}
  </div>
  <div style="font-family:${fontUi};font-size:10px;color:${muted};letter-spacing:0.06em;">
    ${data.number ? `Contract No:&nbsp;<strong style="color:${textColor};">${esc(data.number)}</strong>&nbsp;&nbsp;&bull;&nbsp;&nbsp;` : ""}Date:&nbsp;${esc(data.date)}${data.city ? `&nbsp;&nbsp;&bull;&nbsp;&nbsp;${esc(data.city)}` : ""}
  </div>
</div>

<!-- ═══ RECITAL ═══ -->
<p style="font-family:${fontBody};font-size:12.5px;line-height:1.55;color:${textColor};text-align:justify;-webkit-hyphens:auto;hyphens:auto;margin-bottom:4px;">${recital}</p>

<!-- ═══ PARTIES ═══ -->
${articleBar("Parties to this Agreement")}
<div style="display:flex;gap:36px;margin-bottom:4px;">
  <div style="flex:1;">${partyBlock(party1.role || "Contractor (Service Provider)", party1)}</div>
  <div style="flex:1;">${partyBlock(party2.role || "Customer (Client)", party2)}</div>
</div>

<!-- ═══ CLAUSES ═══ -->
${clausesHtml}

<!-- ═══ WITNESS CLAUSE ═══ -->
<p style="font-family:${fontBody};font-size:12.5px;font-style:italic;line-height:1.55;color:${textColor};margin-top:22px;margin-bottom:4px;border-top:1px solid ${border};padding-top:14px;">
  IN WITNESS WHEREOF, the parties have caused this Agreement to be executed by their duly authorized representatives as of the date first set forth above.
</p>

<!-- ═══ SIGNATURES ═══ -->
${articleBar("Signatures")}
<div style="display:flex;gap:48px;margin-top:4px;">
  ${sigCol("For " + (party1.name || "Contractor") + " (" + (party1.role || "Contractor") + ")", party1)}
  ${sigCol("For " + (party2.name || "Customer") + " (" + (party2.role || "Customer") + ")", party2)}
</div>

<div style="background:${primary};height:2.5px;margin-top:32px;"></div>

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
  const contractorName = formatPartyLabel(contractor);
  const customerName = formatPartyLabel(customer);
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
  .act-header { text-align: center; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 2px solid ${primary}; }
  .act-title { font-family: ${fontBody}; font-size: 19px; font-weight: 700; color: ${primary}; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }
  .act-number { font-family: ${fontMeta}; font-size: 13px; font-weight: 600; color: ${textColor}; margin-bottom: 4px; }
  .act-datecity { font-family: ${fontMeta}; font-size: 11.5px; color: ${muted}; letter-spacing: 0.3px; }
  .intro { margin-bottom: 14px; font-size: 12px; line-height: 1.8; }
  table.services { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table.services th { background: ${primary}; color: #fff; padding: 8px 12px; text-align: left; font-family: ${fontMeta}; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
  table.services th:nth-child(1) { width: 40px; text-align: center; }
  table.services th:nth-child(3) { width: 50px; text-align: right; }
  table.services th:nth-child(4) { width: 80px; text-align: right; }
  table.services th:nth-child(5) { width: 90px; text-align: right; }
  table.services th:nth-child(6) { width: 90px; text-align: right; }
  /* Totals: line-based — no filled navy box */
  .totals { margin-bottom: 16px; display: flex; flex-direction: column; align-items: flex-end; }
  .total-row { font-family: ${fontMeta}; font-size: 12px; display: flex; justify-content: space-between; width: 280px; padding: 4px 0; color: ${muted}; }
  .total-divider { width: 280px; border: none; border-top: 1.5px solid ${primary}; margin: 6px 0 4px; }
  .total-row.grand { font-size: 14px; font-weight: 700; padding: 4px 0; }
  .total-row.grand span:first-child { color: ${textColor}; text-transform: uppercase; letter-spacing: 0.04em; }
  .total-row.grand span:last-child { color: ${primary}; }
  .confirm-box { margin-bottom: 16px; padding: 12px 16px; background: ${bgLight}; border-left: 3px solid ${accent}; font-size: 12px; line-height: 1.7; }
  .section-label { font-family: ${fontMeta}; font-size: 9px; text-transform: uppercase; letter-spacing: 2px; color: ${muted}; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid ${border}; padding-bottom: 6px; }
  .sig-grid { display: flex; gap: 40px; margin-top: 8px; page-break-inside: avoid; }
  .sig-col { flex: 1; page-break-inside: avoid; }
  .sig-party { font-family: ${fontMeta}; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: ${primary}; margin-bottom: 6px; }
  .sig-detail { font-family: ${fontMeta}; font-size: 11px; color: ${textColor}; line-height: 1.6; margin-bottom: 2px; }
  .sig-line { border-bottom: 1px solid ${textColor}; margin-top: 36px; }
  .sig-lbl { font-family: ${fontMeta}; font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px; color: ${muted}; margin-top: 4px; }
  .seal-line { border-bottom: 1px dashed ${border}; margin-top: 18px; }
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
  ${vatRate ? `<div class="total-row"><span>Сума без ПДВ</span><span>${currency}${formatNum(total)}</span></div>` : ""}
  ${vatRate ? `<div class="total-row"><span>ПДВ (${vatRate}%)</span><span>${currency}${formatNum(vatAmount)}</span></div>` : ""}
  <div class="total-divider"></div>
  <div class="total-row grand"><span>Всього до сплати</span><span>${currency}${formatNum(total + vatAmount)}</span></div>
</div>

<div class="confirm-box">
  Вищезазначені роботи (послуги) виконані в повному обсязі, у встановлені строки та з належною якістю.
  Замовник до Виконавця претензій щодо якості та обсягу виконаних робіт не має.
  ${data.notes ? "<br>" + esc(data.notes) : ""}
</div>

<div style="page-break-inside:avoid;">
<div class="section-label">Підписи сторін</div>
<div class="sig-grid">
  <div class="sig-col">
    <div class="sig-party">ВИКОНАВЕЦЬ</div>
    <div class="sig-detail">${esc(contractor.name)}</div>
    ${contractor.representative ? `<div class="sig-detail">${esc(contractor.representative)}${contractor.title ? ", " + esc(contractor.title) : ""}</div>` : ""}
    ${contractor.reg ? `<div class="sig-detail">${esc(contractor.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">Підпис / Дата</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">Печатка</div>
  </div>
  <div class="sig-col">
    <div class="sig-party">ЗАМОВНИК</div>
    <div class="sig-detail">${esc(customer.name)}</div>
    ${customer.representative ? `<div class="sig-detail">${esc(customer.representative)}${customer.title ? ", " + esc(customer.title) : ""}</div>` : ""}
    ${customer.reg ? `<div class="sig-detail">${esc(customer.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">Підпис / Дата</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">Печатка</div>
  </div>
</div>
</div>

</body></html>`;
}

// ─── Generic (report, proposal, etc.) ────────────────────────────────────────

// ─── Proposal / Report ────────────────────────────────────────────────────────
// Shared builder for section-based documents. Matches DOCX visual language:
// Georgia headings in navy, accent underline on H1, Inter body, clean whitespace.

function buildSectionDocumentHtml(data, styling, type) {
  const primary    = styling.primaryColor  || "#1E3A5F";
  const accent     = styling.accentColor   || "#2563EB";
  const textColor  = styling.textColor     || "#1E293B";
  const muted      = styling.mutedColor    || "#64748B";
  const border     = styling.borderColor   || "#E2E8F0";
  const fontHeading = `'PT Serif', Georgia, serif`;
  const fontBody    = `'Inter', Arial, sans-serif`;

  // ── Content parser: turns plain text with bullets/numbers into HTML ──
  function renderContent(text) {
    if (!text) return "";
    const paragraphs = text.split(/\n\n+/);
    return paragraphs.map((block) => {
      const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
      // Detect list block: all lines start with bullet/dash/number
      const isList = lines.length > 1 && lines.every((l) => /^[•\-–—]\s|^\d+[\.\)]\s/.test(l));
      if (isList) {
        const items = lines.map((l) => l.replace(/^[•\-–—]\s+|^\d+[\.\)]\s+/, ""));
        const isOrdered = /^\d+/.test(lines[0]);
        const tag = isOrdered ? "ol" : "ul";
        return `<${tag} style="margin:0 0 11px 20px;padding:0;">${items.map((i) => `<li style="margin-bottom:5px;line-height:1.55;color:${textColor};font-size:13px;">${esc(i)}</li>`).join("")}</${tag}>`;
      }
      // Single line that is a bullet
      if (lines.length === 1 && /^[•\-–—]\s|^\d+[\.\)]\s/.test(lines[0])) {
        const item = lines[0].replace(/^[•\-–—]\s+|^\d+[\.\)]\s+/, "");
        return `<ul style="margin:0 0 6px 20px;padding:0;"><li style="margin-bottom:3px;line-height:1.55;color:${textColor};font-size:13px;">${esc(item)}</li></ul>`;
      }
      return `<p style="margin:0 0 11px;line-height:1.6;color:${textColor};font-size:13px;">${esc(block.replace(/\n/g, " "))}</p>`;
    }).join("");
  }

  // ── TOC ──
  const sections = data.sections || [];
  const tocHtml = sections.map((s) => {
    const level = s.level || 1;
    const indent = level > 1 ? `padding-left:${(level - 1) * 18}px;` : "";
    return `<div style="${indent}margin-bottom:${level === 1 ? 7 : 4}px;">
      <span style="font-family:${level === 1 ? fontHeading : fontBody};font-size:${level === 1 ? "13px" : "12px"};color:${level === 1 ? primary : muted};font-weight:${level === 1 ? "700" : "400"};">${esc(s.heading || s.title || "")}</span>
    </div>`;
  }).join("");

  // ── Sections body ──
  const sectionsHtml = sections.map((s) => {
    const level = s.level || 1;
    if (level === 1) {
      return `
      <div style="margin-top:28px;margin-bottom:20px;page-break-inside:avoid;">
        <div style="font-family:${fontHeading};font-size:18px;font-weight:700;color:${primary};margin-bottom:7px;page-break-after:avoid;">${esc(s.heading || s.title || "")}</div>
        <div style="height:1.5px;background:${accent};width:100%;margin-bottom:14px;"></div>
      </div>
      <div>${renderContent(s.content || "")}${(s.bullets || []).map((b) => `<p style="margin:0 0 6px 20px;line-height:1.55;color:${textColor};font-size:13px;">• ${esc(b)}</p>`).join("")}</div>`;
    } else if (level === 2) {
      return `
      <div style="margin-top:18px;margin-bottom:10px;page-break-after:avoid;">
        <div style="font-family:${fontHeading};font-size:14px;font-weight:700;color:${primary};margin-bottom:6px;">${esc(s.heading || s.title || "")}</div>
      </div>
      <div>${renderContent(s.content || "")}</div>`;
    } else {
      return `
      <div style="margin-top:12px;margin-bottom:8px;">
        <div style="font-family:${fontBody};font-size:12px;font-weight:700;color:${textColor};margin-bottom:5px;">${esc(s.heading || s.title || "")}</div>
      </div>
      <div>${renderContent(s.content || "")}</div>`;
    }
  }).join("\n");

  // ── Cover meta ──
  const metaLines = [];
  if (data.author)    metaLines.push(`<span>Prepared by &nbsp;<strong style="color:${textColor};">${esc(data.author)}</strong></span>`);
  if (data.recipient) metaLines.push(`<span>Prepared for &nbsp;<strong style="color:${textColor};">${esc(data.recipient)}</strong></span>`);
  if (data.date)      metaLines.push(`<span>${esc(data.date)}</span>`);
  if (data.companyName && data.companyName !== data.author) metaLines.push(`<span>${esc(data.companyName)}</span>`);

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 13px; line-height: 1.5; background: #fff; }
  ul li::marker { color: ${accent}; }
  ol li::marker { color: ${accent}; font-weight: 700; }
</style></head><body>

<!-- ═══ TOP BAR ═══ -->
<div style="background:${primary};height:5px;margin-bottom:22px;"></div>

<!-- ═══ COVER ═══ -->
<div style="padding-bottom:20px;border-bottom:1px solid ${border};margin-bottom:22px;">
  <div style="display:inline-block;font-family:${fontBody};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:${accent};margin-bottom:12px;">${type === "proposal" ? "Proposal" : "Report"}</div>
  <div style="font-family:${fontHeading};font-size:28px;font-weight:700;color:${primary};line-height:1.2;margin-bottom:${data.subtitle ? "8px" : "14px"};">${esc(data.title || "")}</div>
  ${data.subtitle ? `<div style="font-family:${fontBody};font-size:15px;color:${muted};margin-bottom:14px;">${esc(data.subtitle)}</div>` : ""}
  ${metaLines.length > 0 ? `<div style="font-family:${fontBody};font-size:10px;color:${muted};display:flex;flex-wrap:wrap;gap:14px;">${metaLines.join("")}</div>` : ""}
</div>

<!-- ═══ TABLE OF CONTENTS ═══ -->
${tocHtml ? `
<div style="margin-bottom:24px;">
  <div style="font-family:${fontHeading};font-size:14px;font-weight:700;color:${primary};margin-bottom:12px;">Contents</div>
  ${tocHtml}
</div>
<div style="border-top:1px solid ${border};margin-bottom:24px;"></div>` : ""}

<!-- ═══ SECTIONS ═══ -->
${sectionsHtml}

<!-- ═══ BOTTOM BAR ═══ -->
<div style="background:${primary};height:4px;margin-top:32px;"></div>

</body></html>`;
}

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

function formatPartyLabel(party) {
  if (!party.name) return "—";
  let label = `<strong>${esc(party.name)}</strong>`;
  if (party.representative) label += `, в особі ${esc(party.representative)}`;
  if (party.title) label += ` (${esc(party.title)})`;
  return label;
}

main();
