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
const { requirePreferences, mergePreferences } = require("./utils");

async function main() {
  try {
    const inputPath = process.argv[2];
    if (!inputPath) throw new Error("Usage: node generate_pptx.js <input.json>");

    const raw = fs.readFileSync(inputPath, "utf-8");
    const input = JSON.parse(raw);
    const { outputPath, data, template } = input;

    // Check preferences (soft — does not block generation)
    const prefsCheck = requirePreferences(input);

    // Auto-merge user preferences (style, company info, logo) into input
    mergePreferences(input);

    if (!outputPath) throw new Error("outputPath is required");
    if (!data) throw new Error("data is required");

    const PptxGenJS = require("pptxgenjs");
    const pptx = new PptxGenJS();

    const styling = template?.styling || data.branding || {};
    const primary = (styling.primaryColor || "#0F172A").replace("#", "");
    const accent = (styling.accentColor || "#6366F1").replace("#", "");
    const secondary = (styling.secondaryColor || "#64748B").replace("#", "");
    const bgColor = (styling.backgroundColor || "#FFFFFF").replace("#", "");
    const textColor = (styling.textColor || "#1E293B").replace("#", "");
    const fontBody = styling.fontFamily || "Arial";
    const fontHeading = styling.fontHeading || "Georgia";
    const titleFontSize = styling.titleFontSize || 40;
    const bodyFontSize = styling.bodyFontSize || 18;

    pptx.layout = "LAYOUT_WIDE";
    pptx.author = data.author || "Document Generator";
    pptx.title = data.title || "Presentation";

    // Master slide with navy header bar + accent line
    pptx.defineSlideMaster({
      title: "CONTENT_SLIDE",
      background: { color: bgColor },
      objects: [
        { rect: { x: 0, y: 0, w: "100%", h: 0.75, fill: { color: primary } } },
        { rect: { x: 0, y: 0.75, w: "100%", h: 0.04, fill: { color: accent } } },
        { rect: { x: 0, y: 7.2, w: "100%", h: 0.02, fill: { color: "E2E8F0" } } },
      ],
    });

    const ctx = { pptx, primary, accent, secondary, bgColor, textColor, fontBody, fontHeading, titleFontSize, bodyFontSize };
    const slides = data.slides || [];

    for (const slideData of slides) {
      switch (slideData.type) {
        case "title": addTitleSlide(ctx, slideData, data); break;
        case "agenda": addAgendaSlide(ctx, slideData); break;
        case "content": addContentSlide(ctx, slideData); break;
        case "two-column": addTwoColumnSlide(ctx, slideData); break;
        case "chart": addChartSlide(ctx, slideData); break;
        case "summary": addSummarySlide(ctx, slideData); break;
        case "contact": addContactSlide(ctx, slideData); break;
        default: addContentSlide(ctx, slideData);
      }
    }

    if (slides.length === 0) {
      addTitleSlide(ctx, { title: data.title, subtitle: data.subtitle }, data);
    }

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    await pptx.writeFile({ fileName: outputPath });

    const stats = fs.statSync(outputPath);
    const result = { success: true, outputPath: path.resolve(outputPath), size: stats.size, slides: Math.max(slides.length, 1) };
    if (!prefsCheck.exists) result.warning = prefsCheck.warning;
    console.log(JSON.stringify(result));
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

function addTitleSlide(ctx, slideData, data) {
  const slide = ctx.pptx.addSlide();
  slide.background = { color: ctx.primary };

  // Accent stripe at bottom
  slide.addShape(ctx.pptx.ShapeType.rect, { x: 0, y: 6.8, w: "100%", h: 0.06, fill: { color: ctx.accent } });

  slide.addText(slideData.title || data.title || "Presentation", {
    x: 1.0, y: 1.2, w: 11.3, h: 2.5,
    fontSize: ctx.titleFontSize,
    fontFace: ctx.fontHeading,
    color: "FFFFFF",
    bold: true,
    align: "left",
    valign: "bottom",
  });

  // Accent line under title
  slide.addShape(ctx.pptx.ShapeType.rect, { x: 1.0, y: 3.8, w: 1.5, h: 0.06, fill: { color: ctx.accent } });

  if (slideData.subtitle || data.subtitle) {
    slide.addText(slideData.subtitle || data.subtitle, {
      x: 1.0, y: 4.0, w: 11.3, h: 1.0,
      fontSize: 20,
      fontFace: ctx.fontBody,
      color: "94A3B8",
      align: "left",
    });
  }

  const metaParts = [];
  if (data.author) metaParts.push(data.author);
  if (data.date || slideData.date) metaParts.push(data.date || slideData.date);
  if (metaParts.length > 0) {
    slide.addText(metaParts.join("  |  "), {
      x: 1.0, y: 5.8, w: 11.3, h: 0.5,
      fontSize: 13,
      fontFace: ctx.fontBody,
      color: "64748B",
      align: "left",
    });
  }
}

function addAgendaSlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "Agenda", {
    x: 0.6, y: 0.12, w: "90%", h: 0.55,
    fontSize: 16, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true,
  });

  const items = slideData.items || [];

  // Numbered items with accent color numbers
  let yPos = 1.2;
  for (let i = 0; i < items.length; i++) {
    slide.addText(String(i + 1).padStart(2, "0"), {
      x: 0.8, y: yPos, w: 0.8, h: 0.6,
      fontSize: 24, fontFace: ctx.fontBody, color: ctx.accent, bold: true,
    });
    slide.addText(items[i], {
      x: 1.7, y: yPos + 0.05, w: 10, h: 0.5,
      fontSize: ctx.bodyFontSize, fontFace: ctx.fontBody, color: ctx.textColor,
    });
    // Subtle divider
    if (i < items.length - 1) {
      slide.addShape(ctx.pptx.ShapeType.rect, { x: 0.8, y: yPos + 0.65, w: 11, h: 0.01, fill: { color: "E2E8F0" } });
    }
    yPos += 0.75;
  }
}

function addContentSlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "", {
    x: 0.6, y: 0.12, w: "90%", h: 0.55,
    fontSize: 16, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true,
  });

  if (slideData.bullets && Array.isArray(slideData.bullets)) {
    const bulletItems = slideData.bullets.map((b) => ({
      text: b,
      options: {
        fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor,
        bullet: { type: "bullet", color: ctx.accent },
        breakLine: true, paraSpaceAfter: 10,
      },
    }));

    const textWidth = slideData.image ? 6.5 : 11.5;
    slide.addText(bulletItems, { x: 0.8, y: 1.2, w: textWidth, h: 5.3, valign: "top" });
  } else if (slideData.content) {
    const textWidth = slideData.image ? 6.5 : 11.5;
    slide.addText(slideData.content, {
      x: 0.8, y: 1.2, w: textWidth, h: 5.3,
      fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor, valign: "top", lineSpacing: 24,
    });
  }

  if (slideData.image && fs.existsSync(slideData.image)) {
    slide.addImage({ path: slideData.image, x: 8, y: 1.2, w: 4.5, h: 4.5 });
  }

  if (slideData.notes) slide.addNotes(slideData.notes);
}

function addTwoColumnSlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "", {
    x: 0.6, y: 0.12, w: "90%", h: 0.55,
    fontSize: 16, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true,
  });

  // Left column with accent border
  slide.addShape(ctx.pptx.ShapeType.rect, { x: 0.5, y: 1.1, w: 0.04, h: 5.0, fill: { color: ctx.accent } });
  const leftItems = (slideData.leftColumn || slideData.left || []).map((b) => ({
    text: b,
    options: { fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor, bullet: { type: "bullet", color: ctx.accent }, breakLine: true, paraSpaceAfter: 10 },
  }));
  slide.addText(leftItems, { x: 0.8, y: 1.1, w: 5.5, h: 5.2, valign: "top" });

  // Right column with secondary border
  slide.addShape(ctx.pptx.ShapeType.rect, { x: 6.7, y: 1.1, w: 0.04, h: 5.0, fill: { color: ctx.secondary } });
  const rightItems = (slideData.rightColumn || slideData.right || []).map((b) => ({
    text: b,
    options: { fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor, bullet: { type: "bullet", color: ctx.secondary }, breakLine: true, paraSpaceAfter: 10 },
  }));
  slide.addText(rightItems, { x: 7.0, y: 1.1, w: 5.5, h: 5.2, valign: "top" });
}

function addChartSlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "", {
    x: 0.6, y: 0.12, w: "90%", h: 0.55,
    fontSize: 16, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true,
  });

  if (slideData.chartData) {
    const chartType = slideData.chartType || "bar";
    const pptxChartType = chartType === "pie" ? ctx.pptx.ChartType.pie : chartType === "line" ? ctx.pptx.ChartType.line : ctx.pptx.ChartType.bar;

    slide.addChart(pptxChartType, slideData.chartData, {
      x: 1, y: 1.2, w: 11, h: 5.2,
      showTitle: false, showValue: true,
      chartColors: [ctx.accent, "F59E0B", "10B981", "EF4444", "8B5CF6"],
      border: { pt: 0 },
    });
  } else {
    slide.addText("Chart data not provided", {
      x: 1, y: 3, w: 11, h: 1,
      fontSize: ctx.bodyFontSize, fontFace: ctx.fontBody, color: "94A3B8", align: "center",
    });
  }

  if (slideData.notes) slide.addNotes(slideData.notes);
}

function addSummarySlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide({ masterName: "CONTENT_SLIDE" });

  slide.addText(slideData.title || "Summary", {
    x: 0.6, y: 0.12, w: "90%", h: 0.55,
    fontSize: 16, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true,
  });

  // Key takeaways box
  if (slideData.keyPoints && Array.isArray(slideData.keyPoints)) {
    slide.addShape(ctx.pptx.ShapeType.rect, { x: 0.5, y: 1.0, w: 5.8, h: 5.5, fill: { color: "F8FAFC" }, rectRadius: 0.1 });
    slide.addShape(ctx.pptx.ShapeType.rect, { x: 0.5, y: 1.0, w: 5.8, h: 0.06, fill: { color: ctx.accent } });

    slide.addText("Key Takeaways", {
      x: 0.8, y: 1.2, w: 5.2, h: 0.5,
      fontSize: ctx.bodyFontSize, fontFace: ctx.fontHeading, color: ctx.primary, bold: true,
    });

    const keyItems = slideData.keyPoints.map((p) => ({
      text: p,
      options: { fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor, bullet: { type: "bullet", color: ctx.accent }, breakLine: true, paraSpaceAfter: 10 },
    }));
    slide.addText(keyItems, { x: 1.0, y: 1.8, w: 5.0, h: 4.2, valign: "top" });
  }

  // Next steps box
  if (slideData.nextSteps && Array.isArray(slideData.nextSteps)) {
    slide.addShape(ctx.pptx.ShapeType.rect, { x: 6.8, y: 1.0, w: 5.8, h: 5.5, fill: { color: "F8FAFC" }, rectRadius: 0.1 });
    slide.addShape(ctx.pptx.ShapeType.rect, { x: 6.8, y: 1.0, w: 5.8, h: 0.06, fill: { color: "F59E0B" } });

    slide.addText("Next Steps", {
      x: 7.1, y: 1.2, w: 5.2, h: 0.5,
      fontSize: ctx.bodyFontSize, fontFace: ctx.fontHeading, color: ctx.primary, bold: true,
    });

    const nextItems = slideData.nextSteps.map((s, idx) => ({
      text: `${idx + 1}. ${s}`,
      options: { fontSize: ctx.bodyFontSize - 2, fontFace: ctx.fontBody, color: ctx.textColor, bullet: false, breakLine: true, paraSpaceAfter: 10 },
    }));
    slide.addText(nextItems, { x: 7.3, y: 1.8, w: 5.0, h: 4.2, valign: "top" });
  }
}

function addContactSlide(ctx, slideData) {
  const slide = ctx.pptx.addSlide();
  slide.background = { color: ctx.primary };

  slide.addShape(ctx.pptx.ShapeType.rect, { x: 0, y: 6.8, w: "100%", h: 0.06, fill: { color: ctx.accent } });

  slide.addText("Thank You", {
    x: 1.0, y: 1.5, w: 11.3, h: 1.5,
    fontSize: 44, fontFace: ctx.fontHeading, color: "FFFFFF", bold: true, align: "left",
  });

  slide.addShape(ctx.pptx.ShapeType.rect, { x: 1.0, y: 3.1, w: 1.5, h: 0.06, fill: { color: ctx.accent } });

  const contactLines = [];
  if (slideData.name) contactLines.push({ text: slideData.name, options: { fontSize: 20, fontFace: ctx.fontBody, color: "FFFFFF", bold: true, breakLine: true, paraSpaceAfter: 6 } });
  if (slideData.email) contactLines.push({ text: slideData.email, options: { fontSize: 16, fontFace: ctx.fontBody, color: "94A3B8", breakLine: true, paraSpaceAfter: 4 } });
  if (slideData.phone) contactLines.push({ text: slideData.phone, options: { fontSize: 16, fontFace: ctx.fontBody, color: "94A3B8", breakLine: true, paraSpaceAfter: 4 } });
  if (slideData.website) contactLines.push({ text: slideData.website, options: { fontSize: 16, fontFace: ctx.fontBody, color: ctx.accent, breakLine: true, paraSpaceAfter: 4 } });

  if (contactLines.length > 0) {
    slide.addText(contactLines, { x: 1.0, y: 3.5, w: 11.3, h: 2.5 });
  }
}

main();
