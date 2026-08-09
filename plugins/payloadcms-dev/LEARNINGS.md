# payloadcms-dev — Learnings

Accumulated fixes, discoveries, and corrections for this plugin. Each entry is filed when `plugin-creator:feedback` or `plugin-creator:wrap-up` runs after a real session uncovered something worth remembering.

Format:
```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong.
**Fix:** What was changed.
**Root cause:** Why the original was wrong.
**Severity:** Critical / Major / Minor.
```

---

## 2026-06-16 — globals, authentication, localization, data-management, admin-customization, official-plugins, deployment: full docs-taxonomy coverage (v1.1.0)

**Feature:** Added 7 new skills to close every gap against the current Payload v3 documentation taxonomy (sourced from `payloadcms.com/llms.txt`), plus a `jobs-queue` refresh for declarative job schedules.
**Implementation:**
- `skills/globals/` — `GlobalConfig`, global access/hooks, `findGlobal`/`updateGlobal` (note: versioned globals use `versions.max`, not collections' `maxPerDoc`).
- `skills/authentication/` — Cookie/JWT/API-key/custom (OAuth/SSO) strategies, auth operations, verification & forgot-password emails, token data.
- `skills/localization/` — `localization` config, localized fields/relationships, fallback locales, `locale`/`fallbackLocale` queries, admin i18n.
- `skills/data-management/` — Trash (`trash: true` + `deletedAt`), Query Presets (`enableQueryPresets`), Folders (`folders: true`), Group By (`admin.groupBy`).
- `skills/admin-customization/` (+ `references/component-slots.md`, `references/react-hooks.md`) — custom RSC/client components, custom views, dashboard widgets, admin React hooks, document locking, CSS.
- `skills/official-plugins/` (+ `references/plugin-catalog.md`) — installing/configuring `@payloadcms/plugin-*` (SEO, form-builder, nested-docs, search, stripe, multi-tenant, redirects, sentry, import-export, MCP) + Ecommerce plugin.
- `skills/deployment/` — production build, Vercel/Docker/self-host, building without a DB (`next build --experimental-build-mode compile`), preventing API abuse, performance.
- `skills/jobs-queue/SKILL.md` — added a "Declarative job schedules (`schedule`)" subsection.
- Updated README (16 → 23 skills), the `payloadcms-developer` agent (skill list + routing table), `plugin.json` + `marketplace.json` (v1.1.0, expanded description, new keywords).
**Rationale:** v1.0.0 had no dedicated coverage for localization, authentication strategies, globals, admin/custom components, official plugins, deployment, or the 2025 data features (trash/presets/folders/group-by) — all first-class Payload areas. A gap analysis against `llms.txt` confirmed these were the only missing top-level topics.
**Research note:** Payload v3 **removed** the v2 top-level `rateLimit` buildConfig option (the docs property is flagged outdated in payloadcms/payload#10321); the `deployment` skill directs rate limiting to Next.js middleware / a reverse proxy instead. The official `production/building-without-db` URL 404s — the canonical v3 mechanism is the Next.js `--experimental-build-mode` flag.

## [2026-08-09] — doc-alignment: docs-alignment pass vs Payload 3.87.1

**Feature:** Full accuracy pass against Payload 3.87.1 (npm `latest`, 2026-08-07) across 18 skills/references; version bumped to 1.2.0.
**Implementation:**
- `fields` — reworked the `import { slugField } from 'payload'` example around the website-template pattern (text field + `beforeValidate` hook). *Correction 2026-08-09: the core `slugField` export is real — payload@3.87.1 exports it from the main entry (present since at least 3.80.0), so `import { slugField } from 'payload'` compiles; it is `@experimental` and undocumented, which is why the DIY pattern remains the recommended stable path.* Added the `virtual: 'author.name'` string-path form (queryable virtual relationship fields) and the new per-field admin toggles `disableBulkEdit` / `disableGroupBy` / `disableListColumn` / `disableListFilter`. (Critical)
- `lexical-editor` — replaced the nonexistent `lexicalToHTML` + `populationPromises` API with `convertLexicalToHTML` (`@payloadcms/richtext-lexical/html`) and `convertLexicalToHTMLAsync` + `getPayloadPopulateFn` (`/html-async`), plus `getRestPopulateFn` and the "generally not recommended" `lexicalHTMLField()` notes. (Critical)
- `adapters` — fixed the Azure export name (`azureStorage`, not `azureBlobStorage`; compile error), promoted GCS to the official `@payloadcms/storage-gcs` / `gcsStorage()`, added the new official `@payloadcms/storage-r2` (`r2Storage()`, Workers R2 bindings) and `@payloadcms/db-d1-sqlite` (`sqliteD1Adapter()`, Cloudflare D1), and noted 3.87.0 `chunkLargeFiles` >5GB Azure client uploads. (Major)
- `cli-recipes` + `graphql-api.md` — `generate:graphql-schema` does not exist on the `payload` bin; GraphQL schema generation is `pnpm payload-graphql generate:schema` (`@payloadcms/graphql` bin). Added `payload run` (env-loading tsx script runner; replaces the `pnpm tsx` recipe), `generate:db-schema`, `payload info`, and `jobs:run` / `jobs:handle-schedules`. (Major)
- `jobs-queue` + `local-api.md` + `rest-api.md` — corrected the run endpoint to `GET /api/payload-jobs/run?limit&queue&allQueues` gated by `jobs.access.run` + CRON_SECRET (was `POST` + `Authorization: JWT`; *correction 2026-08-09: the endpoint registers only `method: 'get'` — plain POST never reaches the handler, only via the `X-Payload-HTTP-Method-Override: GET` header*); documented bin-script workers, `handle-schedules` endpoint, `payload.jobs.runByID/cancel/cancelByID/handleSchedules`, `processingOrder` (FIFO/LIFO per queue), `shouldAutoRun(payload)`, `disableScheduling`, `payload-jobs-stats` global, seconds-precision cron, required `queue` in ScheduleConfig, and the schedulePublish⇄jobs-runner dependency. (Major)
- `nextjs-integration` / `setup` / `scaffold` / README — Next.js support is 15/16 (`>=15.2.9` tested minors, `>=16.2.6 <17`); Next 14 is no longer supported. Node engines are `^18.20.2 || >=20.9.0` (20 LTS+ recommended, not a hard 20.9 floor); Slate adapter exists for v2 migration (lexical is default/recommended, not "only supported"). (Major)
- `globals` — REST global update is `POST /api/globals/{slug}`, not PATCH. (Major)
- `local-api.md` — removed nonexistent `payload.logout` (logout/refresh are `@payloadcms/next/auth` server functions); added `payload.findDistinct`, `restoreGlobalVersion`, and the `trash` / `select` / `populate` universal options. (Major)
- `admin-customization` (+ component-slots) — added the new Dashboard Widgets capability (`admin.dashboard.widgets` + `defaultLayout`, built-in collections widget auto-included). (Major)
- Minor folds: `qs-esm` replaces `qs` in queries/REST examples; REST `select`/`populate`/`joins`/`trash` params; `@payloadcms/sdk` noted as the official typed REST client; `disableBulkDelete` + `livePreview.openByDefault` (3.86); queryPresets `filterConstraints`/`labels`; folders `collectionOverrides` + per-collection object form; MCP plugin options refresh (per-collection `overrideResponse`/`description`, `overrideApiKeyCollection`, `overrideAuth`, `mcp.handlerOptions`, `serverInfo`); Ecommerce plugin concrete Beta facts (required `access`/`customers`, Addresses collection, `stripeAdapter`, no native shipping/taxes/subscriptions); form-builder translations (3.86); `templates/plugin` starter mention; extra repo templates noted.
**Rationale:** Last alignment was 2026-06-16 (~v3.85.1). Releases 3.85.2→3.87.1 plus doc restructuring introduced one compile-breaking fabrication (lexicalToHTML — slugField was initially also flagged as fabricated but turned out to be a real, `@experimental` core export; corrected 2026-08-09) and one wrong export (azureBlobStorage), stale CLI/jobs surfaces, and outdated Next/Node support claims. Payload 4.0 is in canary (admin redesign, hierarchies in core, TanStack adapter) — this plugin continues to target the stable v3 line; revisit folders/data-management and admin-customization when 4.0 ships.

## [2026-08-09] — fact-check: corrections from adversarial doc verification

**Problem:** Two claims from the v1.2.0 doc-alignment pass were refuted against the payload@3.87.1 tarball: (1) `fields/SKILL.md` (and the v1.2.0 LEARNINGS entry) flatly stated "Payload core does not export a `slugField` helper" / "would not compile" — in fact `payload` re-exports `slugField` from its main entry since at least 3.80.0 (a `RowField` with a slug text field + `generateSlug` checkbox; options `name`/`useAsSlug`/`slugify`/`disableUnique`/`checkboxName`/`overrides`), just JSDoc-tagged `@experimental` and undocumented; (2) `jobs-queue/SKILL.md` and `api-reference/references/rest-api.md` documented the jobs run endpoint as "GET or POST /api/payload-jobs/run" — the endpoint registers only `method: 'get'`, and core dispatch skips non-matching methods, so plain POST never reaches the handler (POST works only via the `X-Payload-HTTP-Method-Override: GET` header).
**Fix:** Reworded the slug section: core `slugField` export acknowledged as real-but-experimental/undocumented, DIY website-template pattern kept as the recommended stable path with an explicit note that the local helper shadows the core export; changed "GET or POST" to "GET" in both jobs files with the method-override note; amended the v1.2.0 LEARNINGS wording (slugField was not a fabrication; run endpoint is GET-only). Version 1.2.0 → 1.2.1.
**Root cause:** The v1.2.0 alignment relied on the official v3 docs, where `slugField` is absent (undocumented `@experimental` export — docs absence was mistaken for code absence), and generalized the run endpoint's method from the override-header mechanism instead of checking the registered `method: 'get'` in `dist/queues/endpoints/run.js`.
**Severity:** Major
