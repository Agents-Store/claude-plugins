# LEARNINGS.md — nextjs-dev

Accumulated fixes, discoveries, and improvements for the nextjs-dev plugin.

## 2026-03-30 — troubleshoot: Missing next/image debugging for authenticated upstream

**Problem:** Troubleshoot skill had no coverage of broken images from `next/image` when the upstream source requires authentication. Since `next/image` proxies through `/_next/image`, the 403 error is opaque — developers see broken images with no visible error message in the browser.
**Fix:** Added a new "Image Issues (next/image)" section with a table covering 403 from authenticated upstream, missing remotePatterns, private network issues, and quality/sizing problems. Added a debugging tip about checking `/_next/image` requests in the Network tab.
**Root cause:** Troubleshoot skill covered hydration, build, data fetching, and deployment errors but missed image optimization issues entirely.
**Severity:** Major

## 2026-03-28 — docker-patterns: New skill for Docker containerization

**Problem:** No skill covered Docker patterns for Next.js. Users had to manually write Dockerfiles, configure standalone output, and set up docker-compose for dev/prod — common tasks with well-established patterns.
**Fix:** Created new `docker-patterns` skill covering: standalone output config, multi-stage production Dockerfile, dev Dockerfile with hot reload, docker-compose with dev/prod services, .dockerignore, external services integration, build args for NEXT_PUBLIC_* vars, health checks, and troubleshooting.
**Root cause:** Missing skill — Docker containerization is a standard part of Next.js deployment but was not covered.
**Severity:** Major

## [2026-08-09] — doc-alignment: Full alignment with Next.js 16.3 and next-devtools-mcp 0.4.0

**Feature:** Plugin-wide update to Next.js 16 (16.3 current) across 16 files plus a new Cache Components reference. mcp-tools rewritten for next-devtools-mcp 0.4.0 (4-tool surface: `nextjs_index`, `nextjs_call`, `nextjs_docs` and `browser_eval` as gateways; `init`/`upgrade_nextjs_16`/`enable_cache_components` removed). `middleware.ts` replaced with `proxy.ts` everywhere it was taught (app-router-patterns, examples, dashboard-app scenario, advanced-api, agent routing), and the dashboard scenario's impossible route-group matcher `'/(dashboard)/:path*'` was fixed to real URL paths with a consistent tree. Error handling stabilized to `retry` and `catchError` (formerly `unstable_*`). Caching updated: `revalidateTag(tag, profile)` (single-arg deprecated), new `updateTag()`/`refresh()` Server Action APIs, `cacheComponents: true` prerequisite for `use cache`, new `references/cache-components.md` covering profiles, variants, Partial Prefetching, and new ISR behavior. CLI recipes rewritten: `next lint` removal (ESLint CLI/Biome + `next-lint-to-eslint-cli` codemod), Turbopack default with `--webpack` opt-out, `next typegen`, `next upgrade`, `next experimental-analyze`, `--inspect`/`--debug-prerender`, new create-next-app flags, `next telemetry --enable/--disable`. Removed `NextRequest.geo`/`ip` (gone since 15.0), documented Next 16 image defaults (`qualities: [75]`, 4h `minimumCacheTTL`, `localPatterns`, `dangerouslyAllowLocalIP`), required parallel-route `default.tsx`, `after()`/`connection()`/`forbidden()`/`unauthorized()`/root params in api-reference, React Compiler + Tailwind v4 + prefetching rewrite in performance-optimization, `instant()` E2E helper in testing-patterns, dashboard scenario migrated to Auth.js v5 (`auth()`, `authjs.*` cookies) and zod v4 (`z.email()`, `error` param), Node 20.9+/TS 5.1+ minimums in setup/troubleshoot, and evals updated to Next.js 16 / proxy.ts. Version bumped 1.3.1 → 1.4.0.
**Implementation:** Targeted in-place edits preserving each file's structure and tone; full rewrites only for mcp-tools and cli-recipes where most content was obsolete; one new reference file under data-fetching linked from the skill; README gained a "What's New in v1.4.0" section.
**Rationale:** Verified against nextjs.org/docs (version 16.3.0), the next-16 through next-16-3 release posts, the next-devtools-mcp README (0.4.0 migration notes), and npm dist-tags — the plugin still taught removed commands (`next lint`), removed MCP tools, deprecated conventions (`middleware.ts`, bare `revalidateTag`), pre-16 defaults, and one auth matcher that could never match, all of which would actively mislead agents building on current Next.js.

## [2026-08-09] — fact-check: corrections from adversarial doc verification

**Problem:** Two values in the cacheLife Profiles table of `skills/data-fetching/references/cache-components.md` were wrong: the `default` profile's Expire was listed as "1 year" (official 16.3 docs: **never** — "expire: never expires by time") and the `seconds` profile's Stale was listed as "0" (official docs: **30 seconds**, with a 30-second minimum enforced for client stale time). 19 of 21 fact-checked claims in the v1.4.0 update were confirmed; only these two were refuted.
**Fix:** Changed the `default` row's Expire from "1 year" to "never" and the `seconds` row's Stale from "0" to "30 seconds". All other profile rows (minutes/hours/days/weeks/max) verified correct and left unchanged. No other file in the plugin repeated the wrong values.
**Root cause:** The table was sourced from the outdated Next.js 15 canary cacheLife docs; the stable 16.3 docs changed the `default` expire to never and enforce a 30-second minimum client stale time.
**Severity:** Minor

