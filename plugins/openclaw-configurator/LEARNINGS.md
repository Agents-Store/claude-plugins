# Learnings

## 2026-05-16 — Honor OPENCLAW_PROJECT_DIR env var across all instance-aware commands

**Problem:** Every instance-aware command (`workspace-scan`, `workspace-optimize`, `instance-update`, `config-validate`) and the `PostToolUse` permission-fix hook derived the active instance from `$(pwd)`. That forced the user to `cd /docker/openclaw-<name>` before invoking Claude Code, which broke any workflow where Claude Code is launched from a sibling project (e.g. the plugin monorepo for testing) but should operate on a specific OpenClaw instance.

**Fix:** Introduced `OPENCLAW_PROJECT_DIR` env var. Every command and the hook now resolves the target via `"${OPENCLAW_PROJECT_DIR:-$(pwd)}"`. When the var is set the command `cd`s into it and derives `INSTANCE_NAME` / docker-compose context from there; when unset, behavior is identical to v1.3.0.

**Files changed:** commands/workspace-scan.md, commands/workspace-optimize.md, commands/instance-update.md, commands/config-validate.md, hooks/hooks.json.

**Root cause:** Commands conflated "the agent's shell context" with "the OpenClaw instance to operate on". Decoupling the two via an env var is a cleaner contract and matches how other monorepo plugins expose configuration.

**Severity:** Minor

## 2026-04-05 — instance-update: Tag-based update command for multi-instance Docker deployments

**Feature:** New `/openclaw-configurator:instance-update` command that fetches the latest official release tag, merges it into the local `dev` branch preserving customizations, and rebuilds Docker containers.
**Implementation:** Created `commands/instance-update.md` — 12-step workflow with pre-flight checks, docker-compose backup, tag-based merge, conflict resolution strategy (auto-accept upstream for source, manual merge for docker-compose), syntax validation, container rebuild and verification.
**Rationale:** OpenClaw instances run as git clones with a local `dev` branch holding per-project docker-compose customizations. Updates require merging tagged releases (not branch tracking) while preserving these local changes. Modeled after `dify-ops/commands/update.md` but adapted for tag-based releases and docker-compose-centric customizations (vs Dify's .env-centric approach).
