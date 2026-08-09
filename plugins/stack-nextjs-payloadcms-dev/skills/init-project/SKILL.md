---
name: init-project
description: This skill should be used when the user asks to "create a Next.js + Payload project", "set up the nextjs-payloadcms stack", "initialize a Payload app", "add Payload to my Next.js app", "configure env for Payload", or bootstraps/verifies a project on this stack.
---

# Initialize a Next.js + Payload CMS Project

Bootstrap one Next.js application that contains the frontend, the Payload admin panel, the API, and all backend logic. Target versions: **Payload v3**, **Next.js 16.2.6+** (or 15.2.9+/15.3.9+/15.4.11+ with older payload 3.x), **Node >= 20.9**, **pnpm**, **PostgreSQL**.

## Path A — New Project (preferred)

Scaffold with the official CLI, on the Postgres adapter, with the official Payload skill for Claude:

```bash
npx create-payload-app my-app -t website --db postgres --agent claude
# minimal alternative: -t blank
```

- `-t website` — full reference (pages, posts, blocks, drafts/live preview, SEO, revalidation hooks, seed). Best when building a content site.
- `-t blank` — canonical `(payload)` route group + empty config. Best for product apps (dashboards, portals) that add their own collections.
- `--agent claude` — downloads the official `payload` skill into `.claude/skills/` — keep it; this stack plugin complements it with integration patterns, it does not replace it.

Then reshape `src/` toward the canonical layout from the `architecture` skill (add `access/`, `hooks/`, `actions/`, `jobs/`, `lib/queries/`, `seed/` as the project grows — create directories when the first file needs them, not before).

## Path B — Add Payload to an Existing Next.js App

1. Check compatibility first: Next version in a supported range, Node >= 20.9, ESM-ready config (`next.config.mjs` or `"type": "module"`) — `withPayload` is ESM-only.
2. Install (pin all `@payloadcms/*` to the **exact same version** — mismatches break the admin panel):

```bash
pnpm add payload @payloadcms/next @payloadcms/richtext-lexical @payloadcms/db-postgres sharp graphql
```

3. Wrap the Next config:

```js
// next.config.mjs
import { withPayload } from '@payloadcms/next/withPayload'
export default withPayload({ output: 'standalone' })
```

4. Add the tsconfig alias that makes `@payload-config` resolve:

```json
{ "compilerOptions": { "paths": { "@payload-config": ["./src/payload.config.ts"] } } }
```

5. Copy the `(payload)` route group from the blank template into `src/app/(payload)/` (admin/[[...segments]], api/[...slug], layout.tsx, custom.scss) and move your existing root layout into your own route group, e.g. `src/app/(frontend)/layout.tsx` — the `(payload)` group ships its own root layout and the two must not collide.
6. Create `src/payload.config.ts` (see the `architecture` skill for the canonical spine).

## Environment Variables

Copy the plugin's `templates/.env.example` into the project and fill it:

```bash
DATABASE_URI=postgres://postgres:postgres@localhost:5432/app
PAYLOAD_SECRET=<openssl rand -hex 32>
NEXT_PUBLIC_SERVER_URL=http://localhost:3000
```

Fail fast on missing vars in production (validate at the top of `payload.config.ts`) — a misconfigured container should crash at boot. Local Postgres via compose:

```yaml
services:
  db:
    image: postgres:18
    environment: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: app }
    ports: ['5432:5432']
    volumes: ['pgdata:/var/lib/postgresql/data']
volumes: { pgdata: }
```

## package.json Scripts

```json
{
  "dev": "cross-env NODE_OPTIONS=--no-deprecation next dev",
  "devsafe": "rm -rf .next && cross-env NODE_OPTIONS=--no-deprecation next dev",
  "build": "cross-env NODE_OPTIONS=--no-deprecation payload build",
  "payload": "cross-env NODE_OPTIONS=--no-deprecation payload",
  "generate:types": "cross-env NODE_OPTIONS=--no-deprecation payload generate:types",
  "generate:importmap": "cross-env NODE_OPTIONS=--no-deprecation payload generate:importmap",
  "seed": "tsx src/seed/run.ts",
  "ci": "payload migrate && pnpm build",
  "test": "vitest run"
}
```

Postgres schema flow: **dev uses Drizzle `push`** (auto-sync, default); when a feature is done run `pnpm payload migrate:create <name>`; **production runs `payload migrate`** in CI before build (the `ci` script) or via `prodMigrations` on the adapter for long-running containers. Never mix push and migrate against the same database — pick per environment.

## Verify the Setup

1. `pnpm dev` → open `http://localhost:3000/admin` → create the first admin user.
2. `pnpm generate:types` → `src/payload-types.ts` appears; imports like `import type { User } from '@/payload-types'` compile.
3. Frontend route group renders at `/` independently of the admin.
4. `pnpm test` runs (add vitest with `vite-tsconfig-paths` so `@/` aliases resolve).

## Wire the MCP Servers

This stack plugin ships `.mcp.json` with two servers; make them live:

**1. Payload MCP (the app itself becomes an MCP server).** Install the first-party plugin:

```bash
pnpm add @payloadcms/plugin-mcp
```

```ts
// payload.config.ts
import { mcpPlugin } from '@payloadcms/plugin-mcp'

plugins: [
  mcpPlugin({
    collections: { posts: { enabled: { find: true, create: true, update: true, delete: true } } },
  }),
]
```

Then in the admin panel open **MCP → API Keys**, create a key, and enable per-collection capabilities on it (config alone is not enough — capabilities are toggled per key). Set the env vars the plugin's `.mcp.json` references:

```bash
PAYLOAD_MCP_URL=http://localhost:3000/api/mcp
PAYLOAD_MCP_API_KEY=<key from admin>
```

Restart Claude Code and check `/mcp` — tools appear as `findPosts`, `createPosts`, etc.

**2. Next.js DevTools MCP** (stdio, `npx next-devtools-mcp`) — zero config; on Next 16 it discovers the running `next dev` server's built-in `/_next/mcp` endpoint and exposes runtime tools (`get_errors`, `get_logs`, `get_page_metadata`). On Next 15 only the docs/browser tools work.

## Authoritative Doc Lookups

When deeper reference is needed than the skills provide: `https://payloadcms.com/llms.txt` (index) and `llms-full.txt` (complete docs); Next.js ships versioned markdown docs inside the package at `node_modules/next/dist/docs/`.

Next steps: model the domain (`architecture`), implement logic (`backend-logic`), wire pages (`payload-to-nextjs`), then follow `full-feature` for each feature.
