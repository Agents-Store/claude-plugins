/**
 * Shared HTML Template Module
 *
 * Single source of truth for all HTML-based document rendering.
 * Used by generate_pdf.js (for PDF output) and generate_docx.js (for pandoc-based DOCX).
 *
 * Design system:
 *   - Source Serif 4 (heading/legal) + Inter (body) + Playfair Display (cover titles)
 *   - Georgia (heading fallback) + Arial (body fallback) for DOCX
 *   - Color palette: Slate-900 #0F172A (primary), Indigo-500 #6366F1 (accent)
 *   - 60-30-10 rule: 60% white, 30% primary, 10% accent
 */

const path = require("path");

// ─── Font Embedding ──────────────────────────────────────────────────────────

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
    // Source Serif 4 is a variable font — one file covers 400-700 weight range
    const ssVarFace = (family, latinB64, cyrillicB64) => {
      let css = "";
      if (cyrillicB64) {
        css += `@font-face{font-family:'${family}';font-weight:200 900;font-style:normal;unicode-range:U+0301,U+0400-04FF,U+0500-052F,U+2DE0-2DFF,U+A640-A69F;src:url('data:font/woff2;base64,${cyrillicB64}') format('woff2');}`;
      }
      css += `@font-face{font-family:'${family}';font-weight:200 900;font-style:normal;src:url('data:font/woff2;base64,${latinB64}') format('woff2');}`;
      return css;
    };

    return `<style>
${face("Inter", 400, fonts.interLatin400, fonts.interCyrillic400)}
${face("Inter", 700, fonts.interLatin700, fonts.interCyrillic700)}
${ssVarFace("Source Serif 4", fonts.sourceSerifLatin || fonts.ptSerifLatin400, fonts.sourceSerifCyrillic || fonts.ptSerifCyrillic400)}
${fonts.playfairLatin700 ? face("Playfair Display", 700, fonts.playfairLatin700, fonts.playfairCyrillic700) : ""}
</style>`;
  } catch (_) {
    return `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Source+Serif+4:wght@400;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">`;
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

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

function formatPartyLabel(party, L) {
  if (!party.name) return "\u2014";
  let label = `<strong>${esc(party.name)}</strong>`;
  const repPrefix = (L && L.representativePrefix) || ", represented by ";
  if (party.representative) label += `${repPrefix}${esc(party.representative)}`;
  if (party.title) label += ` (${esc(party.title)})`;
  return label;
}

function logoHtml(data) {
  const src = data.logoBase64
    ? `data:image/png;base64,${data.logoBase64}`
    : data.logoUrl || "";
  if (!src) return "";
  return `<img src="${src}" alt="logo" style="max-height:56px;max-width:160px;object-fit:contain;display:block;margin-bottom:6px;">`;
}

// ─── Gradient helper ─────────────────────────────────────────────────────────

function gradient(primary, accentDark) {
  return `linear-gradient(135deg, ${primary} 0%, ${accentDark} 100%)`;
}

// ─── Default Styling ─────────────────────────────────────────────────────────

function getDefaults(styling) {
  return {
    primary:     styling.primaryColor    || "#0F172A",
    accent:      styling.accentColor     || "#6366F1",
    accentDark:  styling.accentDarkColor || "#4338CA",
    textColor:   styling.textColor       || "#1E293B",
    muted:       styling.mutedColor      || "#64748B",
    border:      styling.borderColor     || "#E2E8F0",
    borderLight: styling.borderLightColor|| "#F1F5F9",
    bgLight:     styling.backgroundColor || "#F8FAFC",
    fontHeading: `'Source Serif 4', Georgia, serif`,
    fontBody:    `'Inter', Arial, sans-serif`,
    fontDisplay: `'Playfair Display', 'Source Serif 4', Georgia, serif`,
    fontUi:      `'Inter', Arial, sans-serif`,
  };
}

// ─── Base Styles ─────────────────────────────────────────────────────────────

/**
 * Returns common CSS reset + body styles for any document type.
 */
function getBaseStyles(s) {
  return `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: ${s.fontBody};
    color: ${s.textColor};
    font-size: 13px;
    line-height: 1.55;
    background: #fff;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-lining-nums;
  }
  h1, h2, h3, h4 { text-rendering: optimizeLegibility; }
  ul li::marker { color: ${s.accent}; }
  ol li::marker { color: ${s.accent}; font-weight: 600; }
  p { orphans: 3; widows: 3; }
  `;
}

// ─── Content Renderer ────────────────────────────────────────────────────────

/**
 * Smart content parser: turns plain text with bullets/numbers into HTML.
 */
function renderContent(text, s) {
  if (!text) return "";
  const paragraphs = text.split(/\n\n+/);
  return paragraphs.map((block) => {
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
    const isList = lines.length > 1 && lines.every((l) => /^[•\-–—]\s|^\d+[\.\)]\s/.test(l));
    if (isList) {
      const items = lines.map((l) => l.replace(/^[•\-–—]\s+|^\d+[\.\)]\s+/, ""));
      const isOrdered = /^\d+/.test(lines[0]);
      const tag = isOrdered ? "ol" : "ul";
      return `<${tag} style="margin:0 0 11px 20px;padding:0;">${items.map((i) => `<li style="margin-bottom:5px;line-height:1.55;color:${s.textColor};font-size:13px;">${esc(i)}</li>`).join("")}</${tag}>`;
    }
    if (lines.length === 1 && /^[•\-–—]\s|^\d+[\.\)]\s/.test(lines[0])) {
      const item = lines[0].replace(/^[•\-–—]\s+|^\d+[\.\)]\s+/, "");
      return `<ul style="margin:0 0 6px 20px;padding:0;"><li style="margin-bottom:3px;line-height:1.55;color:${s.textColor};font-size:13px;">${esc(item)}</li></ul>`;
    }
    return `<p style="margin:0 0 11px;line-height:1.6;color:${s.textColor};font-size:13px;">${esc(block.replace(/\n/g, " "))}</p>`;
  }).join("");
}

// ─── Cover Page ──────────────────────────────────────────────────────────────

/**
 * Full-page cover for proposals and reports.
 * McKinsey-inspired: gradient top bar, clean typography, dot-separated meta.
 */
function buildCoverHtml(data, s, type) {
  const logo = logoHtml(data.companyInfo || data);
  const typeLabel = type === "proposal" ? "PROPOSAL" : type === "report" ? "REPORT" : "";
  const grad = gradient(s.primary, s.accentDark);

  const metaParts = [];
  if (data.author) metaParts.push(`Prepared by <strong style="color:${s.textColor};">${esc(data.author)}</strong>`);
  if (data.recipient) metaParts.push(`Prepared for <strong style="color:${s.textColor};">${esc(data.recipient)}</strong>`);
  if (data.date) metaParts.push(esc(data.date));
  if (data.companyName && data.companyName !== data.author) metaParts.push(esc(data.companyName));

  const metaHtml = metaParts.length > 0
    ? `<div style="font-family:${s.fontBody};font-size:10.5px;color:${s.muted};display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px;">${metaParts.map((m, i) => `<span>${m}</span>${i < metaParts.length - 1 ? `<span style="color:${s.border};">&middot;</span>` : ""}`).join("")}</div>`
    : "";

  return `
<!-- ═══ COVER PAGE ═══ -->
<div style="min-height:calc(100vh - 50mm);display:flex;flex-direction:column;justify-content:center;page-break-after:always;">
  <div style="background:${grad};height:6px;margin-bottom:36px;border-radius:3px;"></div>
  ${logo ? `<div style="margin-bottom:24px;">${logo}</div>` : ""}
  ${typeLabel ? `<div style="display:inline-block;font-family:${s.fontBody};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:${s.accent};margin-bottom:12px;">${typeLabel}</div>` : ""}
  <div style="font-family:${s.fontDisplay};font-size:38px;font-weight:700;color:${s.primary};line-height:1.12;letter-spacing:-0.02em;margin-bottom:${data.subtitle ? "10px" : "18px"};">${esc(data.title || "")}</div>
  ${data.subtitle ? `<div style="font-family:${s.fontBody};font-size:17px;color:${s.muted};margin-bottom:18px;">${esc(data.subtitle)}</div>` : ""}
  ${metaHtml}
  <div style="background:${grad};height:3px;margin-top:36px;border-radius:1.5px;"></div>
</div>`;
}

// ─── Table of Contents ───────────────────────────────────────────────────────

function buildTocHtml(sections, s) {
  if (!sections || sections.length === 0) return "";
  const tocItems = sections.map((sec) => {
    const level = sec.level || 1;
    const indent = level > 1 ? `padding-left:${(level - 1) * 18}px;` : "";
    return `<div style="${indent}margin-bottom:${level === 1 ? 7 : 4}px;">
      <span style="font-family:${level === 1 ? s.fontHeading : s.fontBody};font-size:${level === 1 ? "13px" : "12px"};color:${level === 1 ? s.primary : s.muted};font-weight:${level === 1 ? "700" : "400"};">${esc(sec.heading || sec.title || "")}</span>
    </div>`;
  }).join("");

  return `
<div style="margin-bottom:28px;">
  <div style="font-family:${s.fontHeading};font-size:14px;font-weight:700;color:${s.primary};margin-bottom:12px;">Contents</div>
  ${tocItems}
</div>
<div style="border-top:1px solid ${s.border};margin-bottom:28px;"></div>`;
}

// ─── Sections Body ───────────────────────────────────────────────────────────

function buildSectionsHtml(sections, s) {
  if (!sections) return "";
  const grad = gradient(s.accent, s.accentDark);
  return sections.map((sec) => {
    const level = sec.level || 1;
    const content = renderContent(sec.content || "", s);
    const bullets = (sec.bullets || []).map((b) =>
      `<p style="margin:0 0 6px 20px;line-height:1.55;color:${s.textColor};font-size:13px;">\u2022 ${esc(b)}</p>`
    ).join("");

    if (level === 1) {
      return `
      <div style="margin-top:32px;margin-bottom:20px;page-break-inside:avoid;">
        <div style="font-family:${s.fontHeading};font-size:19px;font-weight:700;color:${s.primary};margin-bottom:7px;letter-spacing:-0.02em;page-break-after:avoid;">${esc(sec.heading || sec.title || "")}</div>
        <div style="height:2px;background:${grad};width:100%;margin-bottom:14px;border-radius:1px;"></div>
      </div>
      <div>${content}${bullets}</div>`;
    } else if (level === 2) {
      return `
      <div style="margin-top:18px;margin-bottom:10px;page-break-after:avoid;">
        <div style="font-family:${s.fontHeading};font-size:14px;font-weight:700;color:${s.primary};margin-bottom:6px;">${esc(sec.heading || sec.title || "")}</div>
      </div>
      <div>${content}${bullets}</div>`;
    } else {
      return `
      <div style="margin-top:12px;margin-bottom:8px;">
        <div style="font-family:${s.fontBody};font-size:12px;font-weight:700;color:${s.textColor};margin-bottom:5px;">${esc(sec.heading || sec.title || "")}</div>
      </div>
      <div>${content}${bullets}</div>`;
    }
  }).join("\n");
}

// ─── Data Table ──────────────────────────────────────────────────────────────

/**
 * Professional styled table with gradient header and subtle row stripes.
 */
function buildTableHtml(tableData, s) {
  if (!tableData || !tableData.length) return "";
  const headers = tableData[0];
  const rows = tableData.slice(1);
  const grad = gradient(s.primary, s.accentDark);

  const thCells = headers.map((h, i) => {
    let borderRadius = "";
    if (i === 0) borderRadius = "border-radius:6px 0 0 0;";
    if (i === headers.length - 1) borderRadius = "border-radius:0 6px 0 0;";
    if (headers.length === 1) borderRadius = "border-radius:6px 6px 0 0;";
    return `<th style="background:${grad};color:#fff;padding:12px 16px;text-align:left;font-family:${s.fontBody};font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;${borderRadius}">${esc(h)}</th>`;
  }).join("");

  const bodyRows = rows.map((row, idx) => {
    const bg = idx % 2 === 0 ? "#FFFFFF" : "rgba(0, 0, 0, 0.015)";
    const cells = row.map((cell) => {
      const isNum = typeof cell === "number" || (typeof cell === "string" && /^\s*[\d,]+(\.\d+)?\s*$/.test(cell));
      const numStyle = isNum ? "font-variant-numeric:tabular-lining-nums;text-align:right;" : "";
      return `<td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};color:${s.textColor};font-size:12px;${numStyle}">${esc(cell)}</td>`;
    }).join("");
    return `<tr style="background:${bg};">${cells}</tr>`;
  }).join("\n");

  return `
<table style="width:100%;border-collapse:collapse;margin:14px 0;">
  <thead><tr>${thCells}</tr></thead>
  <tbody>${bodyRows}</tbody>
</table>`;
}

// ─── Full Document Assemblers ────────────────────────────────────────────────

/**
 * Build full HTML for a proposal or report (section-based document).
 * Full-page cover + TOC + sections + bottom bar.
 */
function buildSectionDocumentHtml(data, styling, type) {
  const s = getDefaults(styling);
  const sections = data.sections || [];
  const grad = gradient(s.primary, s.accentDark);

  const cover = buildCoverHtml(data, s, type);
  const toc = buildTocHtml(sections, s);
  const body = buildSectionsHtml(sections, s);

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  ${getBaseStyles(s)}
</style></head><body>

${cover}

${toc}

${body}

<!-- ═══ BOTTOM BAR ═══ -->
<div style="background:${grad};height:4px;margin-top:32px;border-radius:2px;"></div>

</body></html>`;
}

/**
 * Build generic document HTML — clean design matching the section document style.
 */
function buildGenericHtml(data, styling) {
  const s = getDefaults(styling);
  const grad = gradient(s.accent, s.accentDark);

  const sections = (data.sections || []).map((sec) => {
    const level = sec.level || 1;
    const fontSize = level === 1 ? "20px" : level === 2 ? "16px" : "14px";
    const letterSpacing = level === 1 ? "letter-spacing:-0.02em;" : "";
    const content = sec.content
      ? sec.content.split("\n\n").map((p) => `<p style="margin:0 0 11px;line-height:1.6;color:${s.textColor};font-size:13px;">${esc(p)}</p>`).join("")
      : "";
    const bullets = sec.bullets
      ? `<ul style="padding-left:20px;margin:8px 0;">${sec.bullets.map((b) => `<li style="margin:6px 0;color:${s.textColor};line-height:1.55;font-size:13px;">${esc(b)}</li>`).join("")}</ul>`
      : "";

    return `
    <div style="margin-bottom:28px;">
      <div style="font-family:${s.fontHeading};color:${s.primary};margin:0 0 7px;font-size:${fontSize};font-weight:700;${letterSpacing}">${esc(sec.heading || sec.title || "")}</div>
      <div style="height:2px;background:${level === 1 ? grad : s.accent};width:${level === 1 ? "100%" : "60px"};margin-bottom:14px;border-radius:1px;"></div>
      ${content}
      ${bullets}
    </div>`;
  }).join("\n");

  const logo = logoHtml(data.companyInfo || data);
  const headerGrad = gradient(s.primary, s.accentDark);

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  ${getBaseStyles(s)}
</style></head><body>

<!-- ═══ HEADER ═══ -->
<div style="border-bottom:2px solid ${s.primary};padding-bottom:20px;margin-bottom:28px;">
  ${logo ? `<div style="margin-bottom:12px;">${logo}</div>` : ""}
  <div style="font-family:${s.fontHeading};font-size:28px;font-weight:700;color:${s.primary};margin-bottom:6px;letter-spacing:-0.02em;">${esc(data.title || "")}</div>
  ${data.subtitle ? `<p style="color:${s.muted};font-size:15px;margin-bottom:4px;">${esc(data.subtitle)}</p>` : ""}
  ${data.author || data.date ? `<p style="color:${s.muted};font-size:11px;margin-top:10px;">${esc(data.author || "")}${data.date ? " \u00b7 " + esc(data.date) : ""}</p>` : ""}
</div>

${sections}

<div style="background:${headerGrad};height:4px;margin-top:32px;border-radius:2px;"></div>

</body></html>`;
}

// ─── Invoice ─────────────────────────────────────────────────────────────────

function buildInvoiceHtml(data, styling, template) {
  const s = getDefaults(styling);
  const currency = template?.currencySymbol || styling.currencySymbol || data.currencySymbol || "$";
  const grad = gradient(s.primary, s.accentDark);

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
    <tr style="background: ${idx % 2 === 0 ? "#FFFFFF" : "rgba(0, 0, 0, 0.015)"};">
      <td style="padding: 12px 16px; border-bottom: 0.5px solid ${s.borderLight}; color: ${s.textColor};">${esc(item.description)}</td>
      <td style="padding: 12px 16px; text-align: center; border-bottom: 0.5px solid ${s.borderLight}; color: ${s.muted}; font-variant-numeric: tabular-lining-nums;">${esc(item.quantity)}</td>
      <td style="padding: 12px 16px; text-align: right; border-bottom: 0.5px solid ${s.borderLight}; color: ${s.muted}; font-variant-numeric: tabular-lining-nums;">${currency}${formatNum(item.unitPrice)}</td>
      <td style="padding: 12px 16px; text-align: right; border-bottom: 0.5px solid ${s.borderLight}; color: ${s.textColor}; font-weight: 600; font-variant-numeric: tabular-lining-nums;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${s.fontBody}; color: ${s.textColor}; font-size: 13px; line-height: 1.55; text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-lining-nums; }

  .top-bar { background: ${grad}; height: 6px; border-radius: 0 0 3px 3px; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; padding: 22px 0 18px; border-bottom: 1px solid ${s.border}; margin-bottom: 22px; }
  .company-name { font-family: ${s.fontHeading}; font-size: 22px; font-weight: 700; color: ${s.primary}; margin-bottom: 5px; letter-spacing: -0.01em; }
  .company-details { color: ${s.muted}; font-size: 11.5px; line-height: 1.75; }
  .invoice-meta { text-align: right; }
  .invoice-label { font-family: ${s.fontHeading}; font-size: 28px; font-weight: 700; color: ${s.primary}; letter-spacing: -0.01em; margin-bottom: 3px; }
  .invoice-num { font-size: 12.5px; font-weight: 700; color: ${s.textColor}; margin-bottom: 10px; }
  .invoice-dates { font-size: 11.5px; line-height: 2; }
  .d-label { display: inline-block; min-width: 44px; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: ${s.muted}; }
  .d-value { color: ${s.textColor}; font-weight: 500; }

  .bill-section { display: flex; gap: 40px; margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px solid ${s.border}; }
  .bill-col { flex: 1; }
  .bill-col-right { flex: 0 0 auto; text-align: right; }
  .field-label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: ${s.muted}; margin-bottom: 5px; }
  .field-name { font-size: 14px; font-weight: 700; color: ${s.textColor}; margin-bottom: 3px; }
  .field-detail { font-size: 12px; color: ${s.muted}; line-height: 1.65; }

  table.items { width: 100%; border-collapse: collapse; }
  table.items thead tr { background: ${grad}; }
  table.items th { color: #FFFFFF; padding: 12px 16px; text-align: left; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
  table.items th:first-child { border-radius: 6px 0 0 0; }
  table.items th:last-child { border-radius: 0 6px 0 0; }
  table.items th:nth-child(2) { text-align: center; }
  table.items th:nth-child(3), table.items th:nth-child(4) { text-align: right; }

  .totals-section { display: flex; flex-direction: column; align-items: flex-end; padding: 16px 0 20px; }
  .total-line { display: flex; justify-content: space-between; width: 290px; padding: 4px 0; font-size: 12.5px; }
  .t-label { color: ${s.muted}; }
  .t-value { color: ${s.textColor}; font-variant-numeric: tabular-lining-nums; }
  .total-divider { width: 290px; height: 2px; background: ${grad}; border: none; margin: 8px 0 4px; border-radius: 1px; }
  .total-line.grand .t-label { font-size: 13px; font-weight: 700; color: ${s.textColor}; text-transform: uppercase; letter-spacing: 0.04em; }
  .total-line.grand .t-value { font-size: 16px; font-weight: 700; color: ${s.primary}; }

  .payment-section { border-top: 1px solid ${s.border}; padding-top: 14px; }
  .payment-section .section-heading { font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: ${s.muted}; margin-bottom: 10px; }
  .payment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 32px; }
  .p-label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: ${s.muted}; margin-bottom: 2px; }
  .p-value { font-size: 12px; color: ${s.textColor}; }

  .notes { color: ${s.muted}; font-size: 11px; line-height: 1.6; padding-top: 12px; margin-top: 14px; border-top: 1px solid ${s.border}; }
  .bottom-bar { background: ${grad}; height: 4px; margin-top: 18px; border-radius: 2px; }
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
    <div class="field-name" style="font-size:18px;color:${s.primary};">${currency}${formatNum(total)}</div>
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

// ─── Contract ────────────────────────────────────────────────────────────────

function buildContractHtml(data, styling, template) {
  const s = getDefaults(styling);
  // Contract uses slightly different defaults for a more legal feel
  const primary   = styling.primaryColor    || "#1E2D3D";
  const accentDk  = styling.accentDarkColor || "#4338CA";
  const textColor = styling.textColor       || "#1A1A1A";
  const muted     = styling.mutedColor      || "#4A4A4A";
  const border    = styling.borderColor     || "#D4D4D4";
  const fontBody  = s.fontHeading; // Source Serif 4 for legal body
  const fontUi    = s.fontBody;    // Inter for UI elements
  const grad      = gradient(primary, accentDk);

  const partiesMap = data.parties ? Object.values(data.parties) : null;
  const party1 = data.party1 || (partiesMap && partiesMap[0]) || {};
  const party2 = data.party2 || (partiesMap && partiesMap[1]) || {};
  const logo   = logoHtml(data);

  const articleBar = (text) =>
    `<div style="background:${grad};color:#fff;font-family:${fontUi};font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:8px 12px;margin:18px 0 12px;page-break-after:avoid;border-radius:4px;">${esc(text)}</div>`;

  const partyBlock = (label, p) => `
    <div>
      <div style="font-family:${fontUi};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:${muted};margin-bottom:5px;">${esc(label)}</div>
      ${p.name ? `<div style="font-family:${fontBody};font-size:13px;font-weight:700;color:${textColor};margin-bottom:3px;">${esc(p.name)}</div>` : ""}
      ${p.address ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};line-height:1.5;margin-bottom:1px;">Address: ${esc(p.address)}</div>` : ""}
      ${p.reg ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};margin-bottom:1px;">Registration No: ${esc(p.reg)}</div>` : ""}
      ${p.representative ? `<div style="font-family:${fontUi};font-size:10px;color:${muted};">Representative: ${esc(p.representative)}${p.title ? `, ${esc(p.title)}` : ""}</div>` : ""}
    </div>`;

  const clausesHtml = (data.clauses || [])
    .map((clause) => {
      const paras = (clause.paragraphs || [clause.content]).filter(Boolean);
      const barTitle = `${clause.number ? "Article " + clause.number + ".  " : ""}${clause.title || ""}`;
      const parasHtml = paras.map((p, i) => {
        const multiPara = clause.number && paras.length > 1;
        const num = multiPara ? `${clause.number}.${i + 1}` : "";
        const indent = multiPara ? "style='padding-left:2.2em;text-indent:-2.2em;'" : "";
        const numSpan = num ? `<span style="font-family:${fontUi};font-size:10px;font-weight:600;color:${s.accent};display:inline-block;min-width:2.2em;">${num}</span>` : "";
        return `<p ${indent} style="font-family:${fontBody};font-size:12.5pt;line-height:1.5;color:${textColor};text-align:justify;-webkit-hyphens:auto;hyphens:auto;margin:0 0 9px;orphans:3;widows:3;">${numSpan}${esc(p)}</p>`;
      }).join("");
      return `
      <div style="margin-bottom:4px;page-break-inside:avoid;">
        ${articleBar(barTitle)}
        ${parasHtml}
      </div>`;
    })
    .join("\n");

  const sigLine = (label) => `
    <div style="margin-bottom:16px;">
      <div style="font-family:${fontBody};font-size:12px;color:${textColor};padding-bottom:22px;border-bottom:0.5px solid ${textColor};margin-bottom:3px;">${esc(label)}:</div>
      <div style="font-family:${fontUi};font-size:8px;color:${muted};text-transform:uppercase;letter-spacing:0.1em;"></div>
    </div>`;

  const sigCol = (partyLabel, p) => {
    const partyName = (p.name || partyLabel).toUpperCase();
    return `
    <div style="flex:1;">
      <div style="font-family:${fontUi};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:${muted};margin-bottom:6px;">${esc(partyLabel)}</div>
      <div style="font-family:${fontBody};font-size:11.5px;font-weight:700;color:${textColor};margin-bottom:22px;">${partyName}</div>
      ${sigLine("By")}
      ${sigLine("Name")}
      ${sigLine("Title")}
      ${sigLine("Date")}
    </div>`;
  };

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
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 12.5pt; line-height: 1.5; background: #fff; text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; }
</style></head><body>

<div style="text-align:center;padding:24px 0 10px;border-bottom:2.5px solid ${primary};margin-bottom:14px;">
  ${logo ? `<div style="margin-bottom:10px;display:flex;justify-content:center;">${logo}</div>` : ""}
  <div style="font-family:${fontBody};font-size:20px;font-weight:700;color:${primary};letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">
    ${esc(data.title || "SERVICE PROVISION AGREEMENT")}
  </div>
  <div style="font-family:${fontUi};font-size:10px;color:${muted};letter-spacing:0.06em;">
    ${data.number ? `Contract No:&nbsp;<strong style="color:${textColor};">${esc(data.number)}</strong>&nbsp;&nbsp;&bull;&nbsp;&nbsp;` : ""}Date:&nbsp;${esc(data.date)}${data.city ? `&nbsp;&nbsp;&bull;&nbsp;&nbsp;${esc(data.city)}` : ""}
  </div>
</div>

<p style="font-family:${fontBody};font-size:12.5pt;line-height:1.5;color:${textColor};text-align:justify;-webkit-hyphens:auto;hyphens:auto;margin-bottom:4px;">${recital}</p>

${articleBar("Parties to this Agreement")}
<div style="display:flex;gap:36px;margin-bottom:4px;">
  <div style="flex:1;">${partyBlock(party1.role || "Contractor (Service Provider)", party1)}</div>
  <div style="flex:1;">${partyBlock(party2.role || "Customer (Client)", party2)}</div>
</div>

${clausesHtml}

<p style="font-family:${fontBody};font-size:12.5pt;font-style:italic;line-height:1.5;color:${textColor};margin-top:22px;margin-bottom:4px;border-top:1px solid ${border};padding-top:14px;">
  IN WITNESS WHEREOF, the parties have caused this Agreement to be executed by their duly authorized representatives as of the date first set forth above.
</p>

${articleBar("Signatures")}
<div style="display:flex;gap:48px;margin-top:4px;">
  ${sigCol("For " + (party1.name || "Contractor") + " (" + (party1.role || "Contractor") + ")", party1)}
  ${sigCol("For " + (party2.name || "Customer") + " (" + (party2.role || "Customer") + ")", party2)}
</div>

<div style="background:${grad};height:3px;margin-top:32px;border-radius:1.5px;"></div>

</body></html>`;
}

// ─── Act of Completed Works ──────────────────────────────────────────────────

const ACT_I18N = {
  en: {
    title: "Certificate of Completion", cityPrefix: "",
    serviceDescription: "Service / Work Description", unit: "Unit", quantity: "Qty", price: "Price", amount: "Amount",
    subtotal: "Subtotal (excl. VAT)", vat: "VAT", totalDue: "Total Due",
    confirmText: "The above-listed works and services have been completed in full, within the agreed timeframe, and to proper quality standards. The Client has no claims regarding the quality, scope, or timeliness of the completed works.",
    signaturesLabel: "Signatures", contractor: "SERVICE PROVIDER", customer: "CLIENT",
    signatureDate: "Signature / Date", seal: "Seal",
    introTemplate: (cn, cusn, cr) => `We, the undersigned, ${cn} (hereinafter referred to as the <strong>Service Provider</strong>) and ${cusn} (hereinafter referred to as the <strong>Client</strong>), hereby certify that${cr} the Service Provider has performed and the Client has accepted the following works and services:`,
    contractRefPrefix: " in accordance with ", representativePrefix: ", represented by ",
  },
  ua: {
    title: "\u0410\u043a\u0442 \u0432\u0438\u043a\u043e\u043d\u0430\u043d\u0438\u0445 \u0440\u043e\u0431\u0456\u0442", cityPrefix: "\u043c. ",
    serviceDescription: "\u041d\u0430\u0439\u043c\u0435\u043d\u0443\u0432\u0430\u043d\u043d\u044f \u043f\u043e\u0441\u043b\u0443\u0433\u0438 / \u0440\u043e\u0431\u043e\u0442\u0438", unit: "\u041e\u0434.", quantity: "\u041a\u0456\u043b\u044c\u043a\u0456\u0441\u0442\u044c", price: "\u0426\u0456\u043d\u0430", amount: "\u0421\u0443\u043c\u0430",
    subtotal: "\u0421\u0443\u043c\u0430 \u0431\u0435\u0437 \u041f\u0414\u0412", vat: "\u041f\u0414\u0412", totalDue: "\u0412\u0441\u044c\u043e\u0433\u043e \u0434\u043e \u0441\u043f\u043b\u0430\u0442\u0438",
    confirmText: "\u0412\u0438\u0449\u0435\u0437\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0456 \u0440\u043e\u0431\u043e\u0442\u0438 (\u043f\u043e\u0441\u043b\u0443\u0433\u0438) \u0432\u0438\u043a\u043e\u043d\u0430\u043d\u0456 \u0432 \u043f\u043e\u0432\u043d\u043e\u043c\u0443 \u043e\u0431\u0441\u044f\u0437\u0456, \u0443 \u0432\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0456 \u0441\u0442\u0440\u043e\u043a\u0438 \u0442\u0430 \u0437 \u043d\u0430\u043b\u0435\u0436\u043d\u043e\u044e \u044f\u043a\u0456\u0441\u0442\u044e. \u0417\u0430\u043c\u043e\u0432\u043d\u0438\u043a \u0434\u043e \u0412\u0438\u043a\u043e\u043d\u0430\u0432\u0446\u044f \u043f\u0440\u0435\u0442\u0435\u043d\u0437\u0456\u0439 \u0449\u043e\u0434\u043e \u044f\u043a\u043e\u0441\u0442\u0456 \u0442\u0430 \u043e\u0431\u0441\u044f\u0433\u0443 \u0432\u0438\u043a\u043e\u043d\u0430\u043d\u0438\u0445 \u0440\u043e\u0431\u0456\u0442 \u043d\u0435 \u043c\u0430\u0454.",
    signaturesLabel: "\u041f\u0456\u0434\u043f\u0438\u0441\u0438 \u0441\u0442\u043e\u0440\u0456\u043d", contractor: "\u0412\u0418\u041a\u041e\u041d\u0410\u0412\u0415\u0426\u042c", customer: "\u0417\u0410\u041c\u041e\u0412\u041d\u0418\u041a",
    signatureDate: "\u041f\u0456\u0434\u043f\u0438\u0441 / \u0414\u0430\u0442\u0430", seal: "\u041f\u0435\u0447\u0430\u0442\u043a\u0430",
    introTemplate: (cn, cusn, cr) => `\u041c\u0438, \u0449\u043e \u043d\u0438\u0436\u0447\u0435 \u043f\u0456\u0434\u043f\u0438\u0441\u0430\u043b\u0438\u0441\u044f, ${cn} (\u043d\u0430\u0434\u0430\u043b\u0456 \u2014 <strong>\u0412\u0438\u043a\u043e\u043d\u0430\u0432\u0435\u0446\u044c</strong>) \u0442\u0430 ${cusn} (\u043d\u0430\u0434\u0430\u043b\u0456 \u2014 <strong>\u0417\u0430\u043c\u043e\u0432\u043d\u0438\u043a</strong>), \u0441\u043a\u043b\u0430\u043b\u0438 \u0446\u0435\u0439 \u0430\u043a\u0442 \u043f\u0440\u043e \u0442\u0435, \u0449\u043e${cr} \u0412\u0438\u043a\u043e\u043d\u0430\u0432\u0435\u0446\u044c \u0432\u0438\u043a\u043e\u043d\u0430\u0432, \u0430 \u0417\u0430\u043c\u043e\u0432\u043d\u0438\u043a \u043f\u0440\u0438\u0439\u043d\u044f\u0432 \u043d\u0430\u0441\u0442\u0443\u043f\u043d\u0456 \u0440\u043e\u0431\u043e\u0442\u0438 (\u043f\u043e\u0441\u043b\u0443\u0433\u0438):`,
    contractRefPrefix: " \u0432\u0456\u0434\u043f\u043e\u0432\u0456\u0434\u043d\u043e \u0434\u043e ", representativePrefix: ", \u0432 \u043e\u0441\u043e\u0431\u0456 ",
  },
  de: {
    title: "Abnahmeprotokoll", cityPrefix: "",
    serviceDescription: "Leistungsbeschreibung", unit: "Einh.", quantity: "Menge", price: "Preis", amount: "Betrag",
    subtotal: "Nettobetrag", vat: "MwSt.", totalDue: "Gesamtbetrag",
    confirmText: "Die oben genannten Arbeiten (Leistungen) wurden vollst\u00e4ndig, termingerecht und in angemessener Qualit\u00e4t erbracht. Der Auftraggeber hat keine Beanstandungen hinsichtlich der Qualit\u00e4t und des Umfangs der erbrachten Leistungen.",
    signaturesLabel: "Unterschriften", contractor: "AUFTRAGNEHMER", customer: "AUFTRAGGEBER",
    signatureDate: "Unterschrift / Datum", seal: "Stempel",
    introTemplate: (cn, cusn, cr) => `Wir, die Unterzeichnenden, ${cn} (nachfolgend <strong>Auftragnehmer</strong>) und ${cusn} (nachfolgend <strong>Auftraggeber</strong>), haben dieses Abnahmeprotokoll erstellt, das best\u00e4tigt, dass${cr} der Auftragnehmer die folgenden Arbeiten (Leistungen) erbracht und der Auftraggeber diese abgenommen hat:`,
    contractRefPrefix: " gem\u00e4\u00df ", representativePrefix: ", vertreten durch ",
  },
  fr: {
    title: "Proc\u00e8s-verbal de r\u00e9ception des travaux", cityPrefix: "",
    serviceDescription: "Description du service / travail", unit: "Unit\u00e9", quantity: "Qt\u00e9", price: "Prix", amount: "Montant",
    subtotal: "Sous-total (HT)", vat: "TVA", totalDue: "Total TTC",
    confirmText: "Les travaux (services) mentionn\u00e9s ci-dessus ont \u00e9t\u00e9 ex\u00e9cut\u00e9s int\u00e9gralement, dans les d\u00e9lais convenus et avec une qualit\u00e9 appropri\u00e9e. Le Client n\u2019a aucune r\u00e9clamation concernant la qualit\u00e9 et le volume des travaux r\u00e9alis\u00e9s.",
    signaturesLabel: "Signatures", contractor: "PRESTATAIRE", customer: "CLIENT",
    signatureDate: "Signature / Date", seal: "Cachet",
    introTemplate: (cn, cusn, cr) => `Nous, soussign\u00e9s, ${cn} (ci-apr\u00e8s d\u00e9nomm\u00e9 le <strong>Prestataire</strong>) et ${cusn} (ci-apr\u00e8s d\u00e9nomm\u00e9 le <strong>Client</strong>), avons \u00e9tabli le pr\u00e9sent proc\u00e8s-verbal attestant que${cr} le Prestataire a ex\u00e9cut\u00e9 et le Client a r\u00e9ceptionn\u00e9 les travaux (services) suivants\u00a0:`,
    contractRefPrefix: " conform\u00e9ment au ", representativePrefix: ", repr\u00e9sent\u00e9(e) par ",
  },
  es: {
    title: "Acta de Trabajos Realizados", cityPrefix: "",
    serviceDescription: "Descripci\u00f3n del servicio / trabajo", unit: "Unid.", quantity: "Cant.", price: "Precio", amount: "Importe",
    subtotal: "Subtotal (sin IVA)", vat: "IVA", totalDue: "Total a pagar",
    confirmText: "Los trabajos (servicios) mencionados anteriormente han sido realizados en su totalidad, dentro de los plazos acordados y con la calidad adecuada. El Cliente no tiene reclamaciones respecto a la calidad y el alcance de los trabajos realizados.",
    signaturesLabel: "Firmas", contractor: "PROVEEDOR", customer: "CLIENTE",
    signatureDate: "Firma / Fecha", seal: "Sello",
    introTemplate: (cn, cusn, cr) => `Nosotros, los abajo firmantes, ${cn} (en adelante el <strong>Proveedor</strong>) y ${cusn} (en adelante el <strong>Cliente</strong>), hemos elaborado la presente acta confirmando que${cr} el Proveedor ha realizado y el Cliente ha aceptado los siguientes trabajos (servicios):`,
    contractRefPrefix: " de conformidad con ", representativePrefix: ", representado por ",
  },
};

function getActLabels(data) {
  const lang = (data.language || "en").toLowerCase().replace(/-.*/, "");
  return ACT_I18N[lang] || ACT_I18N.en;
}

function buildActHtml(data, styling, template) {
  const s = getDefaults(styling);
  const primary = styling.primaryColor || "#0F172A";
  const accentDk = styling.accentDarkColor || "#4338CA";
  const accent = styling.accentColor || "#6366F1";
  const fontBody = s.fontHeading; // Source Serif 4
  const fontMeta = s.fontBody;    // Inter
  const currency = template?.currencySymbol || data.currencySymbol || "$";
  const grad = gradient(primary, accentDk);

  const L = getActLabels(data);

  const contractor = data.contractor || {};
  const customer = data.customer || {};
  const services = data.services || [];
  const total = data.totalAmount ?? services.reduce((sum, r) => sum + (r.total || r.quantity * r.unitPrice || 0), 0);
  const vatRate = data.vatRate ?? 0;
  const vatAmount = vatRate ? total * (vatRate / 100) : 0;

  const contractorName = formatPartyLabel(contractor, L);
  const customerName = formatPartyLabel(customer, L);
  const contractRef = data.contractRef ? `${L.contractRefPrefix}${esc(data.contractRef)},` : "";
  const introText = L.introTemplate(contractorName, customerName, contractRef);

  const serviceRows = services
    .map(
      (svc, idx) => `
    <tr style="background:${idx % 2 === 0 ? "#fff" : "rgba(0, 0, 0, 0.015)"}">
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};text-align:center;font-family:${fontMeta};font-size:11px;font-variant-numeric:tabular-lining-nums;">${idx + 1}</td>
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};">${esc(svc.description)}</td>
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};text-align:center;font-family:${fontMeta};font-size:11px;">${esc(svc.unit || "\u2014")}</td>
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};text-align:right;font-family:${fontMeta};font-size:11px;font-variant-numeric:tabular-lining-nums;">${esc(svc.quantity)}</td>
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};text-align:right;font-family:${fontMeta};font-size:11px;font-variant-numeric:tabular-lining-nums;">${formatNum(svc.unitPrice)}</td>
      <td style="padding:12px 16px;border-bottom:0.5px solid ${s.borderLight};text-align:right;font-family:${fontMeta};font-size:11px;font-weight:600;font-variant-numeric:tabular-lining-nums;">${formatNum(svc.total || svc.quantity * svc.unitPrice)}</td>
    </tr>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${s.textColor}; font-size: 12px; line-height: 1.7; text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-lining-nums; }
  .act-header { text-align: center; margin-bottom: 20px; padding-bottom: 14px; }
  .act-header-border { height: 2.5px; background: ${grad}; border-radius: 1.25px; }
  .act-title { font-family: ${fontBody}; font-size: 20px; font-weight: 700; color: ${primary}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
  .act-number { font-family: ${fontMeta}; font-size: 13px; font-weight: 600; color: ${s.textColor}; margin-bottom: 4px; }
  .act-datecity { font-family: ${fontMeta}; font-size: 11.5px; color: ${s.muted}; letter-spacing: 0.03em; }
  .intro { margin-bottom: 14px; font-size: 12px; line-height: 1.8; }
  table.services { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table.services th { background: ${grad}; color: #fff; padding: 12px 16px; text-align: left; font-family: ${fontMeta}; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
  table.services th:first-child { border-radius: 6px 0 0 0; width: 40px; text-align: center; }
  table.services th:last-child { border-radius: 0 6px 0 0; }
  table.services th:nth-child(3) { width: 50px; text-align: right; }
  table.services th:nth-child(4) { width: 80px; text-align: right; }
  table.services th:nth-child(5) { width: 90px; text-align: right; }
  table.services th:nth-child(6) { width: 90px; text-align: right; }
  .totals { margin-bottom: 16px; display: flex; flex-direction: column; align-items: flex-end; }
  .total-row { font-family: ${fontMeta}; font-size: 12px; display: flex; justify-content: space-between; width: 280px; padding: 4px 0; color: ${s.muted}; }
  .total-divider { width: 280px; height: 2px; background: ${grad}; border: none; margin: 6px 0 4px; border-radius: 1px; }
  .total-row.grand { font-size: 14px; font-weight: 700; padding: 4px 0; }
  .total-row.grand span:first-child { color: ${s.textColor}; text-transform: uppercase; letter-spacing: 0.04em; }
  .total-row.grand span:last-child { color: ${primary}; }
  .confirm-box { margin-bottom: 16px; padding: 12px 16px; background: ${s.bgLight}; border-left: 3px solid ${accent}; font-size: 12px; line-height: 1.7; }
  .section-label { font-family: ${fontMeta}; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; color: ${s.muted}; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid ${s.border}; padding-bottom: 6px; }
  .sig-grid { display: flex; gap: 40px; margin-top: 8px; page-break-inside: avoid; }
  .sig-col { flex: 1; page-break-inside: avoid; }
  .sig-party { font-family: ${fontMeta}; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: ${primary}; margin-bottom: 6px; }
  .sig-detail { font-family: ${fontMeta}; font-size: 11px; color: ${s.textColor}; line-height: 1.6; margin-bottom: 2px; }
  .sig-line { border-bottom: 0.5px solid ${s.textColor}; margin-top: 36px; }
  .sig-lbl { font-family: ${fontMeta}; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; color: ${s.muted}; margin-top: 4px; }
  .seal-line { border-bottom: 0.5px dashed ${s.border}; margin-top: 18px; }
</style></head><body>

<div class="act-header">
  <div class="act-title">${esc(L.title)}</div>
  ${data.actNumber ? `<div class="act-number">${esc(data.actNumber)}</div>` : ""}
  <div class="act-datecity">
    ${data.city ? esc(L.cityPrefix) + esc(data.city) + " &nbsp;&middot;&nbsp; " : ""}${esc(data.date)}
  </div>
  <div class="act-header-border" style="margin-top:14px;"></div>
</div>

<div class="intro">${introText}</div>

<table class="services">
  <thead>
    <tr>
      <th style="text-align:center;width:40px;">\u2116</th>
      <th>${esc(L.serviceDescription)}</th>
      <th style="text-align:right;">${esc(L.unit)}</th>
      <th style="text-align:right;">${esc(L.quantity)}</th>
      <th style="text-align:right;">${esc(L.price)}</th>
      <th style="text-align:right;">${esc(L.amount)}</th>
    </tr>
  </thead>
  <tbody>${serviceRows}</tbody>
</table>

<div class="totals">
  ${vatRate ? `<div class="total-row"><span>${esc(L.subtotal)}</span><span>${currency}${formatNum(total)}</span></div>` : ""}
  ${vatRate ? `<div class="total-row"><span>${esc(L.vat)} (${vatRate}%)</span><span>${currency}${formatNum(vatAmount)}</span></div>` : ""}
  <div class="total-divider"></div>
  <div class="total-row grand"><span>${esc(L.totalDue)}</span><span>${currency}${formatNum(total + vatAmount)}</span></div>
</div>

<div class="confirm-box">
  ${esc(L.confirmText)}
  ${data.notes ? "<br>" + esc(data.notes) : ""}
</div>

<div style="page-break-inside:avoid;">
<div class="section-label">${esc(L.signaturesLabel)}</div>
<div class="sig-grid">
  <div class="sig-col">
    <div class="sig-party">${esc(L.contractor)}</div>
    <div class="sig-detail">${esc(contractor.name)}</div>
    ${contractor.representative ? `<div class="sig-detail">${esc(contractor.representative)}${contractor.title ? ", " + esc(contractor.title) : ""}</div>` : ""}
    ${contractor.reg ? `<div class="sig-detail">${esc(contractor.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">${esc(L.signatureDate)}</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">${esc(L.seal)}</div>
  </div>
  <div class="sig-col">
    <div class="sig-party">${esc(L.customer)}</div>
    <div class="sig-detail">${esc(customer.name)}</div>
    ${customer.representative ? `<div class="sig-detail">${esc(customer.representative)}${customer.title ? ", " + esc(customer.title) : ""}</div>` : ""}
    ${customer.reg ? `<div class="sig-detail">${esc(customer.reg)}</div>` : ""}
    <div class="sig-line"></div>
    <div class="sig-lbl">${esc(L.signatureDate)}</div>
    <div class="seal-line"></div>
    <div class="sig-lbl">${esc(L.seal)}</div>
  </div>
</div>
</div>

</body></html>`;
}

// ─── NDA (Non-Disclosure Agreement) ──────────────────────────────────────────

function buildNdaHtml(data, styling, template) {
  const s = getDefaults(styling);
  const primary   = styling.primaryColor || "#0F172A";
  const textColor = styling.textColor    || "#1A1A2E";
  const muted     = styling.mutedColor   || "#4A4A5A";
  const border    = styling.borderColor  || "#D4D4D4";
  const fontBody  = s.fontHeading;
  const fontUi    = s.fontBody;

  const partiesMap = data.parties ? Object.values(data.parties) : null;
  const party1 = data.disclosingParty || data.party1 || (partiesMap && partiesMap[0]) || {};
  const party2 = data.receivingParty  || data.party2 || (partiesMap && partiesMap[1]) || {};
  const logo   = logoHtml(data);

  const ndaType = data.ndaType || "mutual";
  const typeLabel = ndaType === "mutual" ? "Mutual" : ndaType === "unilateral" ? "Unilateral" : "Mutual";

  const articleBar = (text) =>
    `<div style="background:linear-gradient(135deg,${primary},${s.accentDark || primary});color:#fff;font-family:${fontUi};font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;padding:8px 14px;margin:20px 0 14px;border-radius:4px 4px 0 0;page-break-after:avoid;">${esc(text)}</div>`;

  const sigLine = (label) => `
    <div style="margin-bottom:18px;">
      <div style="font-family:${fontBody};font-size:12px;color:${textColor};padding-bottom:22px;border-bottom:0.5px solid ${textColor};margin-bottom:3px;">${esc(label)}:</div>
    </div>`;

  const sigCol = (partyLabel, p) => {
    const partyName = (p.name || partyLabel).toUpperCase();
    return `
    <div style="flex:1;">
      <div style="font-family:${fontUi};font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:${muted};margin-bottom:6px;">${esc(partyLabel)}</div>
      <div style="font-family:${fontBody};font-size:12px;font-weight:700;color:${textColor};margin-bottom:22px;">${partyName}</div>
      ${sigLine("Signature")}
      ${sigLine("Name")}
      ${sigLine("Title")}
      ${sigLine("Date")}
    </div>`;
  };

  // Build clauses
  const defaultClauses = [
    { number: 1, title: "Definition of Confidential Information", content: data.clauses?.confidentialInfoDef || `"Confidential Information" means any and all non-public information, whether in oral, written, electronic, or other form, disclosed by ${ndaType === "mutual" ? "either party" : "the Disclosing Party"} to ${ndaType === "mutual" ? "the other party" : "the Receiving Party"}, including but not limited to: trade secrets, business plans, financial data, customer lists, technical specifications, source code, product roadmaps, marketing strategies, and any other information that is designated as confidential or that reasonably should be understood to be confidential given the nature of the information and circumstances of disclosure.` },
    { number: 2, title: `Obligations of ${ndaType === "mutual" ? "the Parties" : "the Receiving Party"}`, content: data.clauses?.obligations || `${ndaType === "mutual" ? "Each party" : "The Receiving Party"} agrees to: (a) hold Confidential Information in strict confidence using the same degree of care used to protect its own confidential information, but no less than reasonable care; (b) not disclose Confidential Information to any third party without prior written consent; (c) use Confidential Information solely for the purpose of evaluating or pursuing a business relationship between the parties (the "Purpose"); (d) limit access to Confidential Information to employees and advisors who have a need to know and who are bound by confidentiality obligations no less restrictive than those herein.` },
    { number: 3, title: "Exclusions", content: data.clauses?.exclusions || "Confidential Information shall not include information that: (a) is or becomes publicly available through no fault of the receiving party; (b) was already in the receiving party's possession prior to disclosure, as evidenced by written records; (c) is independently developed by the receiving party without reference to the Confidential Information; (d) is rightfully obtained from a third party without restriction on disclosure; or (e) is required to be disclosed by law, regulation, or court order, provided that the receiving party gives prompt written notice to allow the disclosing party to seek a protective order." },
    { number: 4, title: "Term and Duration", content: data.clauses?.term || `This Agreement shall remain in effect for a period of ${data.termYears || "two (2)"} years from the date of execution. The obligations of confidentiality shall survive termination of this Agreement for an additional period of ${data.survivalYears || "three (3)"} years.` },
    { number: 5, title: "Return of Materials", content: data.clauses?.returnMaterials || "Upon termination of this Agreement or upon written request, the receiving party shall promptly return or destroy all copies of Confidential Information in its possession, and shall certify in writing that it has done so. Notwithstanding the foregoing, the receiving party may retain one archival copy solely for legal compliance purposes, subject to the continuing confidentiality obligations herein." },
    { number: 6, title: "Remedies", content: data.clauses?.remedies || "The parties acknowledge that any breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate. Accordingly, the non-breaching party shall be entitled to seek equitable relief, including injunction and specific performance, in addition to all other remedies available at law or in equity." },
    { number: 7, title: "Governing Law", content: data.clauses?.governingLaw || `This Agreement shall be governed by and construed in accordance with the laws of ${data.jurisdiction || "the State of Delaware"}, without regard to its conflict of law provisions.` },
  ];

  const clauses = data.clauses && Array.isArray(data.clauses) ? data.clauses : defaultClauses;

  const clausesHtml = clauses.map((clause) => {
    const content = typeof clause === "string" ? clause : (clause.content || "");
    const title = clause.title || "";
    const num = clause.number || "";
    const paras = content.split(/\n+/).filter(Boolean);
    return `
    <div style="margin-bottom:4px;page-break-inside:avoid;">
      ${articleBar((num ? "Article " + num + ".  " : "") + title)}
      ${paras.map((p) => `<p style="font-family:${fontBody};font-size:12.5pt;line-height:1.5;color:${textColor};text-align:justify;-webkit-hyphens:auto;hyphens:auto;margin:0 0 10px;orphans:3;widows:3;">${esc(p)}</p>`).join("")}
    </div>`;
  }).join("\n");

  const p1Label = party1.role || (ndaType === "mutual" ? "Party A" : "Disclosing Party");
  const p2Label = party2.role || (ndaType === "mutual" ? "Party B" : "Receiving Party");

  const recital = `This ${typeLabel} Non-Disclosure Agreement (this <strong>"Agreement"</strong>) is entered into as of ${esc(data.date || "___________")}${data.city ? ` in ${esc(data.city)}` : ""} by and between <strong>${esc((party1.name || "").toUpperCase())}</strong>${party1.address ? `, with its principal place of business at ${esc(party1.address)}` : ""} (the <strong>"${esc(p1Label)}"</strong>), and <strong>${esc((party2.name || "").toUpperCase())}</strong>${party2.address ? `, with its principal place of business at ${esc(party2.address)}` : ""} (the <strong>"${esc(p2Label)}"</strong>).`;

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${fontBody}; color: ${textColor}; font-size: 12.5pt; line-height: 1.5; background: #fff; text-rendering: optimizeLegibility; }
</style></head><body>

<div style="text-align:center;padding:28px 0 12px;border-bottom:2.5px solid ${primary};margin-bottom:16px;">
  ${logo ? `<div style="margin-bottom:12px;display:flex;justify-content:center;">${logo}</div>` : ""}
  <div style="font-family:${fontUi};font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.15em;color:${s.accent};margin-bottom:8px;">${typeLabel} Non-Disclosure Agreement</div>
  <div style="font-family:${s.fontDisplay || fontBody};font-size:22px;font-weight:700;color:${primary};letter-spacing:0.04em;text-transform:uppercase;margin-bottom:8px;">
    ${esc(data.title || "Non-Disclosure Agreement")}
  </div>
  <div style="font-family:${fontUi};font-size:10px;color:${muted};letter-spacing:0.04em;">
    ${data.number ? `NDA No:&nbsp;<strong style="color:${textColor};">${esc(data.number)}</strong>&nbsp;&nbsp;&bull;&nbsp;&nbsp;` : ""}Date:&nbsp;${esc(data.date || "")}${data.city ? `&nbsp;&nbsp;&bull;&nbsp;&nbsp;${esc(data.city)}` : ""}
  </div>
</div>

<p style="font-family:${fontBody};font-size:12pt;line-height:1.55;color:${textColor};text-align:justify;margin-bottom:6px;">${recital}</p>

<p style="font-family:${fontBody};font-size:12pt;line-height:1.55;color:${textColor};text-align:justify;margin-bottom:6px;">
  <strong>WHEREAS</strong>, the parties wish to explore a potential business relationship (the <strong>"Purpose"</strong>) and, in connection therewith, may disclose certain Confidential Information to ${ndaType === "mutual" ? "each other" : "the Receiving Party"};
</p>
<p style="font-family:${fontBody};font-size:12pt;line-height:1.55;color:${textColor};text-align:justify;margin-bottom:6px;">
  <strong>NOW, THEREFORE</strong>, in consideration of the mutual covenants and agreements herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the parties agree as follows:
</p>

${clausesHtml}

<p style="font-family:${fontBody};font-size:12pt;font-style:italic;line-height:1.55;color:${textColor};margin-top:24px;margin-bottom:6px;border-top:1px solid ${border};padding-top:16px;">
  IN WITNESS WHEREOF, the parties have executed this Non-Disclosure Agreement as of the date first set forth above.
</p>

${articleBar("Signatures")}
<div style="display:flex;gap:48px;margin-top:6px;">
  ${sigCol("For " + (party1.name || p1Label) + " (" + p1Label + ")", party1)}
  ${sigCol("For " + (party2.name || p2Label) + " (" + p2Label + ")", party2)}
</div>

<div style="background:linear-gradient(135deg,${primary},${s.accentDark || primary});height:3px;margin-top:32px;border-radius:2px;"></div>

</body></html>`;
}

// ─── Estimate / Quotation ────────────────────────────────────────────────────

function buildEstimateHtml(data, styling, template) {
  const s = getDefaults(styling);
  const currency = template?.currencySymbol || styling.currencySymbol || data.currencySymbol || "$";

  const phases = data.phases || [];
  const items = data.items || [];
  const hasPhases = phases.length > 0;

  // Compute subtotal from phases or items
  let subtotal;
  if (data.subtotal != null) {
    subtotal = data.subtotal;
  } else if (hasPhases) {
    subtotal = phases.reduce((sum, ph) => {
      const tasks = ph.tasks || ph.items || [];
      return sum + tasks.reduce((ts, t) => ts + (t.amount || t.total || (t.hours || 0) * (t.rate || 0) || 0), 0);
    }, 0);
  } else {
    subtotal = items.reduce((sum, i) => sum + (i.total || i.quantity * i.unitPrice || 0), 0);
  }

  const contingency = data.contingency ?? 0;
  const tax = data.tax ?? 0;
  const discount = data.discount ?? 0;
  const total = data.total ?? (subtotal + contingency + tax - discount);

  const companyInfo = data.companyInfo || {};
  const recipient = data.recipient || data.recipientInfo || data.client || {};
  const logo = logoHtml(data);

  const validDays = data.validDays || data.validityDays || 30;
  const validUntil = data.validUntil || data.expiryDate || "";

  // Count totals for stat cards
  const totalHours = hasPhases
    ? phases.reduce((sum, ph) => sum + (ph.tasks || ph.items || []).reduce((ts, t) => ts + (t.hours || 0), 0), 0)
    : 0;
  const teamMembers = data.team ? data.team.length : 0;

  const gradient = `linear-gradient(135deg, ${s.primary}, ${s.accentDark || s.primary})`;
  const bl = s.borderLight || s.border;

  // ── Section heading helper ──
  const sectionHeading = (title) => `
    <div style="font-family:${s.fontHeading};font-size:15px;font-weight:700;color:${s.primary};margin-bottom:8px;">${esc(title)}</div>
    <div style="height:1.5px;background:linear-gradient(135deg,${s.accent},${s.accentDark || s.accent});width:60px;margin-bottom:14px;border-radius:1px;"></div>`;

  // ── 4. Project Summary Stats (phases mode only) ──
  const statsHtml = hasPhases ? `
  <div style="display:flex;gap:12px;margin-bottom:24px;">
    <div style="flex:1;border:0.5px solid ${s.border};border-radius:8px;padding:16px;text-align:center;">
      <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:6px;">Total</div>
      <div style="font-size:18px;font-weight:700;color:${s.primary};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(total)}</div>
    </div>
    <div style="flex:1;border:0.5px solid ${s.border};border-radius:8px;padding:16px;text-align:center;">
      <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:6px;">Duration</div>
      <div style="font-size:18px;font-weight:700;color:${s.primary};">${esc(data.duration || totalHours + " hrs")}</div>
    </div>
    <div style="flex:1;border:0.5px solid ${s.border};border-radius:8px;padding:16px;text-align:center;">
      <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:6px;">Team Size</div>
      <div style="font-size:18px;font-weight:700;color:${s.primary};">${teamMembers || "—"}</div>
    </div>
    <div style="flex:1;border:0.5px solid ${s.border};border-radius:8px;padding:16px;text-align:center;">
      <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:6px;">Valid Until</div>
      <div style="font-size:14px;font-weight:700;color:${s.primary};">${esc(validUntil || validDays + " days")}</div>
    </div>
  </div>` : "";

  // ── 5. Executive Summary ──
  const execSummaryHtml = data.executiveSummary ? `
  <div style="margin-bottom:24px;page-break-inside:avoid;">
    ${sectionHeading("Executive Summary")}
    <div style="background:${s.bgLight};border-radius:6px;padding:16px 18px;">
      <p style="margin:0;line-height:1.65;color:${s.textColor};font-size:13px;">${esc(data.executiveSummary)}</p>
    </div>
  </div>` : "";

  // ── 6. Scope of Work ──
  let scopeHtml = "";
  if (data.scope) {
    if (typeof data.scope === "object" && !Array.isArray(data.scope)) {
      const sc = data.scope;
      const descPart = sc.description ? `<p style="margin:0 0 14px;line-height:1.6;color:${s.textColor};font-size:13px;">${esc(sc.description)}</p>` : "";
      const inclusions = sc.inclusions || sc.included || [];
      const exclusions = sc.exclusions || sc.excluded || [];
      let gridPart = "";
      if (inclusions.length || exclusions.length) {
        gridPart = `<div style="display:flex;gap:20px;margin-bottom:14px;">`;
        if (inclusions.length) {
          gridPart += `<div style="flex:1;">
            <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:8px;">Inclusions</div>
            ${inclusions.map(item => `<div style="display:flex;align-items:baseline;gap:6px;margin-bottom:5px;font-size:12.5px;color:${s.textColor};line-height:1.5;">
              <span style="color:#22c55e;font-weight:700;flex-shrink:0;">&#10003;</span><span>${esc(typeof item === "string" ? item : item.text || item.description || "")}</span>
            </div>`).join("")}
          </div>`;
        }
        if (exclusions.length) {
          gridPart += `<div style="flex:1;">
            <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:8px;">Exclusions</div>
            ${exclusions.map(item => `<div style="display:flex;align-items:baseline;gap:6px;margin-bottom:5px;font-size:12.5px;color:${s.textColor};line-height:1.5;">
              <span style="color:#ef4444;font-weight:700;flex-shrink:0;">&#10007;</span><span>${esc(typeof item === "string" ? item : item.text || item.description || "")}</span>
            </div>`).join("")}
          </div>`;
        }
        gridPart += `</div>`;
      }
      const assumptions = sc.assumptions || [];
      const assumptionsPart = assumptions.length ? `
        <div style="background:${s.bgLight};border-left:3px solid ${s.accent};border-radius:0 4px 4px 0;padding:12px 16px;margin-top:4px;">
          <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:6px;">Assumptions</div>
          ${assumptions.map(a => `<div style="font-size:12px;color:${s.textColor};line-height:1.6;margin-bottom:3px;">&bull; ${esc(typeof a === "string" ? a : a.text || "")}</div>`).join("")}
        </div>` : "";
      scopeHtml = `
      <div style="margin-bottom:24px;page-break-inside:avoid;">
        ${sectionHeading("Scope of Work")}
        ${descPart}${gridPart}${assumptionsPart}
      </div>`;
    } else {
      // Plain string scope (backward compat)
      const scopeText = typeof data.scope === "string" ? data.scope : String(data.scope);
      scopeHtml = `
      <div style="margin-bottom:24px;page-break-inside:avoid;">
        ${sectionHeading("Scope of Work")}
        ${scopeText.split(/\n\n+/).map(p => `<p style="margin:0 0 10px;line-height:1.55;color:${s.textColor};font-size:13px;">${esc(p)}</p>`).join("")}
      </div>`;
    }
  }

  // ── 7. Team Composition ──
  const teamHtml = data.team && data.team.length ? `
  <div style="margin-bottom:24px;page-break-inside:avoid;">
    ${sectionHeading("Team Composition")}
    <div style="display:flex;flex-wrap:wrap;gap:10px;">
      ${data.team.map(m => `
        <div style="flex:1 1 calc(50% - 10px);min-width:200px;border:0.5px solid ${s.border};border-radius:8px;padding:14px 16px;">
          <div style="font-size:13px;font-weight:700;color:${s.textColor};margin-bottom:3px;">${esc(m.role || m.name || "")}</div>
          ${m.name && m.role ? `<div style="font-size:11.5px;color:${s.muted};margin-bottom:6px;">${esc(m.name)}</div>` : ""}
          <div style="display:flex;gap:16px;font-size:11px;color:${s.muted};">
            ${m.rate != null ? `<span>${currency}${formatNum(m.rate)}/hr</span>` : ""}
            ${m.allocation ? `<span>${esc(String(m.allocation))}</span>` : ""}
            ${m.hours ? `<span>${m.hours} hrs</span>` : ""}
          </div>
        </div>`).join("")}
    </div>
  </div>` : "";

  // ── 8. Pricing Table ──
  let pricingHtml = "";
  if (hasPhases) {
    // Phase-grouped table
    let rowIdx = 0;
    const phaseRows = phases.map(ph => {
      const tasks = ph.tasks || ph.items || [];
      const phColor = ph.color || s.accent;
      const phaseSubtotal = tasks.reduce((ts, t) => ts + (t.amount || t.total || (t.hours || 0) * (t.rate || 0) || 0), 0);
      const taskRows = tasks.map(t => {
        const bg = rowIdx % 2 === 0 ? "#FFFFFF" : "rgba(0,0,0,0.015)";
        rowIdx++;
        const amt = t.amount || t.total || (t.hours || 0) * (t.rate || 0) || 0;
        return `<tr style="background:${bg};">
          <td style="padding:10px 16px;border-bottom:0.5px solid ${bl};color:${s.textColor};font-size:12.5px;">${esc(t.description || t.name || "")}</td>
          <td style="padding:10px 16px;text-align:center;border-bottom:0.5px solid ${bl};color:${s.muted};font-size:12px;">${esc(t.role || "")}</td>
          <td style="padding:10px 16px;text-align:center;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;font-size:12px;">${t.hours != null ? t.hours : ""}</td>
          <td style="padding:10px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;font-size:12px;">${t.rate != null ? currency + formatNum(t.rate) : ""}</td>
          <td style="padding:10px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.textColor};font-weight:600;font-variant-numeric:tabular-lining-nums;font-size:12.5px;">${currency}${formatNum(amt)}</td>
        </tr>`;
      }).join("");
      return `<tr style="background:${phColor}10;border-left:3px solid ${phColor};">
        <td colspan="4" style="padding:10px 16px;font-weight:700;color:${s.textColor};font-size:13px;border-bottom:0.5px solid ${bl};border-left:3px solid ${phColor};">${esc(ph.name || ph.title || "Phase")}</td>
        <td style="padding:10px 16px;text-align:right;font-weight:700;color:${s.textColor};font-size:13px;border-bottom:0.5px solid ${bl};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(phaseSubtotal)}</td>
      </tr>${taskRows}`;
    }).join("");

    pricingHtml = `
    <div style="margin-bottom:4px;page-break-inside:avoid;">
      ${sectionHeading("Pricing Breakdown")}
      <table style="width:100%;border-collapse:separate;border-spacing:0;">
        <thead>
          <tr style="background:${gradient};">
            <th style="color:#FFF;padding:10px 16px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:6px 0 0 0;">Description</th>
            <th style="color:#FFF;padding:10px 16px;text-align:center;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Role</th>
            <th style="color:#FFF;padding:10px 16px;text-align:center;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Hours</th>
            <th style="color:#FFF;padding:10px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Rate</th>
            <th style="color:#FFF;padding:10px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:0 6px 0 0;">Amount</th>
          </tr>
        </thead>
        <tbody>${phaseRows}</tbody>
      </table>
    </div>`;
  } else if (items.length) {
    // Flat table (backward compat)
    const itemRows = items.map((item, idx) => `
      <tr style="background:${idx % 2 === 0 ? "#FFFFFF" : "rgba(0,0,0,0.015)"};">
        <td style="padding:12px 16px;border-bottom:0.5px solid ${bl};color:${s.textColor};">${esc(item.description)}</td>
        <td style="padding:12px 16px;text-align:center;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;">${esc(String(item.quantity))}</td>
        <td style="padding:12px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(item.unitPrice)}</td>
        <td style="padding:12px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.textColor};font-weight:600;font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(item.total || item.quantity * item.unitPrice)}</td>
      </tr>`).join("");

    pricingHtml = `
    <div style="margin-bottom:4px;page-break-inside:avoid;">
      <table style="width:100%;border-collapse:separate;border-spacing:0;">
        <thead>
          <tr style="background:${gradient};">
            <th style="color:#FFF;padding:10px 16px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:6px 0 0 0;">Description</th>
            <th style="color:#FFF;padding:10px 16px;text-align:center;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Qty</th>
            <th style="color:#FFF;padding:10px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Unit Price</th>
            <th style="color:#FFF;padding:10px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:0 6px 0 0;">Amount</th>
          </tr>
        </thead>
        <tbody>${itemRows}</tbody>
      </table>
    </div>`;
  }

  // ── 9. Optional Items ──
  const optionalHtml = data.optionalItems && data.optionalItems.length ? (() => {
    const optRows = data.optionalItems.map((item, idx) => `
      <tr style="background:${idx % 2 === 0 ? "#FFFFFF" : "rgba(0,0,0,0.015)"};">
        <td style="padding:10px 16px;border-bottom:0.5px solid ${bl};color:${s.muted};font-size:12.5px;">${esc(item.description || "")}</td>
        <td style="padding:10px 16px;text-align:center;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;font-size:12px;">${item.hours != null ? item.hours : (item.quantity != null ? item.quantity : "")}</td>
        <td style="padding:10px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.muted};font-variant-numeric:tabular-lining-nums;font-size:12px;">${item.rate != null ? currency + formatNum(item.rate) : (item.unitPrice != null ? currency + formatNum(item.unitPrice) : "")}</td>
        <td style="padding:10px 16px;text-align:right;border-bottom:0.5px solid ${bl};color:${s.muted};font-weight:600;font-variant-numeric:tabular-lining-nums;font-size:12.5px;">${currency}${formatNum(item.amount || item.total || 0)}</td>
      </tr>`).join("");
    return `
    <div style="margin:20px 0;page-break-inside:avoid;">
      ${sectionHeading("Optional Items")}
      <div style="opacity:0.85;">
        <table style="width:100%;border-collapse:separate;border-spacing:0;">
          <thead>
            <tr style="background:${s.muted};">
              <th style="color:#FFF;padding:9px 16px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:6px 0 0 0;">Description</th>
              <th style="color:#FFF;padding:9px 16px;text-align:center;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">${hasPhases ? "Hours" : "Qty"}</th>
              <th style="color:#FFF;padding:9px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;">Rate</th>
              <th style="color:#FFF;padding:9px 16px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;border-radius:0 6px 0 0;">Amount</th>
            </tr>
          </thead>
          <tbody>${optRows}</tbody>
        </table>
      </div>
      <div style="font-size:11px;color:${s.muted};font-style:italic;margin-top:6px;">* Optional items are not included in the estimated total.</div>
    </div>`;
  })() : "";

  // ── 10. Totals ──
  const totalsHtml = `
  <div style="display:flex;flex-direction:column;align-items:flex-end;padding:18px 0 22px;">
    <div style="display:flex;justify-content:space-between;width:300px;padding:5px 0;font-size:12.5px;">
      <span style="color:${s.muted};">Subtotal</span><span style="color:${s.textColor};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(subtotal)}</span>
    </div>
    ${contingency ? `<div style="display:flex;justify-content:space-between;width:300px;padding:5px 0;font-size:12.5px;">
      <span style="color:${s.muted};">Contingency</span><span style="color:${s.textColor};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(contingency)}</span>
    </div>` : ""}
    ${tax ? `<div style="display:flex;justify-content:space-between;width:300px;padding:5px 0;font-size:12.5px;">
      <span style="color:${s.muted};">Tax</span><span style="color:${s.textColor};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(tax)}</span>
    </div>` : ""}
    ${discount ? `<div style="display:flex;justify-content:space-between;width:300px;padding:5px 0;font-size:12.5px;">
      <span style="color:${s.muted};">Discount</span><span style="color:${s.textColor};font-variant-numeric:tabular-lining-nums;">&minus;${currency}${formatNum(discount)}</span>
    </div>` : ""}
    <div style="width:300px;height:2px;background:${gradient};margin:10px 0 6px;border-radius:1px;"></div>
    <div style="display:flex;justify-content:space-between;width:300px;padding:5px 0;">
      <span style="font-size:14px;font-weight:700;color:${s.textColor};text-transform:uppercase;letter-spacing:0.03em;">Estimated Total</span>
      <span style="font-size:16px;font-weight:700;color:${s.primary};font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(total)}</span>
    </div>
  </div>`;

  // ── 11. Timeline ──
  let timelineHtml = "";
  if (data.timeline) {
    if (typeof data.timeline === "object" && !Array.isArray(data.timeline)) {
      const tl = data.timeline;
      const ganttPhases = tl.phases || tl.bars || phases;
      const milestones = tl.milestones || [];
      const tlStart = tl.startDate || tl.start || "";
      const tlEnd = tl.endDate || tl.end || "";

      let ganttHtml = "";
      if (ganttPhases.length && tlStart && tlEnd) {
        const startMs = new Date(tlStart).getTime();
        const endMs = new Date(tlEnd).getTime();
        const totalMs = endMs - startMs || 1;
        ganttHtml = `<div style="position:relative;background:${s.bgLight};border-radius:6px;padding:14px 16px;margin-bottom:14px;min-height:${ganttPhases.length * 32 + 20}px;">
          ${ganttPhases.map((p, i) => {
            const pStart = new Date(p.startDate || p.start || tlStart).getTime();
            const pEnd = new Date(p.endDate || p.end || tlEnd).getTime();
            const left = Math.max(0, ((pStart - startMs) / totalMs) * 100);
            const width = Math.max(2, ((pEnd - pStart) / totalMs) * 100);
            const color = p.color || s.accent;
            return `<div style="position:absolute;top:${14 + i * 32}px;left:${16 + left * 0.92}%;width:${width * 0.92}%;height:22px;background:${color};border-radius:4px;opacity:0.85;display:flex;align-items:center;padding:0 8px;">
              <span style="font-size:9.5px;font-weight:600;color:#FFF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(p.name || p.title || "")}</span>
            </div>`;
          }).join("")}
        </div>`;
      }

      let milestoneHtml = "";
      if (milestones.length) {
        milestoneHtml = `<table style="width:100%;border-collapse:collapse;margin-top:6px;">
          <thead><tr>
            <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Milestone</th>
            <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Date</th>
            <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Description</th>
          </tr></thead>
          <tbody>${milestones.map(m => `<tr>
            <td style="padding:8px 12px;font-size:12.5px;color:${s.textColor};font-weight:600;border-bottom:0.5px solid ${bl};">&#9670; ${esc(m.name || m.title || "")}</td>
            <td style="padding:8px 12px;font-size:12px;color:${s.muted};font-variant-numeric:tabular-lining-nums;border-bottom:0.5px solid ${bl};">${esc(m.date || "")}</td>
            <td style="padding:8px 12px;font-size:12px;color:${s.muted};border-bottom:0.5px solid ${bl};">${esc(m.description || "")}</td>
          </tr>`).join("")}</tbody>
        </table>`;
      }

      timelineHtml = `
      <div style="margin:20px 0;page-break-inside:avoid;">
        ${sectionHeading("Estimated Timeline")}
        ${ganttHtml}${milestoneHtml}
      </div>`;
    } else {
      // Plain string timeline (backward compat)
      timelineHtml = `
      <div style="margin:20px 0;page-break-inside:avoid;">
        ${sectionHeading("Estimated Timeline")}
        <p style="margin:0 0 10px;line-height:1.55;color:${s.textColor};font-size:13px;">${esc(String(data.timeline))}</p>
      </div>`;
    }
  }

  // ── 12. Payment Schedule ──
  const paymentHtml = data.paymentSchedule && data.paymentSchedule.length ? (() => {
    const ps = data.paymentSchedule;
    const totalPct = ps.reduce((sum, p) => sum + (p.percentage || 0), 0) || 100;
    const barSegments = ps.map((p, i) => {
      const w = ((p.percentage || 0) / totalPct) * 100;
      const color = p.color || (phases[i] && phases[i].color) || s.accent;
      return `<div style="width:${w}%;height:24px;background:${color};display:flex;align-items:center;justify-content:center;">
        <span style="font-size:9px;font-weight:600;color:#FFF;">${p.percentage || 0}%</span>
      </div>`;
    }).join("");

    const scheduleRows = ps.map(p => `<tr>
      <td style="padding:8px 12px;font-size:12.5px;color:${s.textColor};font-weight:600;border-bottom:0.5px solid ${bl};">${esc(p.name || p.milestone || "")}</td>
      <td style="padding:8px 12px;font-size:12px;color:${s.muted};border-bottom:0.5px solid ${bl};">${p.percentage ? p.percentage + "%" : ""}</td>
      <td style="padding:8px 12px;font-size:12.5px;color:${s.textColor};font-weight:600;font-variant-numeric:tabular-lining-nums;border-bottom:0.5px solid ${bl};text-align:right;">${currency}${formatNum(p.amount || (total * (p.percentage || 0) / 100))}</td>
      <td style="padding:8px 12px;font-size:12px;color:${s.muted};border-bottom:0.5px solid ${bl};">${esc(p.trigger || p.dueDate || "")}</td>
    </tr>`).join("");

    return `
    <div style="margin:20px 0;page-break-inside:avoid;">
      ${sectionHeading("Payment Schedule")}
      <div style="display:flex;border-radius:4px;overflow:hidden;margin-bottom:12px;">${barSegments}</div>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>
          <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Milestone</th>
          <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">%</th>
          <th style="text-align:right;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Amount</th>
          <th style="text-align:left;padding:6px 12px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};border-bottom:0.5px solid ${s.border};">Trigger</th>
        </tr></thead>
        <tbody>${scheduleRows}</tbody>
      </table>
    </div>`;
  })() : "";

  // ── 14. Terms & Conditions ──
  let termsHtml = "";
  if (data.terms) {
    const termsArr = Array.isArray(data.terms) ? data.terms : (typeof data.terms === "string" ? data.terms.split(/\n\n+/) : []);
    const hasStructured = termsArr.length > 0 && typeof termsArr[0] === "object" && termsArr[0].title;
    termsHtml = `
    <div style="margin:20px 0;page-break-inside:avoid;">
      ${sectionHeading("Terms & Conditions")}
      ${hasStructured
        ? termsArr.map(t => `
          <div style="margin-bottom:12px;">
            <div style="font-size:12px;font-weight:700;color:${s.textColor};margin-bottom:3px;">${esc(t.title || "")}</div>
            <p style="margin:0;line-height:1.55;color:${s.muted};font-size:12px;">${esc(t.text || "")}</p>
          </div>`).join("")
        : termsArr.map(t => `<p style="margin:0 0 8px;line-height:1.55;color:${s.muted};font-size:12px;">${esc(typeof t === "string" ? t : t.text || "")}</p>`).join("")}
    </div>`;
  }

  // ── 15. Acceptance / Signature Block ──
  const acceptanceHtml = data.acceptance && data.acceptance.enabled ? `
  <div style="margin:24px 0;page-break-inside:avoid;">
    ${sectionHeading("Acceptance")}
    ${data.acceptance.text ? `<p style="margin:0 0 16px;line-height:1.55;color:${s.textColor};font-size:12.5px;">${esc(data.acceptance.text)}</p>` : ""}
    <div style="display:flex;gap:40px;">
      <div style="flex:1;">
        <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:30px;">Client Signature</div>
        <div style="border-bottom:1px solid ${s.border};margin-bottom:6px;"></div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:${s.muted};">
          <span>Name: _________________________</span><span>Date: _______________</span>
        </div>
      </div>
      <div style="flex:1;">
        <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:30px;">Provider Signature</div>
        <div style="border-bottom:1px solid ${s.border};margin-bottom:6px;"></div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:${s.muted};">
          <span>Name: _________________________</span><span>Date: _______________</span>
        </div>
      </div>
    </div>
  </div>` : "";

  // ── Line item count label ──
  const lineItemCount = hasPhases
    ? phases.reduce((sum, ph) => sum + (ph.tasks || ph.items || []).length, 0)
    : items.length;

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">${fontLinks()}<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ${s.fontBody}; color: ${s.textColor}; font-size: 13px; line-height: 1.55; text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-lining-nums; }
</style></head><body>

<div style="background:${gradient};height:6px;border-radius:0 0 3px 3px;"></div>

<!-- Header -->
<div style="display:flex;justify-content:space-between;align-items:flex-start;padding:24px 0 20px;border-bottom:0.5px solid ${s.border};margin-bottom:24px;">
  <div>
    ${logo}
    <div style="font-family:${s.fontHeading};font-size:22px;font-weight:700;color:${s.primary};margin-bottom:5px;letter-spacing:-0.01em;">${esc(companyInfo.name) || "Company Name"}</div>
    <div style="color:${s.muted};font-size:11.5px;line-height:1.75;">
      ${companyInfo.address ? esc(companyInfo.address) + "<br>" : ""}${companyInfo.phone ? esc(companyInfo.phone) : ""}${companyInfo.email ? " &middot; " + esc(companyInfo.email) : ""}${companyInfo.website ? "<br>" + esc(companyInfo.website) : ""}
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-family:${s.fontHeading};font-size:28px;font-weight:700;color:${s.primary};letter-spacing:-0.01em;margin-bottom:3px;">ESTIMATE</div>
    <div style="font-size:12.5px;font-weight:700;color:${s.textColor};margin-bottom:10px;">${esc(data.estimateNumber || data.quoteNumber || "")}</div>
    <div style="font-size:11.5px;line-height:2;">
      <div><span style="display:inline-block;min-width:52px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};">Date</span>&ensp;<span style="color:${s.textColor};font-weight:500;">${esc(data.date || "")}</span></div>
      ${validUntil ? `<div><span style="display:inline-block;min-width:52px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};">Valid Until</span>&ensp;<span style="color:${s.textColor};font-weight:500;">${esc(validUntil)}</span></div>` : `<div><span style="display:inline-block;min-width:52px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};">Valid For</span>&ensp;<span style="color:${s.textColor};font-weight:500;">${validDays} days</span></div>`}
      ${data.projectName ? `<div><span style="display:inline-block;min-width:52px;font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};">Project</span>&ensp;<span style="color:${s.textColor};font-weight:500;">${esc(data.projectName)}</span></div>` : ""}
    </div>
  </div>
</div>

<!-- Client Block -->
<div style="display:flex;gap:40px;margin-bottom:24px;padding-bottom:20px;border-bottom:0.5px solid ${s.border};">
  <div style="flex:1;">
    <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:5px;">Prepared For</div>
    <div style="font-size:14px;font-weight:700;color:${s.textColor};margin-bottom:3px;">${esc(recipient.name || "")}</div>
    <div style="font-size:12px;color:${s.muted};line-height:1.65;">${esc(recipient.company || "")}${recipient.company && recipient.address ? "<br>" : ""}${esc(recipient.address || "")}${recipient.email ? "<br>" + esc(recipient.email) : ""}${recipient.phone ? " &middot; " + esc(recipient.phone) : ""}</div>
  </div>
  <div style="flex:0 0 auto;text-align:right;">
    <div style="font-size:8.5px;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;color:${s.muted};margin-bottom:5px;">Estimated Total</div>
    <div style="font-size:20px;font-weight:700;color:${s.primary};margin-bottom:3px;font-variant-numeric:tabular-lining-nums;">${currency}${formatNum(total)}</div>
    <div style="font-size:12px;color:${s.muted};">${lineItemCount} line item${lineItemCount !== 1 ? "s" : ""}${hasPhases ? " &middot; " + phases.length + " phase" + (phases.length !== 1 ? "s" : "") : ""}</div>
  </div>
</div>

${statsHtml}
${execSummaryHtml}
${scopeHtml}
${teamHtml}
${pricingHtml}
${optionalHtml}
${totalsHtml}
${timelineHtml}
${paymentHtml}

<!-- Validity Notice -->
<div style="margin-top:16px;padding:10px 16px;background:${s.bgLight};border-left:3px solid ${s.accent};font-size:12px;color:${s.muted};line-height:1.6;border-radius:0 4px 4px 0;">
  This estimate is valid for <strong>${validDays} days</strong> from the date of issue${validUntil ? ` (until ${esc(validUntil)})` : ""}. Actual costs may vary based on final scope and requirements.
</div>

${termsHtml}
${acceptanceHtml}
${data.notes ? `<div style="color:${s.muted};font-size:11px;line-height:1.6;padding-top:14px;margin-top:16px;border-top:0.5px solid ${s.border};">${esc(data.notes)}</div>` : ""}

<div style="background:${gradient};height:4px;margin-top:20px;border-radius:2px 2px 0 0;"></div>

</body></html>`;
}

// ─── Universal Builder ───────────────────────────────────────────────────────

/**
 * Build HTML for any document type. Single entry point for all builders.
 */
function buildHtml(data, styling, type, template) {
  if (type === "invoice") return buildInvoiceHtml(data, styling, template);
  if (type === "estimate" || type === "quotation" || type === "quote") return buildEstimateHtml(data, styling, template);
  if (type === "contract") return buildContractHtml(data, styling, template);
  if (type === "nda") return buildNdaHtml(data, styling, template);
  if (type === "act") return buildActHtml(data, styling, template);
  if (type === "proposal" || type === "report") return buildSectionDocumentHtml(data, styling, type);
  return buildGenericHtml(data, styling);
}

// ─── Exports ─────────────────────────────────────────────────────────────────

module.exports = {
  fontLinks,
  esc,
  formatNum,
  formatPartyLabel,
  logoHtml,
  getDefaults,
  getBaseStyles,
  renderContent,
  buildCoverHtml,
  buildTocHtml,
  buildSectionsHtml,
  buildTableHtml,
  buildSectionDocumentHtml,
  buildGenericHtml,
  buildInvoiceHtml,
  buildContractHtml,
  buildNdaHtml,
  buildEstimateHtml,
  buildActHtml,
  getActLabels,
  ACT_I18N,
  buildHtml,
};
