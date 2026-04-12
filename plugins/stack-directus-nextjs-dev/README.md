# stack-directus-nextjs-dev

Directus + Next.js stack development plugin for Claude Code. Integrates Directus headless CMS with Next.js App Router for building content-driven applications.

## Type

Stack (Level 2) — project scope with MCP connections.

## Architecture

| Layer | Service | Role |
|-------|---------|------|
| Data | Directus | Content management, REST API, file storage |
| Interface + Logic | Next.js | App Router, Server Components, Server Actions |

Deployment is handled by a separate plugin (e.g. `dokploy-dev`, `vercel-dev`).

## Prerequisites

- Directus v11+ with MCP enabled
- Next.js 15+ with App Router
- Node.js 20+
- Docker (for local Directus development)

## Installation

```bash
claude plugin install stack-directus-nextjs-dev@agents-store-claude-plugins
```

## Environment Variables

Copy `templates/.env.example` to your project root as `.env.local`:

| Variable | Purpose | Client-side |
|----------|---------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | Directus instance URL | Yes |
| `DIRECTUS_ADMIN_TOKEN` | Directus static access token | No |
| `NEXTAUTH_URL` | NextAuth base URL | No |
| `NEXTAUTH_SECRET` | NextAuth encryption secret | No |
| `REVALIDATION_SECRET` | Shared secret for `/api/revalidate` (Directus webhooks) | No |

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Set up environment, install Directus SDK, verify connections |
| `directus-to-nextjs` | Fetch data, render images, TypeScript types, revalidation |
| `authentication` | Directus auth + NextAuth, middleware, session management |
| `deployment` | Docker local dev, ISR revalidation webhooks, production checklist |
| `full-feature` | Step-by-step recipe for building features across the stack |
| `examples` | Scenario walkthroughs (blog, product catalog) |

## Agent

**stack-orchestrator** — Coordinates work across Directus and Next.js for building content-driven features, debugging cross-service issues, and configuring deployment.

## Companion Plugins

Install these Technology Plugins alongside for deep per-tool knowledge:

- `directus-dev@agents-store-claude-plugins` — Directus MCP tools, SDK, API, schema design
- `nextjs-dev@agents-store-claude-plugins` — Next.js App Router, components, data fetching
- `nextjs-provision@agents-store-claude-plugins` — shadcn/ui setup, component scaffolding

For deployment, install the plugin matching your hosting platform (e.g. `dokploy-dev`, `vercel-dev`).
