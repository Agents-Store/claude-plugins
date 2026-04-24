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

## 2026-04-24 — mcp-patterns/observability/managed-prompts: Upgrade plugin to trigger.dev v4.4.4 (33 MCP tools)

**Feature:** Document the full 33-tool catalogue of the Trigger.dev MCP server as of v4.4.4 — the 11 new v4.4.4 tools (profile, query/analytics, dev server, span details, task schema) plus the 7 Managed Prompts tools confirmed by tool-schema introspection. Add two dedicated skills (`observability`, `managed-prompts`) for the feature areas with the most new surface.

**Implementation:**
- `skills/mcp-patterns/SKILL.md` + `references/mcp-tools-reference.md` — 9 tool sections now (added Profile, Query & Analytics, Dev Server, Managed Prompts); split `get_current_worker` + `get_task_schema`; added `get_span_details`, pagination for `get_run_details`, `install-mcp` flags, annotations note.
- `skills/observability/SKILL.md` + `references/trql-reference.md` — new skill covering TRQL, `runs`/`metrics`/`llm_metrics` tables, SDK + REST API usage, dashboards, automatic LLM cost tracking.
- `skills/managed-prompts/SKILL.md` + `references/managed-prompts-reference.md` — new skill covering the slug/version/override model, all 7 MCP tools, hotfix workflow; SDK-side stub marked TODO pending `/docs/prompts` publication.
- `skills/cli-recipes/SKILL.md`, `skills/setup/SKILL.md` — replaced old `mcp` wizard with `install-mcp` + full flag table; added platform-notifications flag.
- `skills/config-and-build/SKILL.md` — added task-level / global TTL defaults with precedence rule.
- `skills/task-development/SKILL.md` — added TTL section with per-trigger / task / global precedence.
- `skills/troubleshoot/SKILL.md` — added Query & Dashboards symptom table and MCP annotations tip.
- `skills/examples/SKILL.md`, `skills/examples/references/mcp/tool-patterns.md` — added dev-server lifecycle, TRQL analysis, LLM cost, profile switch, and prompt-override patterns.
- `agents/trigger-developer.md` — routed `observability` and `managed-prompts`, updated self-hosted note.
- `README.md` — extended skills table to 12 rows, updated tech stack + sources list.
- `plugin.json` + marketplace `version` bumped `1.1.0` → `1.2.0`; added `trql`, `managed-prompts`, `observability` keywords.

**Rationale:** Plugin documented only the pre-v4.4.4 14-tool MCP set. The live MCP server ships 33 tools — 11 added in v4.4.4 (profile, query/dashboards, dev server, span details, task schema) and 7 Managed Prompts tools that are live but not yet covered on trigger.dev/docs. Agents using the plugin against v4.4.4 instances lacked guidance on more than half of the available tools and were blind to the query/dashboards and prompt-override workflows entirely. This gap was surfaced by the user on 2026-04-24 with a pointer to the v4.4.4 changelog.

## 2026-04-22 — deployment/troubleshoot: Container registry login workflow missing for self-hosted staging/prod deploys

**Feature:** Document the full container registry login workflow for self-hosted Trigger.dev deploys — `docker login` (interactive + non-interactive via `--password-stdin`), the distinction between server-side `DEPLOY_REGISTRY_*` env vars and the client-side `DOCKER_REGISTRY_*` convention, registry credential verification, and CI/CD patterns with a `docker login` step before `trigger.dev deploy`.
**Implementation:**
- `skills/deployment/SKILL.md` — new "Container Registry Login (Self-Hosted Only)" section between "Self-Hosted Deploy" and "Self-Hosted Runtime Environment Variables"; updated CI/CD GitHub Actions snippet to include docker login step; added required secrets list.
- `skills/deployment/references/self-hosted-infrastructure.md` — expanded "Container Registry" section with server-side `DEPLOY_REGISTRY_*` table, client-side `DOCKER_REGISTRY_*` convention, htpasswd rotation steps, verification curl commands.
- `skills/deployment/references/ci-cd-patterns.md` — added docker login step to self-hosted GitHub Actions and staging+prod examples; added registry vars rows to Generic CI table.
- `skills/troubleshoot/SKILL.md` — replaced single "Push failed" row with four distinct error symptoms (`denied`, `unauthorized`, `no basic auth credentials`, `localhost:5000` pushes); added "Registry Push Failures (Self-Hosted)" sub-section with interactive + non-interactive login recipes and cred verification; updated Self-Hosted Issues row.
- Version bumped `1.0.4` → `1.1.0` in plugin.json and marketplace.json.
**Rationale:** Original deployment skill stated "The CLI automatically discovers the container registry from the server" but never explained that auth still depends on local Docker credentials. Users on fresh laptops and CI runners hit `unauthorized: authentication required` at the push step with no guidance. Also, the official `DEPLOY_REGISTRY_*` (server) vs ad-hoc `DOCKER_REGISTRY_*` (client) distinction was undocumented — leading users to think the CLI reads these env vars, which it doesn't. This gap was identified during a live deploy session (2026-04-22) where the agent had to research the workflow from scratch after the user asked what to do with `registry.trigger.multiagent.work` at staging/prod deploy time.
