---
name: formatting-standards
description: Typography, font, margin, color, and layout standards for professional business documents. This skill should be used when making formatting decisions, customizing fonts or colors, adjusting margins or spacing, applying branding, or choosing a color palette.
---

# Formatting Standards

Professional formatting guidelines for business documents.

## Font Standards

| Context | Font | Fallback |
|---------|------|----------|
| Business documents (proposals, reports) | Calibri | Arial, Helvetica |
| Legal documents (contracts, agreements) | Times New Roman | Georgia, serif |
| Invoices, financial | Helvetica | Arial, sans-serif |
| Presentations | Calibri | Arial, sans-serif |

## Font Size Hierarchy

### DOCX Documents

| Element | Size (pt) | Style |
|---------|-----------|-------|
| Document title | 28 | Bold, primary color |
| Heading 1 | 18 | Bold, primary color |
| Heading 2 | 14 | Bold, primary color |
| Heading 3 | 12 | Bold, dark gray |
| Body text | 11 | Regular, black |
| Footer/header | 9 | Regular, gray |
| Table header | 11 | Bold, white on primary |
| Table body | 11 | Regular |

### PDF Documents (Invoice)

Note: PDF sizes use **px** (CSS pixels) because PDFs are generated from HTML via Puppeteer. DOCX and PPTX use **pt** (points) as their native unit.

| Element | Size | Style |
|---------|------|-------|
| Invoice title | 36px | Bold, primary color |
| Company name | 24px | Bold, primary color |
| Section label | 12px | Uppercase, primary color |
| Body text | 14px | Regular |
| Small text | 11px | Gray |
| Table header | 12px | Bold, white, uppercase |

### Presentations

| Element | Size (pt) | Style |
|---------|-----------|-------|
| Slide title | 36 | Bold, white on primary |
| Subtitle | 24 | Regular, light gray |
| Body/bullets | 18 | Regular |
| Small bullets | 16 | Regular |
| Header bar text | 14 | Bold, white |
| Notes | 12 | Regular |

## Page Layout

### Margins

| Type | Top | Bottom | Left | Right |
|------|-----|--------|------|-------|
| Standard (proposals, reports) | 1" (1440 twips) | 1" | 0.75" (1080 twips) | 0.75" |
| Legal (contracts) | 1" | 1" | 1" (1440 twips) | 1" |
| Invoice (PDF) | 20mm | 20mm | 15mm | 15mm |

### Line Spacing

| Context | Spacing |
|---------|---------|
| Business documents | 1.15 |
| Legal documents | 1.5 |
| Presentations | Single (1.0) |

### Page Size

| Context | Size |
|---------|------|
| Default | A4 (210 x 297 mm) |
| US documents | Letter (8.5 x 11") |
| Presentations | Widescreen (13.33 x 7.5") |

## Color Palettes

**Default palette per document type:**

| Document Type | Default Palette | Primary Color |
|--------------|----------------|---------------|
| Proposal | Professional Blue | #003366 |
| Report | Professional Blue | #003366 |
| Invoice | Tech Blue | #2563EB |
| Presentation | Professional Blue | #003366 |
| Contract | Corporate Gray | #1F2937 |

### Professional Blue

| Element | Color | Hex |
|---------|-------|-----|
| Primary | Dark blue | #003366 |
| Secondary/Accent | Amber | #F59E0B |
| Background | White | #FFFFFF |
| Body text | Dark gray | #1F2937 |
| Secondary text | Medium gray | #6B7280 |
| Muted text | Light gray | #9CA3AF |
| Table stripe | Very light gray | #F3F4F6 |

### Corporate Gray

| Element | Color | Hex |
|---------|-------|-----|
| Primary | Charcoal | #1F2937 |
| Secondary | Blue gray | #6B7280 |
| Accent | Emerald | #10B981 |

### Tech Blue

| Element | Color | Hex |
|---------|-------|-----|
| Primary | Royal blue | #2563EB |
| Secondary | Amber | #F59E0B |
| Accent | Light blue | #3B82F6 |

## Tables

### DOCX Tables

- Header row: bold text, white color, primary background
- Alternating row colors: white / light gray (#F3F4F6)
- Cell padding: adequate spacing for readability
- Border: light gray (#E5E7EB) or none
- Full width (100%)

### PDF/HTML Tables

- Header: primary color background, white text, uppercase, letter-spacing
- Body: 14px, alternating #fff / #F8FAFC
- Cell padding: 10-12px
- Border-bottom: 1px solid #E5E7EB

## Branding Customization

When the user provides branding information:

1. **Primary color**: Apply to headings, table headers, accent elements
2. **Logo**: Place in header (top-left for docs, top-right for invoices)
3. **Company name**: Use in headers, footers, cover pages
4. **Font**: Override default fonts if specified

If no branding is provided, use the Professional Blue palette with Calibri font.

## Best Practices

- Maximum 3 colors per document (primary + secondary + neutral)
- Consistent heading hierarchy throughout
- Adequate white space between sections
- Page numbers on all multi-page documents
- Company name or document title in header/footer
- Date on every document
- Professional tone in all generated content
