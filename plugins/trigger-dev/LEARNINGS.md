# Trigger.dev Plugin Learnings

## 2026-04-07 — setup/deployment: Missing per-environment connection keys and project ref

**Problem:** Plugin documented only 3 env vars (TRIGGER_SECRET_KEY, TRIGGER_API_URL, TRIGGER_ACCESS_TOKEN). No guidance on storing separate keys per environment (dev/staging/production) or project ref as an env var.
**Fix:** Added recommended convention: TRIGGER_DEV_SECRET_KEY, TRIGGER_STAGE_SECRET_KEY, TRIGGER_PROD_SECRET_KEY for per-env key storage, and TRIGGER_PROJECT_REF for project identifier. Updated environment-setup.md reference, setup/SKILL.md, README.md, and deployment/SKILL.md with complete 7-var tables and .env examples.
**Root cause:** Official Trigger.dev docs use a single TRIGGER_SECRET_KEY with value swapping per env. Plugin lacked a practical convention for managing multiple environments simultaneously.
**Severity:** Major

## 2026-04-07 — setup/deployment: Remove TRIGGER_SECRET_KEY in favor of per-env keys

**Problem:** TRIGGER_SECRET_KEY was still listed alongside TRIGGER_DEV_SECRET_KEY, TRIGGER_STAGE_SECRET_KEY, TRIGGER_PROD_SECRET_KEY, creating redundancy. The per-env vars replace TRIGGER_SECRET_KEY entirely.
**Fix:** Removed TRIGGER_SECRET_KEY from all tables and .env examples. Updated SDK configure() examples to use per-env vars directly.
**Root cause:** First iteration kept the official var alongside convention vars; the convention vars fully replace it.
**Severity:** Minor

## 2026-04-09 — deployment: Missing --api-url flag and post-deploy verification

**Problem:** Self-hosted deploy section said "ensure you're logged in" but didn't show the `--api-url` flag. Agent tried non-existent `--self-hosted` flag. Also, no guidance to verify tasks after deploy — env var issues caused silent runtime failures (`undefined` in URLs).
**Fix:** Rewrote self-hosted deploy section with explicit `--api-url` and `TRIGGER_ACCESS_TOKEN` examples. Added complete deploy flags table. Added "Post-Deploy Verification" section requiring trigger + log check for every deploy.
**Root cause:** Skill assumed cloud-centric workflow where login profiles handle routing. Self-hosted needs explicit `--api-url`. Skill also had no verification step — deploy success != runtime success.
**Severity:** Major

## 2026-04-09 — config-and-build: syncEnvVars not flagged as required, missing @trigger.dev/build dependency

**Problem:** `syncEnvVars` was documented as just another optional extension. No warning that without it, `process.env` vars are `undefined` at runtime. Also, no mention that `@trigger.dev/build` package must be installed before using any extensions — deploy fails with module not found error.
**Fix:** Added install instruction for `@trigger.dev/build` at top of Build Extensions section. Rewrote syncEnvVars section with bold warning that it's required for any task using `process.env`, added practical pattern for syncing from `.env` file.
**Root cause:** Skill treated env var sync as a nice-to-have rather than a deployment prerequisite. The `@trigger.dev/build` dependency was assumed to be pre-installed.
**Severity:** Critical
