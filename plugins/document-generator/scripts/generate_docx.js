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
  TableOfContents,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  Header,
  Footer,
  PageNumber,
  NumberFormat,
  Tab,
  TabStopType,
  TabStopPosition,
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

    const styling = template?.styling || data.branding || {};
    const primaryColor = (styling.primaryColor || "#003366").replace("#", "");
    const fontBody = styling.fontBody || styling.fontHeading || "Calibri";
    const fontSizeBody = styling.fontSizeBody || 11;
    const lineSpacing = styling.lineSpacing || 1.15;

    let children = [];

    if (type === "contract") {
      children = buildContract(data, styling, primaryColor, fontBody, fontSizeBody);
    } else {
      children = buildDocument(data, type, styling, primaryColor, fontBody, fontSizeBody);
    }

    const margins = styling.margins || { top: 1440, bottom: 1440, left: 1080, right: 1080 };

    const doc = new Document({
      styles: {
        default: {
          document: {
            run: { font: fontBody, size: fontSizeBody * 2 },
            paragraph: { spacing: { line: Math.round(lineSpacing * 240) } },
          },
        },
      },
      sections: [
        {
          properties: {
            page: {
              margin: margins,
            },
          },
          headers: data.headerText
            ? {
                default: new Header({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({ text: data.headerText, size: 18, color: "999999", font: fontBody }),
                      ],
                      alignment: AlignmentType.RIGHT,
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
                      children: [
                        new TextRun({ text: data.footer, size: 18, color: "999999", font: fontBody }),
                        new TextRun({ children: [new Tab(), "Page "] }),
                        new TextRun({ children: [PageNumber.CURRENT] }),
                        new TextRun({ children: [" of "] }),
                        new TextRun({ children: [PageNumber.TOTAL_PAGES] }),
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

function buildDocument(data, type, styling, primaryColor, fontBody, fontSizeBody) {
  const children = [];
  const fontSizeTitle = (styling.fontSizeTitle || 28) * 2;
  const fontSizeH1 = (styling.fontSizeH1 || 18) * 2;
  const fontSizeH2 = (styling.fontSizeH2 || 14) * 2;

  // Cover page
  if (data.title) {
    children.push(new Paragraph({ spacing: { before: 4000 } }));
    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: data.title,
            bold: true,
            size: fontSizeTitle,
            color: primaryColor,
            font: fontBody,
          }),
        ],
        alignment: AlignmentType.CENTER,
      })
    );

    if (data.subtitle) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: data.subtitle, size: fontSizeH1, color: "666666", font: fontBody }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { before: 200 },
        })
      );
    }

    const metaLines = [];
    if (data.author) metaLines.push(`Prepared by: ${data.author}`);
    if (data.recipient) metaLines.push(`Prepared for: ${data.recipient}`);
    if (data.date) metaLines.push(`Date: ${data.date}`);
    if (data.companyName || data.branding?.companyName) {
      metaLines.push(data.companyName || data.branding.companyName);
    }

    if (metaLines.length > 0) {
      children.push(new Paragraph({ spacing: { before: 600 } }));
      for (const line of metaLines) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: line, size: 24, color: "666666", font: fontBody })],
            alignment: AlignmentType.CENTER,
          })
        );
      }
    }

    children.push(new Paragraph({ children: [new PageBreak()] }));
  }

  // Table of Contents placeholder
  if (data.tableOfContents !== false) {
    children.push(
      new Paragraph({
        children: [
          new TextRun({ text: "Table of Contents", bold: true, size: fontSizeH1, color: primaryColor }),
        ],
      })
    );
    children.push(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }));
    children.push(new Paragraph({ children: [new PageBreak()] }));
  }

  // Sections
  if (data.sections && Array.isArray(data.sections)) {
    for (const section of data.sections) {
      const level = section.level || 1;
      const headingLevel = level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;

      children.push(
        new Paragraph({
          text: section.heading,
          heading: headingLevel,
          spacing: { before: 360, after: 120 },
        })
      );

      if (section.content) {
        const paragraphs = section.content.split("\n\n");
        for (const para of paragraphs) {
          children.push(
            new Paragraph({
              children: [new TextRun({ text: para.trim(), size: fontSizeBody * 2, font: fontBody })],
              spacing: { after: 120 },
            })
          );
        }
      }

      if (section.bullets && Array.isArray(section.bullets)) {
        for (const bullet of section.bullets) {
          children.push(
            new Paragraph({
              children: [new TextRun({ text: bullet, size: fontSizeBody * 2, font: fontBody })],
              bullet: { level: 0 },
              spacing: { after: 60 },
            })
          );
        }
      }

      if (section.table && Array.isArray(section.table)) {
        children.push(buildTable(section.table, primaryColor, fontBody, fontSizeBody));
      }

      if (section.subsections && Array.isArray(section.subsections)) {
        for (const sub of section.subsections) {
          children.push(
            new Paragraph({
              text: sub.heading,
              heading: HeadingLevel.HEADING_2,
              spacing: { before: 240, after: 120 },
            })
          );
          if (sub.content) {
            children.push(
              new Paragraph({
                children: [new TextRun({ text: sub.content, size: fontSizeBody * 2, font: fontBody })],
                spacing: { after: 120 },
              })
            );
          }
        }
      }
    }
  }

  return children;
}

function buildContract(data, styling, primaryColor, fontBody, fontSizeBody) {
  const children = [];
  const fontSize = fontSizeBody * 2;

  // Title
  children.push(
    new Paragraph({
      children: [
        new TextRun({
          text: data.title || "SERVICE AGREEMENT",
          bold: true,
          size: (styling.fontSizeTitle || 16) * 2,
          font: fontBody,
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    })
  );

  // Date and contract number
  const metaParts = [];
  if (data.contractNumber) metaParts.push(`Contract No: ${data.contractNumber}`);
  if (data.date) metaParts.push(`Date: ${data.date}`);
  if (metaParts.length > 0) {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: metaParts.join("    "), size: fontSize, font: fontBody })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
      })
    );
  }

  // Parties
  if (data.parties) {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: "PARTIES", bold: true, size: fontSize, font: fontBody })],
        spacing: { before: 200, after: 120 },
      })
    );
    for (const [key, party] of Object.entries(data.parties)) {
      const label = party.label || key;
      const details = [`${label}: ${party.name || ""}`];
      if (party.address) details.push(`Address: ${party.address}`);
      if (party.registrationNumber) details.push(`Registration No: ${party.registrationNumber}`);
      for (const line of details) {
        children.push(
          new Paragraph({
            children: [new TextRun({ text: line, size: fontSize, font: fontBody })],
            spacing: { after: 60 },
          })
        );
      }
      children.push(new Paragraph({ spacing: { after: 120 } }));
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
              font: fontBody,
            }),
          ],
          spacing: { before: 300, after: 120 },
        })
      );

      if (clause.content) {
        const paragraphs = clause.content.split("\n\n");
        let subNum = 1;
        for (const para of paragraphs) {
          children.push(
            new Paragraph({
              children: [
                new TextRun({ text: `${clauseNum}.${subNum} `, bold: true, size: fontSize, font: fontBody }),
                new TextRun({ text: para.trim(), size: fontSize, font: fontBody }),
              ],
              spacing: { after: 100 },
            })
          );
          subNum++;
        }
      }
      clauseNum++;
    }
  }

  // Signature block
  if (data.signatureBlock || data.parties) {
    children.push(new Paragraph({ spacing: { before: 600 } }));
    children.push(
      new Paragraph({
        children: [new TextRun({ text: "SIGNATURES", bold: true, size: fontSize, font: fontBody })],
        spacing: { after: 400 },
      })
    );

    const parties = data.signatureBlock
      ? Object.entries(data.signatureBlock)
      : Object.entries(data.parties || {});

    for (const [key, party] of parties) {
      const label = party.label || party.name || key;
      children.push(
        new Paragraph({
          children: [new TextRun({ text: `For ${label}:`, bold: true, size: fontSize, font: fontBody })],
          spacing: { before: 400, after: 200 },
        })
      );
      children.push(
        new Paragraph({
          children: [new TextRun({ text: "Signature: ________________________________", size: fontSize, font: fontBody })],
          spacing: { after: 120 },
        })
      );
      children.push(
        new Paragraph({
          children: [new TextRun({ text: "Name: ________________________________", size: fontSize, font: fontBody })],
          spacing: { after: 120 },
        })
      );
      children.push(
        new Paragraph({
          children: [new TextRun({ text: "Title: ________________________________", size: fontSize, font: fontBody })],
          spacing: { after: 120 },
        })
      );
      children.push(
        new Paragraph({
          children: [new TextRun({ text: "Date: ________________________________", size: fontSize, font: fontBody })],
          spacing: { after: 200 },
        })
      );
    }
  }

  return children;
}

function buildTable(tableData, primaryColor, fontBody, fontSizeBody) {
  if (!tableData || tableData.length === 0) return new Paragraph({});

  const headers = Object.keys(tableData[0]);
  const headerRow = new TableRow({
    children: headers.map(
      (h) =>
        new TableCell({
          children: [
            new Paragraph({
              children: [new TextRun({ text: h, bold: true, size: fontSizeBody * 2, color: "FFFFFF", font: fontBody })],
            }),
          ],
          shading: { fill: primaryColor },
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
                  children: [new TextRun({ text: String(row[h] || ""), size: fontSizeBody * 2, font: fontBody })],
                }),
              ],
              shading: idx % 2 === 1 ? { fill: "F3F4F6" } : undefined,
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
