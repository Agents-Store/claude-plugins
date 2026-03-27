---
name: theme-configuration
description: >
  Configure themes, CSS variables, colors, fonts, and dark mode for shadcn/ui and shadcn studio. This skill
  should be used when the user asks to "set up a theme", "customize shadcn colors", "add dark mode",
  "change shadcn theme", "use shadcn theme generator", "configure CSS variables for shadcn", "install a
  shadcn studio theme", "customize fonts", "brand colors for shadcn", or needs to design and apply visual
  themes to their shadcn/ui project.
---

## Theme System Overview

shadcn/ui themes are powered by CSS custom properties (variables) in HSL format. All components reference these variables, so changing them updates the entire UI.

Theme variables are defined in `globals.css` inside `:root` (light) and `.dark` (dark mode) blocks.

## Installing Pre-Made Themes

### From shadcn studio

```bash
npx shadcn@latest add theme-name --registry @ss-themes
```

Available themes include: Spotify, VS Code, Material Design, Pastel Dreams, GitHub, and 15+ more. The theme CLI command updates `globals.css` with the theme's CSS variables.

### From the Theme Generator

1. Visit https://shadcnstudio.com (Theme Generator section)
2. Select a pre-made theme or create custom with AI
3. Preview changes in real-time
4. Click "Copy" to get the CLI command
5. Run the copied command in your project root
6. Manually import required fonts (see Fonts section below)

## CSS Variable Structure

All color variables use HSL format without the `hsl()` wrapper:

```css
:root {
  /* Background and text */
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;

  /* Primary action color */
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;

  /* Secondary/muted elements */
  --secondary: 240 4.8% 95.9%;
  --secondary-foreground: 240 5.9% 10%;

  /* Destructive/error states */
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;

  /* Muted backgrounds and text */
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;

  /* Accent highlights */
  --accent: 240 4.8% 95.9%;
  --accent-foreground: 240 5.9% 10%;

  /* Cards and popovers */
  --card: 0 0% 100%;
  --card-foreground: 240 10% 3.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 240 10% 3.9%;

  /* Borders and inputs */
  --border: 240 5.9% 90%;
  --input: 240 5.9% 90%;
  --ring: 240 5.9% 10%;

  /* Border radius */
  --radius: 0.5rem;
}
```

## Dark Mode Setup

### Step 1: Define Dark Theme Variables

Add a `.dark` block in `globals.css`:

```css
.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  --primary: 0 0% 98%;
  --primary-foreground: 240 5.9% 10%;
  /* ... all other variables with dark values */
}
```

### Step 2: Configure Tailwind

**Tailwind v3** -- add to `tailwind.config.ts`:
```typescript
export default {
  darkMode: "class",
  // ...
}
```

**Tailwind v4** -- add to `globals.css`:
```css
@custom-variant dark (&:is(.dark *));
```

### Step 3: Install next-themes

```bash
npm install next-themes
```

### Step 4: Create Theme Provider

```typescript
// components/theme-provider.tsx
"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({ children, ...props }: React.ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
```

### Step 5: Wrap App Layout

```typescript
// app/layout.tsx
import { ThemeProvider } from "@/components/theme-provider"

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

### Step 6: Add Theme Toggle

```bash
npx shadcn@latest add button dropdown-menu
```

```typescript
// components/theme-toggle.tsx
"use client"

import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Moon, Sun } from "lucide-react"

export function ThemeToggle() {
  const { setTheme } = useTheme()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme("light")}>Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")}>Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")}>System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

## Font Configuration

### Using next/font (Recommended)

```typescript
// app/layout.tsx
import { Inter } from "next/font/google"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  )
}
```

Map the font variable in `globals.css`:

```css
@layer base {
  body {
    font-family: var(--font-sans), system-ui, sans-serif;
  }
}
```

### Theme-Specific Fonts

When installing a shadcn studio theme, check the theme's font requirements. Fonts must be manually installed via `next/font`:

```typescript
import { Geist, Geist_Mono } from "next/font/google"

const geistSans = Geist({ subsets: ["latin"], variable: "--font-sans" })
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" })
```

## Creating a Custom Brand Theme

### Step 1: Define Brand Colors in HSL

Convert your brand hex colors to HSL:
- `#1a1a2e` → `240 27% 14%` (dark navy)
- `#e94560` → `352 80% 59%` (coral accent)

### Step 2: Map to CSS Variables

```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 27% 14%;
  --primary: 352 80% 59%;
  --primary-foreground: 0 0% 100%;
  /* Map remaining variables following the pattern */
}

.dark {
  --background: 240 27% 8%;
  --foreground: 0 0% 95%;
  --primary: 352 80% 59%;
  --primary-foreground: 0 0% 100%;
}
```

### Step 3: Test Across Components

Install a few components and verify the theme looks correct:

```bash
npx shadcn@latest add button card badge alert dialog
```

Check that:
- Primary buttons use your brand color
- Cards have proper background/border contrast
- Destructive elements are clearly distinguishable
- Dark mode maintains readability

See `references/theme-variables.md` for the complete CSS variable reference and all token mappings.

## What This Skill Does NOT Cover

- Initial shadcn/ui setup -- see `setup` skill
- Component installation -- see `component-registry` skill
- Project structure decisions -- see `project-scaffolding` skill
