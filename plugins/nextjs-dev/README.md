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
| `data-fetching` | Data fetching, Server Actions, caching, ISR, streaming, Cache Components (`use cache`) |
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
| `auth-patterns` | Authentication flows, session management (JWT/cookies), proxy auth guards, RBAC, Auth.js integration |

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

- A Next.js project (16.x recommended — current stable 16.3; 14+ minimum for App Router content)
- For MCP integration: install `next-devtools-mcp` in your project

## Installation

Install as a Claude Code plugin from the Agents Store marketplace.

## What's New in v1.4.0

Full alignment with Next.js 16 (16.3 current):
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
- [Auth.js](https://authjs.dev) — Authentication library for Next.js
- [Vitest](https://vitest.dev) — Unit testing framework
- [Playwright](https://playwright.dev) — E2E testing framework
