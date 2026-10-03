# nextjs-dev

Next.js development plugin for the Agents Store marketplace. Comprehensive knowledge base for building production-ready Next.js applications — covers App Router, Server/Client Components, data fetching, caching, performance optimization, project architecture, error handling, forms & validation, security, authentication, API design, and testing.

## Type

Technology (Level 1) — knowledge-only, no MCP server bundled.

## Skills (18 total)

### Core Framework

| Skill | Description |
|-------|-------------|
| `setup` | Verify Next.js project environment and readiness |
| `app-router-patterns` | App Router file conventions, routing, layouts, metadata, proxy |
| `server-client-components` | Server vs Client Component patterns, boundaries, composition |
| `data-fetching` | Data fetching, Server Actions, caching, ISR, streaming, Cache Components (`use cache`), previous-model route config (`revalidate`, `dynamic`) and what replaces it under `cacheComponents`, pages backed by a headless CMS (webhook revalidation, CMS images) |
| `api-reference` | Framework API quick reference (functions, config, types) |

### Architecture & Patterns

| Skill | Description |
|-------|-------------|
| `project-structure` | Project architecture, folder organization, feature-based structure, naming conventions |
| `error-handling` | Error boundaries (`error.tsx`, `global-error.tsx`), `not-found.tsx`, `loading.tsx`, `catchError` |
| `form-handling` | Server Action forms, `useActionState`, `useFormStatus`, Zod validation, `useOptimistic`, file uploads |
| `api-design` | Route Handlers, streaming responses (SSE), webhooks, API versioning, CORS |

### Security & Auth

| Skill | Description |
|-------|-------------|
| `security-patterns` | CSP headers with nonces, CSRF protection, XSS prevention, env var safety, `server-only`, security headers |
| `auth-patterns` | Authentication flows, session management (JWT/cookies), proxy auth guards, RBAC, Better Auth for new projects (with the role caveat), NextAuth v4 and Auth.js v5 for existing ones |

### Quality & Testing

| Skill | Description |
|-------|-------------|
| `testing-patterns` | Vitest + React Testing Library setup, testing Server Actions, Route Handlers, mocking `next/navigation`, Playwright E2E |
| `performance-optimization` | Image/font optimization, code splitting, bundle analysis, Core Web Vitals |
| `troubleshoot` | Common errors, hydration mismatches, build failures, deployment issues |

### Tooling & Examples

| Skill | Description |
|-------|-------------|
| `mcp-tools` | Next.js DevTools MCP server reference (`next-devtools-mcp`) |
| `cli-recipes` | CLI commands, scripts, environment variables, Docker deployment |
| `docker-patterns` | Standalone output, multi-stage Dockerfile, Docker Compose, health checks |
| `examples` | End-to-end scenario walkthroughs (dashboard app, e-commerce storefront) |

## Agent

**nextjs-developer** — Next.js development specialist for building pages, fetching data, implementing auth, designing APIs, handling forms, securing applications, writing tests, debugging issues, and optimizing performance.

## Prerequisites

- A Next.js project (16.x recommended, pinned `next@^16.3.8` — earlier 16.3.x patches miss several security fixes; 14+ minimum for App Router content)
- Node.js 22 or 24 LTS recommended (Next.js 16 formally requires >=20.9.0, but Node 20 is end-of-life)
- For MCP integration: install `next-devtools-mcp` in your project and run `next@>=16.3.8` (earlier dev servers expose `/_next/mcp` without an origin check)

## Installation

Install as a Claude Code plugin from the Agents Store marketplace.

## What's New in v1.5.0

Aligned with `next@16.3.8` and the September 2026 security release:
- **Version floor** — recommended range is `next@^16.3.8`; the 16.3.x patches since 16.3.0 carry critical, high and medium security fixes (see `security-patterns` and `setup`)
- **Previous-model route config is now labelled** — every `export const revalidate` / `dynamic` / `dynamicParams` / `fetchCache` example states that it works only without `cacheComponents`; with `cacheComponents: true` those options are removed and `'use cache'` + `cacheLife()` / `cacheTag()` replaces them (migration table in `data-fetching/references/cache-components.md`)
- **Troubleshooting** — "Dynamic server usage" under Cache Components is fixed with `<Suspense>` around the runtime-API reader, not `force-dynamic`
- **Caching details** — `fetch` tags need `cache: 'force-cache'`; `'use cache: private'` is browser-only and never part of the static shell; `experimental.cachedNavigations` is automatic under `cacheComponents`
- **Auth** — Auth.js now lives under Better Auth: a new "Better Auth (recommended for new projects)" section; Auth.js v5 stays documented as beta, maintenance-mode
- **New 16.3 surface** — `io()` from `next/cache`, the `instant` / `prefetch` segment configs, per-link prefetching, view transitions, and the first-party agent skills (`next-dev-loop`, `next-cache-components-adoption`, `next-cache-components-optimizer`, `next-partial-prefetching-adoption`)
- **Tooling** — Vitest 5 requirements (Node >= 22.12, Vite >= 6.4), experimental Rust React Compiler caveats, `instant()` E2E helper needs `baseURL` and `exposeTestingApiInProductionBuild` against `next start`

## What's New in v1.4.0

Full alignment with Next.js 16.3:
- **proxy.ts** — `middleware.ts` is deprecated; all routing, auth, and CSP examples now use the `proxy` convention
- **Stable error APIs** — `retry` prop and `catchError` from `next/error` (formerly `unstable_*`)
- **Caching APIs** — `revalidateTag(tag, profile)` (single-arg form deprecated), new `updateTag()` and `refresh()` Server Action APIs, `cacheComponents: true` prerequisite for `use cache`, new Cache Components / Instant Navigations reference
- **`next lint` removal** — linting recipes migrated to the ESLint CLI / Biome; `next typegen` for CI type checks
- **Turbopack default** — dev and build default to Turbopack; bundle analysis via `next experimental-analyze`
- **next-devtools-mcp 0.4.0** — 4-tool surface (`nextjs_index`, `nextjs_call`, `nextjs_docs`, `browser_eval` gateways); `init`/`upgrade_nextjs_16`/`enable_cache_components` removed
- Next 16 image defaults, parallel-route `default.tsx` requirement, Node 20.9+ / TS 5.1+ minimums, Tailwind v4 and zod v4 example updates

## What's New in v1.3.0

Added 7 new skills covering production-ready patterns:
- **Project structure** — scalable folder organization for small to large apps
- **Error handling** — error boundaries, recovery, and loading states
- **Form handling** — Server Action forms with validation and optimistic UI
- **Security** — CSP, CSRF, XSS prevention, environment variable safety
- **Authentication** — session management, proxy guards, RBAC
- **API design** — Route Handlers, streaming, webhooks
- **Testing** — Vitest unit tests, Playwright E2E, mocking patterns

## Related

- [`next-devtools-mcp`](https://github.com/vercel/next-devtools-mcp) — Vercel's official MCP server for Next.js runtime diagnostics
- [Next.js Documentation](https://nextjs.org/docs) — Official framework documentation
- [Better Auth](https://www.better-auth.com) — Authentication library for new Next.js projects (Auth.js is now part of Better Auth)
- [Auth.js](https://authjs.dev) — Existing Auth.js v5 projects; migration guide to Better Auth
- [Vitest](https://vitest.dev) — Unit testing framework
- [Playwright](https://playwright.dev) — E2E testing framework
