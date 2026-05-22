# Learnings

## 2026-05-22 — Separate OPENCLAW_INSTANCE_DIR from OPENCLAW_PROJECT_DIR

**Problem:** v1.4.0 collapsed two distinct concepts onto a single `OPENCLAW_PROJECT_DIR` env var: the git/docker-compose project dir (e.g. `/docker/openclaw-pitline/`) and the runtime instance dir holding `openclaw.json` + `workspace/` (e.g. `~/.openclaw-pitline/`). For Docker deployments these are **different** paths. Workspace commands (`workspace-scan`, `config-validate`, `workspace-optimize`) followed `OPENCLAW_PROJECT_DIR` and looked for `openclaw.json` inside the source repo, where it doesn't exist — so users with split layouts couldn't validate/scan/optimize their instance without `cd`-ing into `~/.openclaw-{name}/` first, defeating the whole point of the env var.

**Fix:** Introduced `OPENCLAW_INSTANCE_DIR` and split responsibilities:

- **Workspace-aware commands + permission hook**: resolve via `"${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"`. This means `OPENCLAW_INSTANCE_DIR` is the primary control; `OPENCLAW_PROJECT_DIR` is only used as a fallback for backward compatibility with v1.4.0 setups where both happened to coincide.
- **`instance-update` command**: keeps using `OPENCLAW_PROJECT_DIR` only — it needs the git checkout, not the instance.
- **Docker permission fix** (in `workspace-optimize` step 9 and hook): instance NAME is derived from the instance dir, but `cd` for `docker compose` uses `OPENCLAW_PROJECT_DIR` because that's where `docker-compose.yaml` lives.

**Files changed:** commands/workspace-scan.md, commands/config-validate.md, commands/workspace-optimize.md, hooks/hooks.json, skills/workspace-overview/SKILL.md, plugin.json (1.4.0 → 1.5.0), marketplace.json (version bump), root CLAUDE.md (Path-anchored plugins section).

**Root cause:** v1.4.0 modeled OpenClaw as "one dir per instance" but real Docker deployments separate **source** (project) from **runtime state** (instance). One env var couldn't express both.

**Severity:** Major (workspace commands broken for split-layout users)

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
