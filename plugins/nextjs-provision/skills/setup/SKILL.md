---
name: setup
description: >
  Set up shadcn/ui and shadcn studio in a Next.js project. This skill should be used when the user asks to
  "set up shadcn", "install shadcn/ui", "initialize shadcn", "configure shadcn studio", "add shadcn to my
  project", "set up component library", "init shadcn in next.js", or needs to initialize a Next.js project
  for shadcn/ui component development.
---

## Prerequisites Check

Before initializing shadcn/ui, verify the project meets these requirements:

| Requirement | Check | Minimum |
|-------------|-------|---------|
| Node.js | `node --version` | 18.17+ (20+ for Tailwind v4) |
| Next.js | `package.json` → `next` | 13+ with App Router |
| React | `package.json` → `react` | 18+ |
| TypeScript | `tsconfig.json` exists | Recommended |
| Tailwind CSS | `package.json` → `tailwindcss` | 3.x or 4.x |

If Tailwind CSS is not installed:

```bash
# For new projects, create-next-app includes Tailwind by default:
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir

# For existing projects without Tailwind:
npm install -D tailwindcss @tailwindcss/postcss postcss
```

## Step 1: Initialize shadcn/ui

Run the init command in the project root:

```bash
npx shadcn@latest init
```

The CLI prompts for:
- **Style**: New York or Default (New York recommended -- cleaner borders and shadows)
- **Base color**: Neutral, Slate, Stone, Gray, or Zinc
- **CSS variables**: Yes (required for theming)

This creates:
- `components.json` -- Configuration file for the shadcn CLI
- `lib/utils.ts` (or `src/lib/utils.ts`) -- The `cn()` class merge utility
- Updates `globals.css` with CSS variables for the chosen theme
- Installs dependencies: `clsx`, `tailwind-merge`, `class-variance-authority`

## Step 2: Verify Base Installation

Check these files exist and are correct:

1. **`components.json`** -- Should contain:
   ```json
   {
     "$schema": "https://ui.shadcn.com/schema.json",
     "style": "new-york",
     "rsc": true,
     "tsx": true,
     "tailwind": {
       "config": "tailwind.config.ts",
       "css": "src/app/globals.css",
       "baseColor": "neutral",
       "cssVariables": true
     },
     "aliases": {
       "components": "@/components",
       "utils": "@/lib/utils"
     }
   }
   ```

2. **`lib/utils.ts`** -- Should export the `cn()` helper:
   ```typescript
   import { type ClassValue, clsx } from "clsx"
   import { twMerge } from "tailwind-merge"

   export function cn(...inputs: ClassValue[]) {
     return twMerge(clsx(inputs))
   }
   ```

3. **`globals.css`** -- Should contain `:root` and `.dark` CSS variable blocks

4. **Font variable check** -- After init, verify `globals.css` does not contain circular font references:
   - `--font-sans: var(--font-sans)` — **wrong**, circular reference, browser falls back to system font
   - `--font-sans: var(--font-geist-sans)` — **correct**, maps to the CSS variable set by `next/font` in `layout.tsx`

   If the project uses Geist (Next.js default), ensure `layout.tsx` declares the font variable:
   ```typescript
   import { Geist } from "next/font/google"
   const geistSans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" })
   ```
   And `globals.css` maps it (inside `@theme inline`):
   ```css
   --font-sans: var(--font-geist-sans);
   ```

## Step 3: Configure shadcn studio Registries

To access shadcn studio components, blocks, and themes, add the studio registry to `components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  },
  "registries": {
    "ss-components": {
      "url": "https://shadcnstudio.com/registry"
    },
    "ss-blocks": {
      "url": "https://shadcnstudio.com/registry"
    },
    "ss-themes": {
      "url": "https://shadcnstudio.com/registry"
    }
  }
}
```

This enables three namespace registries:
- `@ss-components` -- Component variants (buttons, cards, inputs, etc.)
- `@ss-blocks` -- Pre-built UI blocks (hero sections, dashboards, forms, etc.)
- `@ss-themes` -- Theme presets (color schemes, typography, etc.)

## Step 4: Configure Premium Access (Optional)

For premium shadcn studio content, create a `.env` file in the project root:

```bash
EMAIL=your-email@example.com
LICENSE_KEY=your-license-key
```

Add `.env` to `.gitignore` if not already present:

```bash
echo ".env" >> .gitignore
```

Free components and blocks work without credentials. Premium content requires a shadcn studio license (Basic $99, Pro $199, Team $449).

## Step 5: Test Component Installation

Verify the setup works by installing a test component:

```bash
# Standard shadcn/ui component:
npx shadcn@latest add button

# shadcn studio component (if registries configured):
npx shadcn@latest add button --registry @ss-components
```

Check that:
- Component file created at `components/ui/button.tsx` (or `src/components/ui/button.tsx`)
- No import errors when building: `npm run build`
- Component renders correctly in the browser

## Step 6: Configure Community Registries (Optional)

The official shadcn MCP only searches registries listed in `components.json`. To unlock search across all 180+ community registries, populate them from the official endpoint:

```bash
curl -s https://ui.shadcn.com/r/registries.json
```

This returns a JSON array with `name`, `url`, `homepage`, `description` for every registry. Add each entry to the `"registries"` field in `components.json`:

```json
{
  "registries": {
    "@magicui": "https://magicui.design/r/{name}.json",
    "@aceternity": "https://ui.aceternity.com/r/{name}.json"
  }
}
```

Use the `/add-registries` command to do this automatically — it fetches the endpoint, parses all entries, and merges them into `components.json`.

### Install the Official shadcn Skill

The official shadcn skill reads `components.json` and enables Claude to discover components from configured registries:

```bash
pnpm dlx skills add shadcn/ui
```

This creates skill files that Claude Code loads automatically when `components.json` is detected.

## Tailwind v3 vs v4 Notes

| Aspect | Tailwind v3 | Tailwind v4 |
|--------|-------------|-------------|
| Config file | `tailwind.config.ts` | CSS-based (`@import "tailwindcss"`) |
| Content paths | In config `content: [...]` | Auto-detected |
| CSS variables | `@layer base { :root {...} }` | Same pattern, new import syntax |
| Button cursor | `cursor-pointer` default | `cursor-default` (add `cursor-pointer` manually) |

If using Tailwind v4, ensure `postcss.config.mjs` uses `@tailwindcss/postcss`:

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
}
```

## What This Skill Does NOT Cover

- Development patterns (App Router, Server Components) -- see `nextjs-dev` plugin
- MCP server configuration -- see `mcp-tools` skill
- Theme customization beyond initial setup -- see `theme-configuration` skill
- Browsing and installing specific components -- see `component-registry` skill
- Searching and installing from community registries -- see `component-search` skill
