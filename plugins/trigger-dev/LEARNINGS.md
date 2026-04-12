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

## 2026-04-13 — deployment: TRIGGER_SECRET_KEY as TRIGGER_ACCESS_TOKEN fallback for self-hosted

**Problem:** CLI profile token (PAT) couldn't find a project that exists on the self-hosted instance. MCP tools (using TRIGGER_SECRET_KEY) could see it. Agent spent multiple iterations debugging auth.
**Fix:** Added Option B to self-hosted deploy: use `TRIGGER_ACCESS_TOKEN=$TRIGGER_SECRET_KEY` when the CLI profile token lacks project access. Added diagnostic tip for "Project not found" error.
**Root cause:** Skill only documented PAT tokens for TRIGGER_ACCESS_TOKEN. On self-hosted instances, the project secret key also works as an access token and avoids org/permission mismatches.
**Severity:** Major

## 2026-04-13 — deployment: Runtime env vars not propagated by deploy.env on self-hosted

**Problem:** `deploy.env` in trigger.config.ts did not propagate env vars to self-hosted runtime containers. Tasks failed with `TypeError: Failed to parse URL from undefined/...`. Agent had to discover the REST API endpoint manually.
**Fix:** Added "Self-Hosted Runtime Environment Variables" section with REST API method (`POST /api/v1/projects/{ref}/envvars/{env}`) and dashboard UI alternative. Documented the common `undefined` URL symptom.
**Root cause:** Skill assumed `deploy.env` or `syncEnvVars` always works. On self-hosted, runtime env vars may need to be set via API or dashboard separately.
**Severity:** Critical

## 2026-04-13 — task-development: External SDK clients crash deploy when initialized at module top level

**Problem:** `const openai = new OpenAI()` at module level caused deploy to fail with "Missing credentials" because `OPENAI_API_KEY` is not available during the Docker build phase.
**Fix:** Added Critical Rule #6: lazy-initialize external SDK clients. Included bad/good code examples showing the singleton getter pattern.
**Root cause:** Trigger.dev imports and validates task files during the Docker build step. Any top-level code that reads env vars will fail because build-time env != runtime env.
**Severity:** Major
