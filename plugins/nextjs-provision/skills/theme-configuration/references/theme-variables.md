# CSS Variable Reference

Complete reference for shadcn/ui theme CSS custom properties.

## Variable Categories

### Background & Text

| Variable | Purpose | Typical Light | Typical Dark |
|----------|---------|---------------|--------------|
| `--background` | Page background | `0 0% 100%` (white) | `240 10% 3.9%` (near-black) |
| `--foreground` | Default text color | `240 10% 3.9%` | `0 0% 98%` |

### Primary Colors

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--primary` | Primary action color | Buttons, links, active states |
| `--primary-foreground` | Text on primary backgrounds | Button text, badge text |

### Secondary Colors

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--secondary` | Secondary action color | Secondary buttons, less prominent actions |
| `--secondary-foreground` | Text on secondary backgrounds | Secondary button text |

### Destructive Colors

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--destructive` | Error/danger color | Delete buttons, error messages |
| `--destructive-foreground` | Text on destructive backgrounds | Error button text |

### Muted Colors

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--muted` | Subtle background | Muted sections, disabled areas |
| `--muted-foreground` | Subtle text | Placeholder text, secondary labels |

### Accent Colors

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--accent` | Highlight/accent | Hover states, selected items |
| `--accent-foreground` | Text on accent backgrounds | Hover text |

### Card & Popover

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--card` | Card background | Card containers |
| `--card-foreground` | Card text | Text inside cards |
| `--popover` | Popover/dropdown background | Menus, tooltips, dialogs |
| `--popover-foreground` | Popover text | Text in popovers |

### Borders & Inputs

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--border` | Default border color | Card borders, dividers |
| `--input` | Input border color | Form input borders |
| `--ring` | Focus ring color | Focus indicators on interactive elements |

### Layout

| Variable | Purpose | Usage |
|----------|---------|-------|
| `--radius` | Border radius | Applied to all components (default `0.5rem`) |

### Chart Colors

| Variable | Purpose |
|----------|---------|
| `--chart-1` | First chart color (series 1) |
| `--chart-2` | Second chart color (series 2) |
| `--chart-3` | Third chart color (series 3) |
| `--chart-4` | Fourth chart color (series 4) |
| `--chart-5` | Fifth chart color (series 5) |

### Sidebar Colors (if using sidebar component)

| Variable | Purpose |
|----------|---------|
| `--sidebar-background` | Sidebar background |
| `--sidebar-foreground` | Sidebar text |
| `--sidebar-primary` | Active sidebar item |
| `--sidebar-primary-foreground` | Active item text |
| `--sidebar-accent` | Hover sidebar item |
| `--sidebar-accent-foreground` | Hover item text |
| `--sidebar-border` | Sidebar borders |
| `--sidebar-ring` | Sidebar focus ring |

## HSL Format

All color values use raw HSL numbers without the `hsl()` wrapper:

```css
/* Correct: */
--primary: 240 5.9% 10%;

/* Incorrect: */
--primary: hsl(240, 5.9%, 10%);
```

Components reference them with `hsl()`:
```css
.button {
  background-color: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}
```

## Color Token Hierarchy

```
Background (page) → Card (container) → Popover (overlay)
     ↓                    ↓                    ↓
 Foreground          Card-foreground      Popover-foreground

Primary → Used for main CTAs, active navigation, links
Secondary → Used for secondary actions, less emphasis
Muted → Used for disabled, subtle backgrounds, placeholder text
Accent → Used for hover states, highlights
Destructive → Used for errors, deletions, warnings

Border → Dividers, card edges, separators
Input → Form field borders (often same as border)
Ring → Focus indicators (often matches primary)
```

## Pre-Built Theme Presets

### Neutral (Default)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --secondary: 240 4.8% 95.9%;
  --muted: 240 4.8% 95.9%;
  --accent: 240 4.8% 95.9%;
  --destructive: 0 84.2% 60.2%;
  --border: 240 5.9% 90%;
  --radius: 0.5rem;
}
```

### Slate
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --secondary: 210 40% 96.1%;
  --muted: 210 40% 96.1%;
  --accent: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;
  --border: 214.3 31.8% 91.4%;
  --radius: 0.5rem;
}
```

### Stone
```css
:root {
  --background: 0 0% 100%;
  --foreground: 20 14.3% 4.1%;
  --primary: 24 9.8% 10%;
  --secondary: 60 4.8% 95.9%;
  --muted: 60 4.8% 95.9%;
  --accent: 60 4.8% 95.9%;
  --destructive: 0 84.2% 60.2%;
  --border: 20 5.9% 90%;
  --radius: 0.5rem;
}
```

### Zinc
```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --secondary: 240 4.8% 95.9%;
  --muted: 240 4.8% 95.9%;
  --accent: 240 4.8% 95.9%;
  --destructive: 0 84.2% 60.2%;
  --border: 240 5.9% 90%;
  --radius: 0.5rem;
}
```

## Creating Custom Colors

### Hex to HSL Conversion

To convert brand colors to HSL for CSS variables:

| Hex | HSL | Variable Assignment |
|-----|-----|---------------------|
| `#000000` | `0 0% 0%` | Pure black |
| `#ffffff` | `0 0% 100%` | Pure white |
| `#3b82f6` | `217 91% 60%` | Blue |
| `#ef4444` | `0 84% 60%` | Red |
| `#22c55e` | `142 71% 45%` | Green |
| `#f59e0b` | `38 92% 50%` | Amber |
| `#8b5cf6` | `258 90% 66%` | Violet |

### Contrast Guidelines

For accessibility, ensure sufficient contrast between background and foreground pairs:

| Pair | Minimum Contrast (WCAG AA) |
|------|---------------------------|
| `--background` / `--foreground` | 4.5:1 for normal text |
| `--primary` / `--primary-foreground` | 4.5:1 for button text |
| `--card` / `--card-foreground` | 4.5:1 for card text |
| `--muted` / `--muted-foreground` | 3:1 for large text/UI |
| `--destructive` / `--destructive-foreground` | 4.5:1 for error text |

### Generating a Color Scale

For a primary color of `217 91% 60%` (blue):

```css
/* Lighter variants */
--primary-50: 217 91% 97%;
--primary-100: 217 91% 93%;
--primary-200: 217 91% 85%;
--primary-300: 217 91% 75%;

/* Base */
--primary: 217 91% 60%;

/* Darker variants */
--primary-600: 217 91% 50%;
--primary-700: 217 91% 40%;
--primary-800: 217 91% 30%;
--primary-900: 217 91% 20%;
```

Note: shadcn/ui's default theme system uses a simpler two-tone approach (primary + primary-foreground) rather than full color scales. Extend with custom variables only if your design requires it.
