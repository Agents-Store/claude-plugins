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
