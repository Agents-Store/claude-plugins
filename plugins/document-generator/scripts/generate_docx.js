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
    const { type, outputPath, data, template } = input;

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    const styling = template?.styling || {};
    const primaryColor = (styling.primaryColor || "#1E3A5F").replace("#", "");
    const accentColor = (styling.accentColor || "#2563EB").replace("#", "");
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

    if (type === "contract") {
      children = buildContract(data, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, fontHeading, fontBody, fontSizeBody);
    } else {
      children = buildDocument(data, type, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, bgLight, fontHeading, fontBody, fontSizeBody);
    }

    const margins = styling.margins || { top: 1440, bottom: 1440, left: 1080, right: 1080 };

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
    console.log(
      JSON.stringify({
        success: true,
        outputPath: path.resolve(outputPath),
        size: stats.size,
        pages: Math.max(1, Math.ceil(children.length / 25)),
      })
    );
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

function buildDocument(data, type, styling, primaryColor, accentColor, textColor, mutedColor, borderColor, bgLight, fontHeading, fontBody, fontSizeBody) {
  const children = [];
  const fontSizeTitle = (styling.fontSizeTitle || 32) * 2;
  const fontSizeH1 = (styling.fontSizeH1 || 18) * 2;
  const fontSizeH2 = (styling.fontSizeH2 || 14) * 2;

  // Cover page with visual hierarchy
  if (data.title) {
    children.push(new Paragraph({ spacing: { before: 3000 } }));

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
              children: [new TextRun({ text: h, bold: true, size: fontSizeBody * 2, color: "FFFFFF", font: fontBody })],
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
