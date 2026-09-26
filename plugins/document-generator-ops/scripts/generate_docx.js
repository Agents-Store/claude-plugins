#!/usr/bin/env node

/**
 * DOCX Document Generator
 * Generates professional DOCX documents (proposals, reports, contracts)
 * using the docx (docx-js) library.
 *
 * Usage: node generate_docx.js <input.json>
 * Input: JSON file with document data
 * Output: JSON to stdout { success, outputPath } or { success: false, error }
 */

const fs = require("fs");
const path = require("path");
const { requirePreferences, mergePreferences, normalizeMargins } = require("./utils");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  PageBreak,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  Header,
  Footer,
  PageNumber,
  Tab,
  TabStopType,
  TabStopPosition,
  ShadingType,
} = require("docx");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) {
      throw new Error("Usage: node generate_docx.js <input.json>");
    }

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);
    const { type, engine, outputPath, data, template } = input;

    // Check preferences (soft — does not block generation)
    const prefsCheck = requirePreferences(input);

    // Auto-merge user preferences (style, company info, logo) into input
    mergePreferences(input);

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    // ── Pandoc engine: generate HTML → DOCX via pandoc for unified styling ──
    if (engine === "pandoc") {
      await generateWithPandoc(type, outputPath, data, template);
      return;
    }

    const styling = template?.styling || {};
    const primaryColor = (styling.primaryColor || "#0F172A").replace("#", "");
    const accentColor = (styling.accentColor || "#6366F1").replace("#", "");
    const textColor = (styling.textColor || "#1E293B").replace("#", "");
    const mutedColor = (styling.mutedColor || "#64748B").replace("#", "");
    const borderColor = (styling.borderColor || "#E2E8F0").replace("#", "");
    const bgLight = (styling.backgroundColor || "#F8FAFC").replace("#", "");
    const fontHeading = styling.fontHeading || "Georgia";
    const fontBody = styling.fontBody || styling.fontBodyFallback || "Arial";
    const fontSizeBody = styling.fontSizeBody || 11;
    const lineSpacing = styling.lineSpacing || 1.3;

    // Substitute template placeholders in header/footer text
    const subs = {
      title: data.title || "",
      date: data.date || "",
      companyName: data.companyName || "",
      author: data.author || "",
    };
    const fillPlaceholders = (str) => str ? str.replace(/\{\{(\w+)\}\}/g, (_, k) => subs[k] ?? _) : str;
    if (data.headerText) data.headerText = fillPlaceholders(data.headerText);
    if (data.footer) data.footer = fillPlaceholders(data.footer);

    let children = [];

    // Pass template section definitions so buildDocument can normalize object-style sections
    if (template?.structure?.sections && Array.isArray(template.structure.sections)) {
      data._templateSections = template.structure.sections;
    }

    // Also use template header/footer if data doesn't have them
    if (!data.headerText && template?.headerText) data.headerText = fillPlaceholders(template.headerText);
    if (!data.footer && template?.footer) data.footer = fillPlaceholders(template.footer);

    if (type === "contract") {
      children = buildContract(data, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, fontHeading, fontBody, fontSizeBody);
    } else {
      children = buildDocument(data, type, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, bgLight, fontHeading, fontBody, fontSizeBody);
    }

    const margins = normalizeMargins(styling.margins, "docx");

    const doc = new Document({
      styles: {
        default: {
          document: {
            run: { font: fontBody, size: fontSizeBody * 2, color: textColor },
            paragraph: { spacing: { line: Math.round(lineSpacing * 240) } },
          },
        },
      },
      sections: [
        {
          properties: { page: { margin: margins } },
          headers: data.headerText
            ? {
                default: new Header({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({ text: data.headerText, size: 16, color: mutedColor, font: fontBody, italics: true }),
                      ],
                      alignment: AlignmentType.RIGHT,
                      border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor } },
                      spacing: { after: 120 },
                    }),
                  ],
                }),
              }
            : undefined,
          footers: data.footer
            ? {
                default: new Footer({
                  children: [
                    new Paragraph({
                      border: { top: { style: BorderStyle.SINGLE, size: 1, color: borderColor } },
                      spacing: { before: 120 },
                      children: [
                        new TextRun({ text: data.footer, size: 16, color: mutedColor, font: fontBody }),
                        new TextRun({ children: [new Tab()] }),
                        new TextRun({ text: "Page ", size: 16, color: mutedColor, font: fontBody }),
                        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: mutedColor, font: fontBody }),
                        new TextRun({ text: " of ", size: 16, color: mutedColor, font: fontBody }),
                        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: mutedColor, font: fontBody }),
                      ],
                      tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
                    }),
                  ],
                }),
              }
            : undefined,
          children,
        },
      ],
    });

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);

    const stats = fs.statSync(outputPath);
    const result = {
      success: true,
      outputPath: path.resolve(outputPath),
      size: stats.size,
      pages: Math.max(1, Math.ceil(children.length / 25)),
    };
    if (!prefsCheck.exists) result.warning = prefsCheck.warning;
    console.log(JSON.stringify(result));
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

// ─── Pandoc Engine ──────────────────────────────────────────────────────────
// Generates HTML using the shared html_templates module (same as PDF output),
// then converts to DOCX via pandoc for unified styling across formats.

async function generateWithPandoc(type, outputPath, data, template) {
  const { execSync } = require("child_process");
  const os = require("os");
  const { buildHtml } = require("./html_templates");

  // Check pandoc is available
  try {
    execSync("which pandoc", { encoding: "utf-8" });
  } catch (_) {
    throw new Error(
      "pandoc is not installed (needed for engine: pandoc). " +
      "Install with: brew install pandoc (macOS) or apt install pandoc (Linux). " +
      "Alternatively, remove engine: pandoc from the input to use docx-js."
    );
  }

  const styling = template?.styling || {};

  // Build HTML using the same shared templates as the PDF generator — all types supported
  const html = buildHtml(data, styling, type, template);

  // Write HTML to temp file
  const tmpHtml = path.join(os.tmpdir(), `docgen_${Date.now()}.html`);
  fs.writeFileSync(tmpHtml, html, "utf-8");

  // Check for reference doc
  const pluginDir = path.resolve(__dirname, "..");
  const refDoc = path.join(pluginDir, "assets", "reference.docx");
  const refArg = fs.existsSync(refDoc) ? ` --reference-doc="${refDoc}"` : "";

  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  try {
    execSync(
      `pandoc "${tmpHtml}" -f html -t docx${refArg} -o "${outputPath}"`,
      { encoding: "utf-8", timeout: 30000 }
    );
  } finally {
    try { fs.unlinkSync(tmpHtml); } catch (_) {}
  }

  const stats = fs.statSync(outputPath);
  console.log(
    JSON.stringify({
      success: true,
      outputPath: path.resolve(outputPath),
      size: stats.size,
      engine: "pandoc",
    })
  );
  process.exit(0);
}

function buildDocument(data, type, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, bgLight, fontHeading, fontBody, fontSizeBody) {
  const children = [];
  const fontSizeTitle = (styling.fontSizeTitle || 32) * 2;
  const fontSizeH1 = (styling.fontSizeH1 || 18) * 2;
  const fontSizeH2 = (styling.fontSizeH2 || 14) * 2;

  // Normalize sections: if data.sections is an object (keyed by section id),
  // convert it to an array using template structure for headings and order.
  if (data.sections && !Array.isArray(data.sections)) {
    const sectionData = data.sections;
    const templateSections = data._templateSections || [];
    const normalized = [];
    for (const tmpl of templateSections) {
      const value = sectionData[tmpl.id];
      if (value !== undefined && value !== null) {
        normalized.push({
          heading: tmpl.heading,
          level: tmpl.level || 1,
          content: typeof value === "string" ? value : undefined,
          items: Array.isArray(value) ? value : undefined,
        });
      }
    }
    // Also include any sections in data that aren't in the template
    for (const [key, value] of Object.entries(sectionData)) {
      if (!templateSections.find((t) => t.id === key)) {
        const heading = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        normalized.push({
          heading,
          level: 1,
          content: typeof value === "string" ? value : undefined,
          items: Array.isArray(value) ? value : undefined,
        });
      }
    }
    data.sections = normalized;
  }

  // Cover page with visual hierarchy
  if (data.title) {
    // Company logo on cover page (if available)
    const logoBase64 = data.companyInfo?.logoBase64 || data.logoBase64;
    if (logoBase64) {
      try {
        const { ImageRun } = require("docx");
        const logoBuffer = Buffer.from(logoBase64, "base64");
        children.push(new Paragraph({ spacing: { before: 1200 } }));
        children.push(
          new Paragraph({
            children: [
              new ImageRun({
                data: logoBuffer,
                transformation: { width: 160, height: 56 },
                type: "png",
              }),
            ],
            spacing: { after: 400 },
          })
        );
        children.push(new Paragraph({ spacing: { before: 600 } }));
      } catch (_) {
        // If logo fails, continue without it
        children.push(new Paragraph({ spacing: { before: 3000 } }));
      }
    } else {
      children.push(new Paragraph({ spacing: { before: 3000 } }));
    }

    // Accent line before title
    children.push(
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: accentColor } },
        spacing: { after: 300 },
      })
    );

    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: data.title,
            bold: true,
            size: fontSizeTitle,
            color: primaryColor,
            font: fontHeading,
          }),
        ],
        alignment: AlignmentType.LEFT,
        spacing: { after: 200 },
      })
    );

    if (data.subtitle) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: data.subtitle, size: fontSizeH1, color: mutedColor, font: fontBody }),
          ],
          spacing: { after: 400 },
        })
      );
    }

    const metaLines = [];
    if (data.author) metaLines.push(`Prepared by  ${data.author}`);
    if (data.recipient) metaLines.push(`Prepared for  ${data.recipient}`);
    if (data.date) metaLines.push(data.date);
    if (data.companyName) {
      metaLines.push(data.companyName);
    }

    if (metaLines.length > 0) {
      children.push(new Paragraph({ spacing: { before: 200 } }));
      for (const line of metaLines) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: line, size: 22, color: mutedColor, font: fontBody })],
            spacing: { after: 80 },
          })
        );
      }
    }

    children.push(new Paragraph({ children: [new PageBreak()] }));
  }

  // Table of Contents — built manually from sections so it renders correctly without Word field update
  if (data.tableOfContents !== false && data.sections && data.sections.length > 0) {
    children.push(
      new Paragraph({
        children: [
          new TextRun({ text: "Contents", bold: true, size: fontSizeH1, color: primaryColor, font: fontHeading }),
        ],
        spacing: { after: 240 },
      })
    );
    for (const section of data.sections) {
      const level = section.level || 1;
      const indent = level === 1 ? 0 : level === 2 ? 360 : 720;
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: section.heading || section.title || "",
              size: level === 1 ? 24 : 22,
              color: level === 1 ? primaryColor : textColor,
              font: level === 1 ? fontHeading : fontBody,
              bold: level === 1,
            }),
          ],
          indent: { left: indent },
          spacing: { after: level === 1 ? 100 : 60 },
        })
      );
    }
    children.push(new Paragraph({ children: [new PageBreak()] }));
  }

  // Sections with accent underline
  if (data.sections && Array.isArray(data.sections)) {
    for (const section of data.sections) {
      const level = section.level || 1;
      const headingLevel = level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;

      // Section heading with accent underline for H1
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: section.heading,
              bold: true,
              size: level === 1 ? fontSizeH1 : fontSizeH2,
              color: primaryColor,
              font: fontHeading,
            }),
          ],
          heading: headingLevel,
          spacing: { before: 480, after: level === 1 ? 60 : 120 },
        })
      );

      // Accent line under H1 headings
      if (level === 1) {
        children.push(
          new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: accentColor } },
            spacing: { after: 200 },
          })
        );
      }

      if (section.content) {
        const paragraphs = section.content.split("\n\n");
        for (const para of paragraphs) {
          children.push(
            new Paragraph({
              children: [new TextRun({ text: para.trim(), size: fontSizeBody * 2, font: fontBody, color: textColor })],
              spacing: { after: 160 },
            })
          );
        }
      }

      if (section.bullets && Array.isArray(section.bullets)) {
        for (const bullet of section.bullets) {
          children.push(
            new Paragraph({
              children: [new TextRun({ text: bullet, size: fontSizeBody * 2, font: fontBody, color: textColor })],
              bullet: { level: 0 },
              spacing: { after: 80 },
            })
          );
        }
      }

      // Render array items as either a table or structured list (timeline, pricing, etc.)
      if (section.items && Array.isArray(section.items)) {
        for (const item of section.items) {
          if (typeof item === "object" && item !== null) {
            // Timeline-style items (phase + duration + description)
            if (item.phase || item.duration) {
              const label = [item.phase, item.duration ? `(${item.duration})` : ""].filter(Boolean).join(" ");
              children.push(
                new Paragraph({
                  children: [new TextRun({ text: label, bold: true, size: fontSizeBody * 2, font: fontBody, color: primaryColor })],
                  spacing: { before: 160, after: 60 },
                })
              );
              if (item.description) {
                children.push(
                  new Paragraph({
                    children: [new TextRun({ text: item.description, size: fontSizeBody * 2, font: fontBody, color: textColor })],
                    spacing: { after: 120 },
                  })
                );
              }
            }
            // Pricing-style items (item + amount)
            else if (item.item !== undefined && item.amount !== undefined) {
              children.push(
                new Paragraph({
                  children: [
                    new TextRun({ text: `${item.item}`, size: fontSizeBody * 2, font: fontBody, color: textColor }),
                    new TextRun({ text: `    $${Number(item.amount).toLocaleString()}`, bold: true, size: fontSizeBody * 2, font: fontBody, color: primaryColor }),
                  ],
                  spacing: { after: 80 },
                  bullet: { level: 0 },
                })
              );
            }
            // Generic object — render as key-value
            else {
              const text = Object.entries(item).map(([k, v]) => `${k}: ${v}`).join(" | ");
              children.push(
                new Paragraph({
                  children: [new TextRun({ text, size: fontSizeBody * 2, font: fontBody, color: textColor })],
                  spacing: { after: 80 },
                  bullet: { level: 0 },
                })
              );
            }
          }
        }
        // Add total line for pricing arrays
        const totalAmount = section.items.reduce((sum, i) => sum + (Number(i.amount) || 0), 0);
        if (totalAmount > 0) {
          children.push(
            new Paragraph({
              border: { top: { style: BorderStyle.SINGLE, size: 2, color: primaryColor } },
              children: [
                new TextRun({ text: `Total: $${totalAmount.toLocaleString()}`, bold: true, size: (fontSizeBody + 2) * 2, font: fontBody, color: primaryColor }),
              ],
              spacing: { before: 160, after: 200 },
              alignment: AlignmentType.RIGHT,
            })
          );
        }
      }

      if (section.table && Array.isArray(section.table)) {
        children.push(new Paragraph({ spacing: { before: 120 } }));
        children.push(buildTable(section.table, primaryColor, accentColor, textColor, bgLight, borderColor, fontBody, fontSizeBody));
        children.push(new Paragraph({ spacing: { after: 120 } }));
      }

      if (section.subsections && Array.isArray(section.subsections)) {
        for (const sub of section.subsections) {
          children.push(
            new Paragraph({
              children: [
                new TextRun({ text: sub.heading, bold: true, size: fontSizeH2, color: primaryColor, font: fontHeading }),
              ],
              heading: HeadingLevel.HEADING_2,
              spacing: { before: 320, after: 120 },
            })
          );
          if (sub.content) {
            children.push(
              new Paragraph({
                children: [new TextRun({ text: sub.content, size: fontSizeBody * 2, font: fontBody, color: textColor })],
                spacing: { after: 160 },
              })
            );
          }
        }
      }
    }
  }

  return children;
}

function buildContract(data, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, fontHeading, fontBody, fontSizeBody) {
  const children = [];
  const fontSize = fontSizeBody * 2;

  // Normalize party1/party2 and parties object into a unified map
  const partiesMap = data.parties
    ? data.parties
    : data.party1 || data.party2
      ? { party1: data.party1 || {}, party2: data.party2 || {} }
      : null;

  // Title with line
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: data.title || "SERVICE AGREEMENT",
          bold: true,
          size: (styling.fontSizeTitle || 18) * 2,
          font: fontHeading,
          color: primaryColor,
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
    })
  );
  children.push(
    new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: primaryColor } },
      spacing: { after: 300 },
    })
  );

  // Date and contract number
  const metaParts = [];
  if (data.contractNumber) metaParts.push(`Contract No: ${data.contractNumber}`);
  if (data.date) metaParts.push(`Date: ${data.date}`);
  if (metaParts.length > 0) {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: metaParts.join("    |    "), size: fontSize, font: fontBody, color: mutedColor })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
      })
    );
  }

  // Parties
  if (partiesMap) {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: "PARTIES", bold: true, size: 24, font: fontHeading, color: primaryColor })],
        spacing: { before: 200, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor } },
      })
    );
    for (const [key, party] of Object.entries(partiesMap)) {
      const label = party.role || party.label || key;
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: `${label}: `, bold: true, size: fontSize, font: fontBody, color: primaryColor }),
            new TextRun({ text: party.name || "", size: fontSize, font: fontBody, color: textColor }),
          ],
          spacing: { before: 120, after: 40 },
        })
      );
      if (party.address) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: `Address: ${party.address}`, size: fontSize, font: fontBody, color: mutedColor })],
            spacing: { after: 40 },
          })
        );
      }
      if (party.reg) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: `Registration No: ${party.reg}`, size: fontSize, font: fontBody, color: mutedColor })],
            spacing: { after: 120 },
          })
        );
      }
    }
  }

  // Clauses
  if (data.clauses && Array.isArray(data.clauses)) {
    let clauseNum = 1;
    for (const clause of data.clauses) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `${clauseNum}. ${clause.title}`,
              bold: true,
              size: (styling.fontSizeClauseTitle || 12) * 2,
              font: fontHeading,
              color: primaryColor,
            }),
          ],
          spacing: { before: 360, after: 80 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor } },
        })
      );

      if (clause.content) {
        const paragraphs = clause.content.split("\n\n");
        let subNum = 1;
        for (const para of paragraphs) {
          children.push(
            new Paragraph({
              children: [
                new TextRun({ text: `${clauseNum}.${subNum} `, bold: true, size: fontSize, font: fontBody, color: mutedColor }),
                new TextRun({ text: para.trim(), size: fontSize, font: fontBody, color: textColor }),
              ],
              spacing: { after: 120 },
            })
          );
          subNum++;
        }
      }
      clauseNum++;
    }
  }

  // Signature block
  if (data.signatureBlock || partiesMap) {
    children.push(new Paragraph({ spacing: { before: 600 } }));
    children.push(
      new Paragraph({
        children: [new TextRun({ text: "SIGNATURES", bold: true, size: 24, font: fontHeading, color: primaryColor })],
        spacing: { after: 80 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor } },
      })
    );

    const parties = data.signatureBlock
      ? Object.entries(data.signatureBlock)
      : Object.entries(partiesMap || {});

    for (const [key, party] of parties) {
      const label = party.role || party.label || party.name || key;
      children.push(
        new Paragraph({
          children: [new TextRun({ text: `For ${label}:`, bold: true, size: fontSize, font: fontBody, color: primaryColor })],
          spacing: { before: 400, after: 240 },
        })
      );
      const sigFields = ["Signature", "Name", "Title", "Date"];
      for (const field of sigFields) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: `${field}: `, bold: true, size: fontSize, font: fontBody, color: mutedColor }), new TextRun({ text: "________________________________", size: fontSize, font: fontBody, color: borderColor })],
            spacing: { after: 120 },
          })
        );
      }
    }
  }

  return children;
}

function buildTable(tableData, primaryColor, accentColor, textColor, bgLight, borderColor, fontBody, fontSizeBody) {
  if (!tableData || tableData.length === 0) return new Paragraph({});

  const headers = Object.keys(tableData[0]);
  const headerRow = new TableRow({
    children: headers.map(
      (h) =>
        new TableCell({
          children: [
            new Paragraph({
              children: [new TextRun({ text: h.toUpperCase(), bold: true, size: fontSizeBody * 2, color: "FFFFFF", font: fontBody, characterSpacing: 40 })],
              spacing: { before: 60, after: 60 },
            }),
          ],
          shading: { fill: primaryColor, type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 80, right: 80 },
        })
    ),
    tableHeader: true,
  });

  const dataRows = tableData.map(
    (row, idx) =>
      new TableRow({
        children: headers.map(
          (h) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [new TextRun({ text: String(row[h] || ""), size: fontSizeBody * 2, font: fontBody, color: textColor })],
                  spacing: { before: 40, after: 40 },
                }),
              ],
              shading: idx % 2 === 1 ? { fill: bgLight, type: ShadingType.CLEAR } : undefined,
              margins: { top: 40, bottom: 40, left: 80, right: 80 },
            })
        ),
      })
  );

  return new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}

main();
