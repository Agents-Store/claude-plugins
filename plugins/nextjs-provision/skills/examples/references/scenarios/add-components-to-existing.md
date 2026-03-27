# Scenario: Add shadcn Components to an Existing Project

Walkthrough for adding shadcn/ui and shadcn studio to an existing Next.js project that already has some UI components.

## Prerequisites

- Existing Next.js 13+ project with App Router
- Tailwind CSS already installed
- TypeScript configured

## Step 1: Audit Existing Components

Before installing shadcn, understand what you already have:

```bash
# List existing component files
find src/components -name "*.tsx" -o -name "*.jsx" | head -30

# Check for existing UI libraries
grep -E "(material-ui|chakra|mantine|radix|headless)" package.json
```

### Decision Points

| Existing Setup | Approach |
|----------------|----------|
| No UI library | Clean install, straightforward |
| Radix UI primitives | shadcn builds on Radix -- components will coexist |
| Material UI / Chakra | Gradual migration, keep both temporarily |
| Custom Tailwind components | Remap to shadcn equivalents where possible |

## Step 2: Initialize shadcn/ui

```bash
npx shadcn@latest init
```

The CLI detects your existing configuration:
- Finds `tailwind.config.ts` (v3) or CSS imports (v4)
- Detects `tsconfig.json` path aliases
- Sets up `components.json` based on your project structure

Verify `components.json` paths match your project:

```json
{
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

If your project uses a different structure (e.g., `@/src/components`), update the aliases accordingly.

## Step 3: Verify No Conflicts

Check for potential conflicts:

```bash
# Check if components/ui/ already exists
ls src/components/ui/ 2>/dev/null

# Check for cn() utility conflicts
grep -r "function cn" src/ --include="*.ts" --include="*.tsx"

# Check for CSS variable conflicts
grep -c "\-\-background:" src/app/globals.css
```

If `components/ui/` exists with custom components, either:
- Rename your existing directory: `mv src/components/ui src/components/custom-ui`
- Use a different alias in `components.json`: `"ui": "@/components/shadcn"`

## Step 4: Install Components Incrementally

Start with the components you need most. Do not install everything at once.

### Replace Existing Custom Components

Map your custom components to shadcn equivalents:

| Your Component | shadcn Equivalent | Install |
|----------------|-------------------|---------|
| Custom button | `button` | `npx shadcn@latest add button` |
| Custom modal | `dialog` | `npx shadcn@latest add dialog` |
| Custom dropdown | `dropdown-menu` | `npx shadcn@latest add dropdown-menu` |
| Custom input | `input` + `form` | `npx shadcn@latest add input form` |
| Custom tooltip | `tooltip` | `npx shadcn@latest add tooltip` |
| Custom tabs | `tabs` | `npx shadcn@latest add tabs` |
| Custom toast | `sonner` | `npx shadcn@latest add sonner` |

### Migration Pattern

For each component replacement:

1. Install the shadcn component
2. Create a wrapper that matches your existing API (if needed)
3. Update imports one file at a time
4. Test each file after updating
5. Remove old custom component when fully migrated

Example -- migrating a custom button:

```typescript
// BEFORE: components/custom-ui/button.tsx
export function Button({ variant, children, ...props }) {
  const classes = variant === "primary" ? "bg-blue-500 text-white" : "bg-gray-200"
  return <button className={classes} {...props}>{children}</button>
}

// AFTER: Already have components/ui/button.tsx from shadcn
// Update imports across the codebase:
// import { Button } from "@/components/custom-ui/button"
//    → import { Button } from "@/components/ui/button"

// Map old variants to shadcn variants:
// variant="primary" → variant="default"
// variant="secondary" → variant="secondary"
// variant="danger" → variant="destructive"
```

## Step 5: Add shadcn studio Registries

Once base shadcn/ui is working, add studio registries:

```json
// Add to components.json
{
  "registries": {
    "ss-components": { "url": "https://shadcnstudio.com/registry" },
    "ss-blocks": { "url": "https://shadcnstudio.com/registry" },
    "ss-themes": { "url": "https://shadcnstudio.com/registry" }
  }
}
```

## Step 6: Add Studio Blocks for Common Sections

Replace hand-built sections with studio blocks:

```bash
# If you have a custom hero section
npx shadcn@latest add hero-section-01 --registry @ss-blocks

# If you have a custom pricing page
npx shadcn@latest add pricing-01 --registry @ss-blocks

# If you have a custom dashboard layout
npx shadcn@latest add dashboard-shell-01 --registry @ss-blocks
```

## Step 7: Match Theme to Existing Brand

Extract your current brand colors and map to shadcn CSS variables:

```bash
# Find your current color definitions
grep -r "bg-\[#" src/ --include="*.tsx" | head -10
grep -r "text-\[#" src/ --include="*.tsx" | head -10
```

Convert hex colors to HSL and update `globals.css`:

```css
:root {
  /* Replace with your brand colors in HSL format */
  --primary: 217 91% 60%;           /* Your primary brand color */
  --primary-foreground: 0 0% 100%;   /* Text on primary */
  /* ... map all variables */
}
```

See `theme-configuration` skill for detailed theming instructions.

## Step 8: Clean Up

After migration is complete:

```bash
# Remove old custom UI components that have been replaced
rm -rf src/components/custom-ui/  # Only after all imports are updated!

# Remove unused dependencies from old UI library
npm uninstall @old-ui-library

# Verify build still passes
npm run build
```

## Step 9: Verify

```bash
# Full build check
npm run build

# Type check
npx tsc --noEmit

# Start dev server and test each page
npm run dev
```

Check:
- All pages render correctly
- No broken imports or missing components
- Theme colors match your brand
- Dark mode works (if applicable)
- Interactive components (dialogs, dropdowns, forms) function properly
- No console errors

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Breaking existing pages during migration | Migrate one component at a time, test after each |
| CSS conflicts between old and new styles | Use shadcn's CSS variable system, remove duplicate color definitions |
| Path alias mismatches | Ensure `components.json` aliases match `tsconfig.json` paths |
| Missing `'use client'` directives | Interactive shadcn components need client boundaries |
| Forgetting TooltipProvider | Add `<TooltipProvider>` in root layout if using Tooltip |
| Old library CSS bleeding through | Remove old library's CSS imports from layout/globals |
