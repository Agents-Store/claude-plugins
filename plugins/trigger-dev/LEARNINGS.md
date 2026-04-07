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
