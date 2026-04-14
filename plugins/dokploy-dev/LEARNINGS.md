# LEARNINGS.md — dokploy-dev

## 2026-04-14 — deploy + status commands: Docker Compose build mode not detected

**Problem:** When a Dokploy project uses Docker Compose build mode (production runs from a compose service, not the standalone application), the deploy command only deployed the standalone application. The push auto-deploy webhook was also connected to the application, not the compose service. This caused the deployment to report "done" while the production site remained unchanged — a silent failure.
**Fix:** Updated `deploy.md` to detect Docker Compose build mode by checking if the project has a compose service alongside the application. If compose exists, it warns the user and deploys the compose service using `compose-deploy` MCP tool or REST API fallback. Updated `status.md` to show both application and compose service status, and flag auto-deploy misconfiguration.
**Root cause:** The deploy command assumed all projects use standalone application mode. Projects using `docker-compose.prod.yml` need compose-level deployment, not application-level.
**Severity:** Critical

## 2026-04-09 — mcp-patterns: Auth header, GitHub provider repo field, Git provider required fields

**Problem:** (1) REST API fallback section was missing — when MCP tools fail, users need curl examples with correct `x-api-key` header (not Bearer). (2) `saveGithubProvider` `repository` field was ambiguous — passing a full URL (`https://github.com/org/repo`) caused Dokploy to create a broken double-URL clone path (`github.com/org/https://github.com/org/repo`). This caused 4 failed deployments before root cause was found. (3) `saveGitProvider` table was missing required fields `customGitBuildPath` and `watchPaths`, causing 400 validation errors.
**Fix:** Added REST API fallback section with `x-api-key` auth examples (GET/POST/health). Added explicit warning that `repository` for GitHub provider must be repo name only, never full URL. Documented all required fields for `saveGitProvider` and `saveGithubProvider` including `githubId` (from `gitProvider.getAll`), `enableSubmodules`, `triggerType`, `watchPaths`, `buildPath`. Added `x-api-key` vs Bearer error to error handling table.
**Root cause:** GitHub provider constructs clone URL from `{owner}/{repository}` — the API schema says "URL or name" which is misleading. Auth header was documented as Bearer in earlier version but Dokploy uses x-api-key. Git provider required fields were not tested end-to-end.
**Severity:** Critical

## 2026-04-06 — deploy command + mcp-patterns + troubleshoot: 5 fixes from real deployment session

**Problem:** (1) MCP tools failed with "Invalid URL" when env vars weren't passed through — no fallback guidance. (2) Deploy command didn't mention setting env vars or build args. (3) Deploy command didn't monitor deployment to completion or iterate on failures. (4) No guidance on reading deployment logs (had to use Beszel as workaround). (5) Default build type was nixpacks but project had Dockerfile — should ask user and default to dockerfile.
**Fix:** Updated deploy command with pre-deploy checks (env vars, build type) and monitoring loop. Updated mcp-patterns with correct required parameters for `saveEnvironment` (buildArgs, buildSecrets, createEnvFile) and `saveBuildType` (dockerfile, dockerContextPath, etc.). Fixed troubleshoot auth header from `Authorization: Bearer` to `x-api-key`. Added MCP "Invalid URL" fallback to troubleshoot. Added deployment log reading via Beszel.
**Root cause:** Initial skills were written from API docs without testing a real end-to-end deployment. Required parameters for saveEnvironment and saveBuildType were undocumented. Auth header was assumed to be Bearer but Dokploy uses x-api-key.
**Severity:** Critical

## 2026-04-04 — all skills: Prompting quality improvements

**Problem:** Skill descriptions used "Use when..." format instead of required third-person "This skill should be used when...". Agent examples lacked commentary. `examples/references/scenarios/` was 2 levels deep (max 1). api-reference SKILL.md was 104 lines (must be under 100). Reference files over 100 lines lacked table of contents.
**Fix:** Updated all 6 skill descriptions to third-person format. Added commentary to 3 agent examples. Flattened scenarios/ dir up one level. Trimmed api-reference from 104 to 62 lines. Added TOC to all 8 reference files over 100 lines.
**Root cause:** Initial generation didn't follow all Agents Store prompting quality conventions from the validation checklist.
**Severity:** Minor

## 2026-04-04 — commands: Add slash commands for standard operations

**Problem:** Plugin had no slash commands — users had to describe operations in natural language or remember MCP tool names.
**Fix:** Added 8 commands: list-projects, create-project, list-apps, create-app, deploy, status, create-db, add-domain. Each with argument parsing, project/app name resolution, and usage examples.
**Root cause:** Initial plugin creation focused on skills and agent, skipped commands component.
**Severity:** Major
