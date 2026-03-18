#!/usr/bin/env node

/**
 * PPTX Presentation Generator
 * Generates professional PowerPoint presentations using pptxgenjs.
 *
 * Usage: node generate_pptx.js <input.json>
 * Input: JSON file with presentation data
 * Output: JSON to stdout { success, outputPath } or { success: false, error }
 */

const fs = require("fs");
const path = require("path");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) throw new Error("Usage: node generate_pptx.js <input.json>");

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);
    const { outputPath, data, template } = input;

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    const PptxGenJS = require("pptxgenjs");
    const pptx = new PptxGenJS();

    const styling = template?.styling || data.branding || {};
    const primaryColor = styling.primaryColor || "003366";
    const secondaryColor = styling.secondaryColor || "F59E0B";
    const bgColor = styling.backgroundColor || "FFFFFF";
    const fontFamily = styling.fontFamily || "Calibri";
    const titleFontSize = styling.titleFontSize || 36;
    const bodyFontSize = styling.bodyFontSize || 18;

    pptx.layout = "LAYOUT_WIDE";
    pptx.author = data.author || "Document Generator";
    pptx.title = data.title || "Presentation";

    // Define master slides
    pptx.defineSlideMaster({
      title: "CONTENT_SLIDE",
      background: { color: bgColor },
      objects: [
        {
          rect: { x: 0, y: 0, w: "100%", h: 0.6, fill: { color: primaryColor.replace("#", "") } },
        },
      ],
    });

    const slides = data.slides || [];

    for (const slideData of slides) {
      switch (slideData.type) {
        case "title":
          addTitleSlide(pptx, slideData, data, primaryColor, secondaryColor, fontFamily, titleFontSize);
          break;
        case "agenda":
          addAgendaSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
          break;
        case "content":
          addContentSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
          break;
        case "two-column":
          addTwoColumnSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
          break;
        case "chart":
          addChartSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
          break;
        case "summary":
          addSummarySlide(pptx, slideData, primaryColor, secondaryColor, fontFamily, bodyFontSize);
          break;
        case "contact":
          addContactSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
          break;
        default:
          addContentSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize);
      }
    }

    // If no slides were provided, create a basic title slide
    if (slides.length === 0) {
      addTitleSlide(pptx, { title: data.title, subtitle: data.subtitle }, data, primaryColor, secondaryColor, fontFamily, titleFontSize);
    }

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    await pptx.writeFile({ fileName: outputPath });

    const stats = fs.statSync(outputPath);
    console.log(
      JSON.stringify({
        success: true,
        outputPath: path.resolve(outputPath),
        size: stats.size,
        slides: Math.max(slides.length, 1),
      })
    );
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

function addTitleSlide(pptx, slideData, data, primaryColor, secondaryColor, fontFamily, titleFontSize) {
  const slide = pptx.addSlide();
  const pc = primaryColor.replace("#", "");

  slide.background = { color: pc };

  slide.addText(slideData.title || data.title || "Presentation", {
    x: 0.5,
    y: 1.5,
    w: "90%",
    h: 2,
    fontSize: titleFontSize,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
    align: "center",
    valign: "middle",
  });

  if (slideData.subtitle || data.subtitle) {
    slide.addText(slideData.subtitle || data.subtitle, {
      x: 0.5,
      y: 3.5,
      w: "90%",
      h: 1,
      fontSize: 20,
      fontFace: fontFamily,
      color: "CCCCCC",
      align: "center",
    });
  }

  const metaParts = [];
  if (data.author) metaParts.push(data.author);
  if (data.date || slideData.date) metaParts.push(data.date || slideData.date);
  if (metaParts.length > 0) {
    slide.addText(metaParts.join(" | "), {
      x: 0.5,
      y: 5.0,
      w: "90%",
      h: 0.5,
      fontSize: 14,
      fontFace: fontFamily,
      color: "AAAAAA",
      align: "center",
    });
  }
}

function addAgendaSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  const pc = primaryColor.replace("#", "");

  slide.addText(slideData.title || "Agenda", {
    x: 0.5,
    y: 0.1,
    w: "90%",
    h: 0.5,
    fontSize: 14,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
  });

  const items = slideData.items || [];
  const bulletItems = items.map((item, idx) => ({
    text: `${idx + 1}. ${item}`,
    options: { fontSize: bodyFontSize, fontFace: fontFamily, color: "333333", bullet: false, breakLine: true, paraSpaceAfter: 12 },
  }));

  slide.addText(bulletItems, { x: 1, y: 1.2, w: 11, h: 5, valign: "top" });
}

function addContentSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  const pc = primaryColor.replace("#", "");

  slide.addText(slideData.title || "", {
    x: 0.5,
    y: 0.1,
    w: "90%",
    h: 0.5,
    fontSize: 14,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
  });

  if (slideData.bullets && Array.isArray(slideData.bullets)) {
    const bulletItems = slideData.bullets.map((b) => ({
      text: b,
      options: { fontSize: bodyFontSize - 2, fontFace: fontFamily, color: "333333", bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 8 },
    }));

    const textWidth = slideData.image ? 6.5 : 11;
    slide.addText(bulletItems, { x: 0.8, y: 1.0, w: textWidth, h: 5.5, valign: "top" });
  } else if (slideData.content) {
    const textWidth = slideData.image ? 6.5 : 11;
    slide.addText(slideData.content, {
      x: 0.8,
      y: 1.0,
      w: textWidth,
      h: 5.5,
      fontSize: bodyFontSize - 2,
      fontFace: fontFamily,
      color: "333333",
      valign: "top",
    });
  }

  if (slideData.image && fs.existsSync(slideData.image)) {
    slide.addImage({ path: slideData.image, x: 8, y: 1.2, w: 4.5, h: 4.5 });
  }

  if (slideData.notes) {
    slide.addNotes(slideData.notes);
  }
}

function addTwoColumnSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "", {
    x: 0.5,
    y: 0.1,
    w: "90%",
    h: 0.5,
    fontSize: 14,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
  });

  const leftItems = (slideData.leftColumn || slideData.left || []).map((b) => ({
    text: b,
    options: { fontSize: bodyFontSize - 2, fontFace: fontFamily, color: "333333", bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 8 },
  }));

  const rightItems = (slideData.rightColumn || slideData.right || []).map((b) => ({
    text: b,
    options: { fontSize: bodyFontSize - 2, fontFace: fontFamily, color: "333333", bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 8 },
  }));

  slide.addText(leftItems, { x: 0.5, y: 1.0, w: 5.8, h: 5.5, valign: "top" });
  slide.addText(rightItems, { x: 6.8, y: 1.0, w: 5.8, h: 5.5, valign: "top" });
}

function addChartSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "", {
    x: 0.5,
    y: 0.1,
    w: "90%",
    h: 0.5,
    fontSize: 14,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
  });

  if (slideData.chartData) {
    const chartType = slideData.chartType || "bar";
    const pptxChartType = chartType === "pie" ? pptx.ChartType.pie : chartType === "line" ? pptx.ChartType.line : pptx.ChartType.bar;

    slide.addChart(pptxChartType, slideData.chartData, {
      x: 1,
      y: 1.2,
      w: 11,
      h: 5,
      showTitle: false,
      showValue: true,
      chartColors: [primaryColor.replace("#", ""), "F59E0B", "10B981", "EF4444", "8B5CF6"],
    });
  } else {
    slide.addText("Chart data not provided", {
      x: 1,
      y: 3,
      w: 11,
      h: 1,
      fontSize: bodyFontSize,
      fontFace: fontFamily,
      color: "999999",
      align: "center",
    });
  }

  if (slideData.notes) slide.addNotes(slideData.notes);
}

function addSummarySlide(pptx, slideData, primaryColor, secondaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  const pc = primaryColor.replace("#", "");

  slide.addText(slideData.title || "Summary", {
    x: 0.5,
    y: 0.1,
    w: "90%",
    h: 0.5,
    fontSize: 14,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
  });

  if (slideData.keyPoints && Array.isArray(slideData.keyPoints)) {
    slide.addText("Key Takeaways", {
      x: 0.5,
      y: 1.0,
      w: 5.8,
      h: 0.5,
      fontSize: bodyFontSize,
      fontFace: fontFamily,
      color: pc,
      bold: true,
    });

    const keyItems = slideData.keyPoints.map((p) => ({
      text: p,
      options: { fontSize: bodyFontSize - 2, fontFace: fontFamily, color: "333333", bullet: { type: "bullet" }, breakLine: true, paraSpaceAfter: 8 },
    }));
    slide.addText(keyItems, { x: 0.8, y: 1.6, w: 5.5, h: 4.5, valign: "top" });
  }

  if (slideData.nextSteps && Array.isArray(slideData.nextSteps)) {
    slide.addText("Next Steps", {
      x: 6.8,
      y: 1.0,
      w: 5.8,
      h: 0.5,
      fontSize: bodyFontSize,
      fontFace: fontFamily,
      color: secondaryColor.replace("#", ""),
      bold: true,
    });

    const nextItems = slideData.nextSteps.map((s, idx) => ({
      text: `${idx + 1}. ${s}`,
      options: { fontSize: bodyFontSize - 2, fontFace: fontFamily, color: "333333", bullet: false, breakLine: true, paraSpaceAfter: 8 },
    }));
    slide.addText(nextItems, { x: 7.0, y: 1.6, w: 5.5, h: 4.5, valign: "top" });
  }
}

function addContactSlide(pptx, slideData, primaryColor, fontFamily, bodyFontSize) {
  const slide = pptx.addSlide();
  const pc = primaryColor.replace("#", "");
  slide.background = { color: pc };

  slide.addText("Thank You", {
    x: 0.5,
    y: 1.5,
    w: "90%",
    h: 1.5,
    fontSize: 36,
    fontFace: fontFamily,
    color: "FFFFFF",
    bold: true,
    align: "center",
  });

  const contactLines = [];
  if (slideData.name) contactLines.push(slideData.name);
  if (slideData.email) contactLines.push(slideData.email);
  if (slideData.phone) contactLines.push(slideData.phone);
  if (slideData.website) contactLines.push(slideData.website);

  if (contactLines.length > 0) {
    const contactItems = contactLines.map((line) => ({
      text: line,
      options: { fontSize: 18, fontFace: fontFamily, color: "CCCCCC", breakLine: true, paraSpaceAfter: 8 },
    }));
    slide.addText(contactItems, { x: 0.5, y: 3.5, w: "90%", h: 2, align: "center" });
  }
}

main();
