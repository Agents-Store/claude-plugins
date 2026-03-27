---
name: cli-recipes
description: Next.js CLI commands and common development scripts. This skill should be used when the user asks about "Next.js CLI", "next dev command", "next build", "create-next-app", "Turbopack", "Next.js command line", or needs to run Next.js commands from the terminal.
---

# Next.js CLI Recipes

Command-line recipes for creating, developing, building, and deploying Next.js applications.

## Create a New Project

```bash
npx create-next-app@latest my-app
```

Interactive prompts will ask about TypeScript, ESLint, Tailwind CSS, `src/` directory, App Router, and import aliases.

Non-interactive with all defaults:

```bash
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

From a template:

```bash
npx create-next-app@latest --example with-tailwindcss my-app
npx create-next-app@latest --example https://github.com/user/repo my-app
```

## Development Server

```bash
# Standard dev server
next dev

# With Turbopack (faster HMR and builds)
next dev --turbopack

# Custom port
next dev -p 4000

# Custom hostname
next dev -H 0.0.0.0

# HTTPS (local development)
next dev --experimental-https

# Show verbose output
next dev --verbose
```

Turbopack is the recommended bundler for development in Next.js 15+. It provides significantly faster hot module replacement.

## Build for Production

```bash
# Production build
next build

# Analyze bundle size
ANALYZE=true next build
```

Build output appears in `.next/`. For standalone output (Docker), set `output: 'standalone'` in `next.config.ts`.

The build reports:
- **Route sizes** — JS sent to client per route
- **First Load JS** — Total JS for initial page load
- **Static vs Dynamic** — Which routes are statically generated vs server-rendered

## Start Production Server

```bash
# Start built application
next start

# Custom port
next start -p 4000
```

Requires `next build` first. Serves the production build with Node.js.

## Linting

```bash
# Lint all files
next lint

# Lint specific directories
next lint --dir src --dir app

# Fix auto-fixable issues
next lint --fix

# Output format
next lint --format json
```

Next.js includes a built-in ESLint configuration (`eslint-config-next`) that catches common Next.js issues:
- Incorrect image usage
- Missing `alt` attributes
- Incorrect `<link>` and `<script>` usage
- Accessibility issues

## Type Checking

```bash
# TypeScript type checking
npx tsc --noEmit

# Or with next build (includes type checking)
next build
```

## Useful Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | Dev/prod server port | `PORT=4000 next dev` |
| `HOSTNAME` | Server hostname | `HOSTNAME=0.0.0.0 next start` |
| `NODE_ENV` | Environment | `development`, `production`, `test` |
| `NEXT_TELEMETRY_DISABLED` | Disable telemetry | `NEXT_TELEMETRY_DISABLED=1` |
| `ANALYZE` | Enable bundle analyzer | `ANALYZE=true next build` |
| `NEXT_PUBLIC_*` | Client-side env vars | `NEXT_PUBLIC_API_URL=...` |

## Package Scripts

Typical `package.json` scripts:

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "test": "vitest",
    "test:e2e": "playwright test"
  }
}
```

## Bundle Analysis

Install and configure the bundle analyzer:

```bash
npm install @next/bundle-analyzer
```

```ts
// next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer'

const nextConfig = {
  // ...
}

export default process.env.ANALYZE === 'true'
  ? withBundleAnalyzer()(nextConfig)
  : nextConfig
```

```bash
ANALYZE=true next build
```

Opens an interactive treemap showing client and server bundle composition.

## Docker Deployment

```dockerfile
FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable pnpm && pnpm build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
```

Requires `output: 'standalone'` in `next.config.ts`.

## Telemetry

```bash
# Check telemetry status
next telemetry status

# Disable telemetry
next telemetry disable

# Enable telemetry
next telemetry enable
```

## Codemod (Upgrade Migrations)

```bash
# Run all codemods for a target version
npx @next/codemod@latest upgrade

# Run a specific codemod
npx @next/codemod@latest <transform> <path>
```

Available codemods handle async API migrations (`params`, `cookies`, `headers`), configuration changes, and deprecated API removals.
