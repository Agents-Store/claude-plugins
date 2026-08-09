---
name: architecture
description: This skill should be used when the user asks "how to structure a Next.js + Payload project", "where does business logic live", "project architecture for Payload CMS", "organize collections, actions and jobs", or plans where a new feature's code belongs in the nextjs-payloadcms stack.
---

# Next.js + Payload CMS — Project Architecture

Define the architecture of a project where **one Next.js application is the entire system**: frontend, admin panel, API, business logic, and background workflows. Payload CMS v3 is embedded in the Next.js app — there is no separate CMS server, no external workflow engine, and no second deployable. Every piece of backend logic runs on Payload primitives (hooks, jobs, access control, Local API) or Next.js server primitives (Server Components, Server Actions, Route Handlers).

## The Single-App Principle

Payload v3 installs *into* the Next.js App Router. The admin panel, REST API, and GraphQL API are Next.js routes in the `(payload)` route group. Your product UI lives in a sibling `(frontend)` route group. Both share one process, one database connection pool, one `payload.config.ts`, and one generated type file. Consequences:

- Server code calls Payload through the **Local API** (direct function calls) — never through HTTP fetch to your own REST API, because that adds a network hop, loses type inference, and skips the shared transaction.
- Business rules enforced in **hooks and access control** apply to every entry point at once: admin panel, REST, GraphQL, and Local API calls.
- One deploy ships everything: schema, logic, admin, and UI can never drift apart.

## Canonical Directory Layout

```
src/
├── payload.config.ts          # Single source of truth: collections, globals, jobs, plugins
├── payload-types.ts           # GENERATED — run `payload generate:types` after schema changes
├── collections/               # One file per collection (CollectionConfig)
│   ├── users.ts
│   ├── leave-requests.ts
│   └── leave-requests.integration.test.ts   # Tests colocated with the code they cover
├── globals/                   # GlobalConfig files (site/company settings)
├── access/                    # Reusable Access functions and role helpers
│   └── roles.ts               # hasRole, adminOnly, companyScopedAccess(...)
├── hooks/                     # Collection/field hooks — thin adapters over lib/ logic
│   ├── leave-requests.ts      # computeLeaveDays, handleLeaveReview
│   └── leave-status.ts        # Pure state-machine helper (unit-testable)
├── jobs/                      # Jobs Queue tasks and workflows (TaskConfig/WorkflowConfig)
├── actions/                   # Next.js Server Actions ('use server') — one file per domain
├── lib/                       # Framework-free logic + shared helpers
│   ├── session.ts             # getSession(): { payload, user }
│   └── queries/               # Read-path helpers: (payload, args) => typed DTOs
├── components/                # React components (ui/ = design system, client components)
├── seed/                      # Seed scripts run with tsx
└── app/
    ├── (frontend)/            # Product UI: own root layout, pages, route handlers
    └── (payload)/             # Payload-owned: admin/[[...segments]], api/[...slug], layout.tsx
migrations/                    # Generated DB migrations (Postgres) — committed
```

Keep the two route groups strictly separated: `(payload)` ships its own root `layout.tsx` that Payload manages, so the app's real root layout lives inside `(frontend)`. Never move frontend pages into `(payload)` — the groups exist so each side controls its own `<html>` shell.

## Where Does Logic Go? (Decision Matrix)

Route every new piece of logic with this table. The left column is the requirement; the right column is the only correct home for it in this stack.

| Requirement | Home | Why |
|---|---|---|
| Derived/computed field (slug, full name, day count) | `beforeChange` collection hook or field hook in `src/hooks/` | Runs for admin panel, REST, and Local API alike |
| Validation / invariant / status transition | `beforeValidate`/`beforeChange` hook throwing `APIError` | Rejects invalid writes from every entry point |
| Stamping metadata (reviewer, timestamps, actor) | `beforeChange` hook reading `req.user` | The hook sees the authenticated actor on any surface |
| Side effect after a write (audit log, counters) | `afterChange` hook (guard with `context` flag) | Fires on create and update, has the final `doc` |
| Slow side effect (email, external API, AI call) | `afterChange` hook that **queues a job** | Hooks block the request — offload anything slow |
| Scheduled / recurring work | Task in `src/jobs/` with `schedule: [{ cron, queue }]` | Payload Jobs Queue is the stack's cron |
| Multi-step durable process | Jobs Queue **workflow** chaining tasks | Completed tasks resume from cache on retry |
| User-triggered mutation from the UI | Server Action in `src/actions/` | One POST round-trip, `revalidatePath` after |
| Read path for a page | Helper in `src/lib/queries/` called from an RSC | Keeps pages thin, queries reusable and testable |
| Endpoint for an external system (webhook, integration) | Custom endpoint in `payload.config.ts` or collection `endpoints` | Gets `req.payload` + `req.user`; check auth yourself |
| Page-shaped HTTP API for the frontend | Route Handler in `app/(frontend)/**/route.ts` | Next-native, typed params, no Payload coupling |
| Cross-cutting request rules (redirects, headers) | `proxy.ts` (Next 16) / `middleware.ts` (Next 15) | Keep it thin — real auth checks live in layouts/pages |

Two placement rules with reasons:

1. **Enforce in hooks, pre-check in actions.** Server Actions validate input and return friendly error messages, but the authoritative enforcement (allowances, transitions, tenant boundaries) lives in hooks and access control — because the admin panel and REST API bypass your actions entirely.
2. **Extract pure logic into `lib/`.** Hooks and job handlers should be thin adapters calling pure functions (`workingDaysBetween`, `isValidLeaveTransition`, `selectExpiringDocuments`) — because pure modules unit-test without a database, and the same rule can serve a hook, an action, and a job.

## The Type Contract

`payload-types.ts` is generated from the config and imported everywhere (`import type { User, LeaveRequest } from '@/payload-types'`). Treat it as the API contract between all layers:

- After any collection/field change run `pnpm payload generate:types` (and `payload generate:importmap` if admin components changed).
- Type hooks generically: `CollectionBeforeChangeHook<LeaveRequest>`, `Access<LeaveRequest>`, `FieldHook<User, string, User>`.
- Local API calls infer types from the slug — `payload.create({ collection: 'recognitions', data })` type-checks `data`.

## Data Flow of One Feature

A complete feature travels through the layers in this order (see the `full-feature` skill for the step-by-step recipe):

```
collection (schema + access)  →  hooks (rules)  →  action (UI mutation)
        ↓                            ↓                    ↓
payload-types.ts              jobs (async work)    revalidatePath()
        ↓                                                ↓
lib/queries (reads)  →  RSC page (frontend)  →  client components
```

## Configuration Spine

`payload.config.ts` aggregates everything — when reviewing a project, read it first. The canonical shape:

```ts
export default buildConfig({
  serverURL: process.env.NEXT_PUBLIC_SERVER_URL,
  admin: { user: Users.slug, importMap: { baseDir: path.resolve(dirname) } },
  collections: [Users, Media /* ... */],
  globals: [CompanySettings],
  jobs: {
    tasks: [notifyExpiringDocuments],
    autoRun: [{ cron: '0 8 * * *', queue: 'nightly', limit: 10 }],
    shouldAutoRun: async () => process.env.ENABLE_JOBS === 'true',
  },
  db: postgresAdapter({
    pool: { connectionString: process.env.DATABASE_URI || '' },
    push: process.env.NODE_ENV !== 'production',   // dev: schema push; prod: migrations only
    migrationDir: path.resolve(dirname, '../migrations'),
  }),
  editor: lexicalEditor(),
  secret: process.env.PAYLOAD_SECRET || '',
  typescript: { outputFile: path.resolve(dirname, 'payload-types.ts') },
  cors: [process.env.NEXT_PUBLIC_SERVER_URL || ''].filter(Boolean),
  csrf: [process.env.NEXT_PUBLIC_SERVER_URL || ''].filter(Boolean),
})
```

Validate required env vars at config load in production (fail fast on missing `PAYLOAD_SECRET`, `DATABASE_URI`, `NEXT_PUBLIC_SERVER_URL`) — a misconfigured container should crash at boot, not at first request.

## Testing Placement

- **Unit tests** — colocated with pure helpers (`leave-status.test.ts` next to `leave-status.ts`); no database needed.
- **Integration tests** — colocated with collections (`employees.integration.test.ts`); boot Payload with `getPayload`, exercise hooks + access through the Local API.
- Run with `vitest`; keep the pure-logic extraction rule above and most tests stay in the fast unit tier.

## Related Skills

- Placement details for actions/hooks/jobs → `backend-logic`
- Read paths, caching, revalidation → `payload-to-nextjs`
- Sessions, roles, tenant scoping → `auth-and-access`
- Running workers and cron → `background-job`
- End-to-end recipe → `full-feature`
- Deep tool knowledge (field types, adapters, admin customization) lives in the `payloadcms-dev` and `nextjs-dev` technology plugins — this stack plugin covers how the pieces compose.
