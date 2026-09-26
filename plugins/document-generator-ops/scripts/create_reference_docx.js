#!/usr/bin/env node

/**
 * Creates assets/reference.docx — a pandoc reference template that defines
 * document styles (headings, body text, tables) matching the plugin's design system.
 *
 * Run once: node scripts/create_reference_docx.js
 */

const path = require("path");
const fs = require("fs");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  ShadingType,
} = require("docx");

async function main() {
  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: "Arial", size: 22, color: "1E293B" },
          paragraph: { spacing: { line: 312 } }, // 1.3 line spacing
        },
        heading1: {
          run: { font: "Georgia", size: 36, bold: true, color: "0F172A" },
          paragraph: {
            spacing: { before: 240, after: 120 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: "6366F1" } },
          },
        },
        heading2: {
          run: { font: "Georgia", size: 28, bold: true, color: "0F172A" },
          paragraph: { spacing: { before: 200, after: 100 } },
        },
        heading3: {
          run: { font: "Arial", size: 24, bold: true, color: "1E293B" },
          paragraph: { spacing: { before: 160, after: 80 } },
        },
        title: {
          run: { font: "Georgia", size: 56, bold: true, color: "0F172A" },
          paragraph: { spacing: { after: 200 } },
        },
        listParagraph: {
          run: { font: "Arial", size: 22, color: "1E293B" },
          paragraph: { spacing: { line: 312 } },
        },
      },
    },
    sections: [
      {
        properties: {
          page: {
            margin: { top: 1440, bottom: 1440, left: 1080, right: 1080 },
          },
        },
        children: [
          // Title
          new Paragraph({
            children: [new TextRun({ text: "Document Title", bold: true, size: 56, color: "0F172A", font: "Georgia" })],
            heading: HeadingLevel.TITLE,
          }),
          // Heading 1
          new Paragraph({
            children: [new TextRun({ text: "Heading 1", bold: true, size: 36, color: "0F172A", font: "Georgia" })],
            heading: HeadingLevel.HEADING_1,
          }),
          new Paragraph({
            children: [new TextRun({ text: "Body text in Arial 11pt with dark slate color.", size: 22, color: "1E293B", font: "Arial" })],
          }),
          // Heading 2
          new Paragraph({
            children: [new TextRun({ text: "Heading 2", bold: true, size: 28, color: "0F172A", font: "Georgia" })],
            heading: HeadingLevel.HEADING_2,
          }),
          new Paragraph({
            children: [new TextRun({ text: "More body text demonstrating the reference style.", size: 22, color: "1E293B", font: "Arial" })],
          }),
          // Heading 3
          new Paragraph({
            children: [new TextRun({ text: "Heading 3", bold: true, size: 24, color: "1E293B", font: "Arial" })],
            heading: HeadingLevel.HEADING_3,
          }),
          new Paragraph({
            children: [new TextRun({ text: "Final body paragraph.", size: 22, color: "1E293B", font: "Arial" })],
          }),
        ],
      },
    ],
  });

  const outputPath = path.resolve(__dirname, "..", "assets", "reference.docx");
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Created: ${outputPath} (${buffer.length} bytes)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
