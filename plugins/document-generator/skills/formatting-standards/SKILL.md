---
name: formatting-standards
description: Typography, font, margin, color, and layout standards for professional business documents. This skill should be used when making formatting decisions, customizing fonts or colors, adjusting margins or spacing, applying branding, or choosing a color palette.
---

# Formatting Standards

Professional formatting guidelines based on industry best practices. Follows the **60-30-10 color rule** (60% background, 30% structure, 10% accent) and an **8px spacing grid**.

## Font System

### Font Pairing

Fonts differ by output format — DOCX/PPTX use system fonts; PDF uses embedded Inter + PT Serif (Cyrillic+Latin, offline).

#### DOCX / PPTX — System Fonts

| Context | Headings | Body Text |
|---------|----------|-----------|
| Proposals, Reports | **Georgia** (serif) | Arial (sans-serif) |
| Presentations | **Georgia** (serif) | Arial (sans-serif) |
| Contracts, Legal | **Georgia** (serif) | Georgia (serif) |

Georgia and Arial are pre-installed on macOS and Windows — no embedding needed.

#### PDF — Embedded Fonts (Inter + PT Serif)

Loaded from `scripts/fonts.js`. Works fully offline. Supports Ukrainian and English.

| Context | Headings | Body Text |
|---------|----------|-----------|
| Invoices | **PT Serif** | Inter |
| Contracts (PDF) | **PT Serif** | PT Serif |
| Acts / Акти | **PT Serif** | PT Serif + Inter (meta labels) |
| Reports, Proposals (PDF) | **PT Serif** | Inter |

PT Serif was designed for Cyrillic+Latin — ideal for Ukrainian documents. Inter provides clean readability for body text.

### Font Size Hierarchy

#### DOCX Documents (sizes in pt)

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Document title | 32 | Bold | Primary (#1E3A5F) |
| Heading 1 | 18 | Bold | Primary (#1E3A5F) |
| Heading 2 | 14 | Bold | Primary (#1E3A5F) |
| Heading 3 | 12 | Bold | Text (#1E293B) |
| Body text | 11 | Regular | Text (#1E293B) |
| Meta/footer | 8-9 | Regular/Italic | Muted (#64748B) |
| Table header | 11 | Bold | White on Primary |
| Table body | 11 | Regular | Text (#1E293B) |

#### PDF Documents (sizes in px — CSS pixels via Puppeteer)

Note: PDF uses **px** (CSS pixels) because documents are rendered from HTML. DOCX and PPTX use **pt** as their native unit.

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Invoice title (INVOICE) | 32px | Bold | Primary |
| Company name | 22px | Bold | Primary |
| Section label | 10-11px | Uppercase, 700 | Muted |
| Body text | 13px | Regular | Text |
| Small/notes | 11px | Regular | Muted |
| Table header | 11px | Bold, uppercase | White |

#### Presentations (sizes in pt)

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Slide title (title slide) | 40 | Bold | White |
| Slide header bar | 16 | Bold | White on Primary |
| Subtitle | 20-22 | Regular | Muted (#94A3B8) |
| Body/bullets | 16-18 | Regular | Text (#1E293B) |
| Agenda numbers | 24 | Bold | Accent (#2563EB) |
| Meta/author | 13 | Regular | Muted |

## Color System

### Primary Palette — Corporate Blue

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Primary** | Navy | `#1E3A5F` | Headings, header bars, title slide bg |
| **Accent** | Bright blue | `#2563EB` | Accent lines, bullet colors, links |
| **Background** | Cool gray | `#F8FAFC` | Alternating sections, card backgrounds |
| **Text** | Dark slate | `#1E293B` | Body text |
| **Muted** | Slate gray | `#64748B` | Secondary text, meta, captions |
| **Border** | Light border | `#E2E8F0` | Dividers, table borders |
| **Highlight** | Light blue | `#EFF6FF` | Payment cards, callout boxes |

### Default Palette by Document Type

| Document Type | Default Palette | Primary | Accent |
|--------------|----------------|---------|--------|
| Proposal | Corporate Blue | #1E3A5F | #2563EB |
| Report | Corporate Blue | #1E3A5F | #2563EB |
| Invoice | Corporate Blue | #1E3A5F | #2563EB |
| Presentation | Corporate Blue | #1E3A5F | #2563EB |
| Contract | Dark Slate | #1E293B | #1E3A5F |

### Color Application (60-30-10 Rule)

- **60%** Background: White (#FFFFFF) and light gray (#F8FAFC)
- **30%** Structure: Navy (#1E3A5F) for headers, headings, table headers
- **10%** Accent: Bright blue (#2563EB) for lines, bullet colors, links, highlights

## Layout & Spacing

### Spacing Grid (8px base)

Use multiples of 8px: 8, 16, 24, 32, 48, 64px for all spacing values.

| Context | Before | After |
|---------|--------|-------|
| H1 heading | 48px (480 twips) | 6px + accent line |
| H2 heading | 32px (320 twips) | 12px (120 twips) |
| Body paragraph | — | 16px (160 twips) |
| Bullet item | — | 8px (80 twips) |
| Section gap | 32px | 32px |
| Cover page title spacer | 300px (3000 twips) | — |

### Margins

| Type | Top | Bottom | Left | Right |
|------|-----|--------|------|-------|
| Proposals, Reports | 1" (1440 twips) | 1" | 0.75" (1080 twips) | 0.75" |
| Contracts | 1" | 1" | 1" (1440 twips) | 1" |
| Invoice PDF | 20mm | 20mm | 18mm | 18mm |

### Line Spacing

| Context | Spacing |
|---------|---------|
| Business documents (proposals, reports) | 1.3 |
| Legal documents (contracts) | 1.5 |
| Presentations | Single (1.0) |

## Visual Design Techniques

### Color Blocking

- **Top/bottom bars**: 4-6px colored bars at page edges (navy primary)
- **Header bars**: Full-width navy background with white text (presentations, invoices)
- **Accent underlines**: 3-4px accent blue lines under H1 headings
- **Card backgrounds**: Light gray (#F8FAFC) with left accent border (4px blue)
- **Alternating rows**: White / #F8FAFC for table rows and sections

### Cover Pages (DOCX)

1. Large spacer (pushes title to center-upper area)
2. Accent line (6px blue) above title
3. Title in Georgia Bold, left-aligned, primary color
4. Subtitle in body font, muted color
5. Meta block (author, recipient, date) in small muted text
6. Page break

### Invoice Layout (PDF)

1. Top accent bar (6px navy)
2. Header: company info left, "INVOICE" right in Georgia
3. Info cards with left accent borders (Bill To, Summary)
4. Items table with navy header row
5. Totals box with navy "Total Due" row
6. Payment details in light blue card (#EFF6FF)
7. Bottom accent bar (4px navy)

### Presentation Slides

1. Master slide: navy header bar (0.75") + accent line (0.04")
2. Title slide: full navy background, accent stripe, left-aligned
3. Agenda: numbered items with accent-colored numbers + dividers
4. Content: accent-colored bullet points
5. Two-column: accent/secondary left border lines
6. Summary: two card boxes with top accent stripe
7. Contact: navy background with accent stripe

## Branding Customization

When the user provides branding:
1. **Primary color** → replaces #1E3A5F in headers, bars, headings
2. **Accent color** → replaces #2563EB in lines, bullets, highlights
3. **Logo** → placed in header area
4. **Company name** → header and footer
5. **Font override** → replaces Georgia/Arial if specified

If no branding is provided, use the Corporate Blue palette with Georgia + Arial.

## Anti-Patterns (What Makes Documents Look Primitive)

- More than 3 colors in a document
- Centered body text (use left-aligned)
- Thick borders on tables (use 1px or none)
- No visual hierarchy (all same size/weight)
- Dense text without white space
- Default system fonts without pairing (e.g., plain Calibri everywhere)
- Missing accent elements (no lines, bars, or color blocks)
