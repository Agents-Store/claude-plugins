# stack-directus-nextjs-trigger-dev

Directus + Next.js + Trigger.dev stack development plugin for Claude Code. Extends the Directus + Next.js App Router stack with a self-hosted Trigger.dev platform — a workflow engine for AI agents, durable long-running logic, and scheduled jobs.

Delegates complex async logic (AI agent workflows, webhook processing, image transforms, third-party API calls, bulk operations) out of Next.js Server Actions and route handlers and into durable Trigger.dev tasks that can retry, be observed, and write results back to Directus.

## Type

Stack (Level 2) — 3-service architecture with MCP connections to Directus AND Trigger.dev.

## Architecture

| Layer | Service | Role |
|-------|---------|------|
| Data | Directus | Content management, REST API, file storage, Flows |
| Logic | Next.js + Trigger.dev (self-hosted) | Next.js: sync logic (API routes, Server Actions, webhook receivers). Trigger.dev: async/durable logic (AI agent workflows, scheduled jobs, long-running tasks, retries) |
| Interface | Next.js | App Router, Server Components, rendering |
| Deployment | Vercel / Dokploy (Next.js) + Docker (Directus + Trigger webapp/supervisor) | Hosting, edge functions, auto-builds |

## Prerequisites

- Directus v11+ with MCP enabled
- Next.js 15+ with App Router
- Self-hosted Trigger.dev v4 instance (webapp + supervisor running)
- Node.js 20+
- Docker (for local Directus development)

## Installation

```bash
claude plugin install stack-directus-nextjs-trigger-dev@agents-store-claude-plugins
```

## Environment Variables

Copy `templates/.env.example` to your project root as `.env.local`:

| Variable | Purpose | Client-side |
|----------|---------|-------------|
| `NEXT_PUBLIC_DIRECTUS_URL` | Directus instance URL | Yes |
| `DIRECTUS_ADMIN_TOKEN` | Directus static access token | No |
| `NEXTAUTH_URL` | NextAuth base URL | No |
| `NEXTAUTH_SECRET` | NextAuth encryption secret | No |
| `REVALIDATION_SECRET` | Shared secret for `/api/revalidate` (Directus webhooks + Trigger callbacks) | No |
| `VERCEL_TOKEN` | Vercel API token (optional if using Dokploy) | No |
| `VERCEL_ORG_ID` | Vercel organization ID | No |
| `VERCEL_PROJECT_ID` | Vercel project ID | No |
| `TRIGGER_SECRET_KEY` | Trigger.dev env secret OR PAT (also used by the MCP server — see note below) | No |
| `TRIGGER_API_URL` | Self-hosted Trigger.dev URL | No |
| `TRIGGER_PROJECT_REF` | Trigger.dev project ref | No |

> **Note on `TRIGGER_SECRET_KEY`**: the bundled `.mcp.json` wires `TRIGGER_SECRET_KEY` into the Trigger.dev MCP server's `TRIGGER_ACCESS_TOKEN`. The MCP server normally expects a Personal Access Token (`tr_pat_...`), not an environment secret key (`tr_dev_...`). If MCP rejects your env secret key, create a PAT in the Trigger.dev dashboard → Personal Access Tokens and put it in `TRIGGER_SECRET_KEY` instead — the SDK accepts PATs for task triggering too.

## MCP Servers

This plugin bundles `.mcp.json` with two MCP servers:

- **`directus`** (http) — connects to `${NEXT_PUBLIC_DIRECTUS_URL}/mcp` with `DIRECTUS_ADMIN_TOKEN` for schema exploration, item CRUD, Flow management
- **`trigger-dev`** (stdio) — spawns `npx trigger.dev@latest mcp` with `TRIGGER_ACCESS_TOKEN=${TRIGGER_SECRET_KEY}` and `TRIGGER_API_URL` for listing tasks, triggering runs, managing schedules

Values interpolate from your project `.env.local` automatically.

## Skills

| Skill | Description |
|-------|-------------|
| `init-project` | Set up environment, install Directus SDK + Trigger SDK, initialize trigger.dev, verify all three service connections |
| `directus-to-nextjs` | Fetch data, render images, TypeScript types, revalidation patterns |
| `authentication` | Directus auth + NextAuth, middleware, session management, per-user clients in tasks |
| `deployment` | Vercel/Dokploy production, Docker local, Directus webhooks, Trigger task deploys, CI/CD |
| `full-feature` | 6-step recipe for building features across Directus, Next.js, and Trigger.dev |
| `examples` | Scenario walkthroughs (blog, product catalog, AI enrichment pipeline, scheduled data sync) |
| `background-tasks` | Offload work from Next.js to Trigger.dev — Server Actions, route handlers, `force-dynamic`, `useRealtimeRun` |
| `scheduled-tasks` | `schedules.task()` cron patterns, reading/writing Directus on a schedule, environment attachment |
| `directus-to-trigger` | Directus Flow → Next.js webhook → Trigger task → Directus writeback → revalidate pipeline |

## Agent

**stack-orchestrator** — Coordinates work across Directus, Next.js, and Trigger.dev for building content-driven features, offloading slow operations to durable tasks, wiring event-driven pipelines from Directus Flows, defining scheduled jobs, debugging cross-service issues, and configuring deployment.

## Companion Plugins

Install these Technology Plugins alongside for deep per-tool knowledge:

- `directus-dev@agents-store-claude-plugins` — Directus MCP tools, SDK, API, schema design
- `nextjs-dev@agents-store-claude-plugins` — Next.js App Router, components, data fetching
- `nextjs-provision@agents-store-claude-plugins` — shadcn/ui setup, component scaffolding
- `trigger-dev@agents-store-claude-plugins` — Trigger.dev task API, retries/queues/waits, realtime, CLI, MCP patterns, self-hosted deployment
- `dokploy-dev@agents-store-claude-plugins` — Dokploy deployments, self-hosted Trigger.dev webapp + supervisor
- `vercel@claude-plugins-official` — Vercel deployment (if not self-hosting Next.js)

## What This Plugin Does NOT Cover

To keep skills focused and avoid duplication, this plugin delegates to the companion Technology plugins for:

- **Directus internals** (field types, relation modes, permissions, Flow operation catalog, extensions) → `directus-dev`
- **Next.js internals** (App Router dynamic features, caching layers, middleware config, Server Component rules) → `nextjs-dev`
- **Trigger.dev task API depth** (retry configs, queues, waits, metadata, tags, Zod schemas, AI agent patterns, build extensions, realtime hooks API) → `trigger-dev`
- **shadcn/ui setup** → `nextjs-provision`
- **Dokploy compose/infra** for self-hosted Trigger → `dokploy-dev`

This plugin covers the **integration seams**: how to wire all three services together, the gotchas unique to each boundary, and end-to-end recipes that span all layers.
