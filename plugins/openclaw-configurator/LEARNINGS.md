# Learnings

## 2026-05-22 — v1.6.0: upgrade reconciliation, provider-auth, infisical-migration

**Feature:** Four capability additions plus a DRY refactor, all grounded against live docs (docs.openclaw.ai, infisical.com/docs/cli) at planning time.

1. **Upgrade intelligence (Goal 1).** New `release-migration` skill turns a code update into a config update: read `CHANGELOG.md` between tags + `git log` + release notes (via docs-research), recommend new features (opt-in), migrate deprecated/legacy settings (e.g. legacy model refs `openai-codex/*`,`codex-cli/*`,`claude-cli/*`), then run `openclaw doctor --fix`. Wired into `/instance-update` as a new mandatory Step 11 (steps renumbered 11→13) and exposed standalone via `/config-validate --upgrade-from <tag>`.
2. **Provider auth (Goal 2).** New `provider-auth` skill + `/provider-setup` command. OAuth/CLI-backend-first, cost-saving bias: route chat through a local Claude/Codex CLI subscription session (`agentRuntime.id: "claude-cli"`, Codex ChatGPT OAuth) instead of metered API tokens; reserve API keys for functions/skills needing the embedded API. Interactive logins are printed for the user to run via the `!` prefix (never run browser OAuth in-session). Documents the `auth-profiles.json` precedence gotcha (embedded-API `mode:"token"` profile blocks the CLI backend).
3. **Centralized doc research (Goal 3).** New `docs-research` skill is the single source of truth for the tool-priority ladder (Firecrawl → Exa → Perplexity → Jina → context7 → WebFetch) and the OpenClaw doc URL map. Replaced 4 duplicated inline blocks (config-validate, config-validation, openclaw-config, assistant agent) + the auditor agent with a pointer.
4. **Infisical migration (Goal 4).** New `infisical-migration` skill (full server-side playbook) + `/infisical-migrate` command (prompt project id → enumerate keys → `infisical secrets set` push → patch Dockerfile/compose/wrapper → rebuild → strip plaintext + auth-profiles `keyRef` → `openclaw secrets audit --check`). OAuth/CLI creds stay in OpenClaw's encrypted store — out of scope.

**Files changed:** new `skills/{docs-research,provider-auth,release-migration,infisical-migration}/SKILL.md` (+ evals), new `commands/{provider-setup,infisical-migrate}.md`, modified `commands/{instance-update,config-validate}.md`, `agents/{openclaw-configurator-assistant,openclaw-workspace-auditor}.md`, `plugin.json` + `marketplace.json` (1.5.0 → 1.6.0), root `.env.example`.

**Root cause:** v1.5.0 updated code but never reconciled config; documented `provider/model` strings but not authentication; duplicated the doc-fetch ladder 4×; and had no path from plaintext `.env` to Infisical despite a proven manual playbook existing.

**Severity:** Major (new capabilities + removes a maintenance footgun)

## 2026-05-22 — Separate OPENCLAW_INSTANCE_DIR from OPENCLAW_PROJECT_DIR

**Problem:** v1.4.0 collapsed two distinct concepts onto a single `OPENCLAW_PROJECT_DIR` env var: the git/docker-compose project dir (e.g. `<compose-root>/openclaw-<name>/`) and the runtime instance dir holding `openclaw.json` + `workspace/` (e.g. `~/.openclaw-<name>/`). For Docker deployments these are **different** paths. Workspace commands (`workspace-scan`, `config-validate`, `workspace-optimize`) followed `OPENCLAW_PROJECT_DIR` and looked for `openclaw.json` inside the source repo, where it doesn't exist — so users with split layouts couldn't validate/scan/optimize their instance without `cd`-ing into `~/.openclaw-{name}/` first, defeating the whole point of the env var.

**Fix:** Introduced `OPENCLAW_INSTANCE_DIR` and split responsibilities:

- **Workspace-aware commands + permission hook**: resolve via `"${OPENCLAW_INSTANCE_DIR:-${OPENCLAW_PROJECT_DIR:-$(pwd)}}"`. This means `OPENCLAW_INSTANCE_DIR` is the primary control; `OPENCLAW_PROJECT_DIR` is only used as a fallback for backward compatibility with v1.4.0 setups where both happened to coincide.
- **`instance-update` command**: keeps using `OPENCLAW_PROJECT_DIR` only — it needs the git checkout, not the instance.
- **Docker permission fix** (in `workspace-optimize` step 9 and hook): instance NAME is derived from the instance dir, but `cd` for `docker compose` uses `OPENCLAW_PROJECT_DIR` because that's where `docker-compose.yaml` lives.

**Files changed:** commands/workspace-scan.md, commands/config-validate.md, commands/workspace-optimize.md, hooks/hooks.json, skills/workspace-overview/SKILL.md, plugin.json (1.4.0 → 1.5.0), marketplace.json (version bump), root CLAUDE.md (Path-anchored plugins section).

**Root cause:** v1.4.0 modeled OpenClaw as "one dir per instance" but real Docker deployments separate **source** (project) from **runtime state** (instance). One env var couldn't express both.

**Severity:** Major (workspace commands broken for split-layout users)

## 2026-05-16 — Honor OPENCLAW_PROJECT_DIR env var across all instance-aware commands

**Problem:** Every instance-aware command (`workspace-scan`, `workspace-optimize`, `instance-update`, `config-validate`) and the `PostToolUse` permission-fix hook derived the active instance from `$(pwd)`. That forced the user to `cd <compose-root>/openclaw-<name>` before invoking Claude Code, which broke any workflow where Claude Code is launched from a sibling project (e.g. the plugin monorepo for testing) but should operate on a specific OpenClaw instance.

**Fix:** Introduced `OPENCLAW_PROJECT_DIR` env var. Every command and the hook now resolves the target via `"${OPENCLAW_PROJECT_DIR:-$(pwd)}"`. When the var is set the command `cd`s into it and derives `INSTANCE_NAME` / docker-compose context from there; when unset, behavior is identical to v1.3.0.

**Files changed:** commands/workspace-scan.md, commands/workspace-optimize.md, commands/instance-update.md, commands/config-validate.md, hooks/hooks.json.

**Root cause:** Commands conflated "the agent's shell context" with "the OpenClaw instance to operate on". Decoupling the two via an env var is a cleaner contract and matches how other monorepo plugins expose configuration.

**Severity:** Minor

## 2026-04-05 — instance-update: Tag-based update command for multi-instance Docker deployments

**Feature:** New `/openclaw-configurator:instance-update` command that fetches the latest official release tag, merges it into the local `dev` branch preserving customizations, and rebuilds Docker containers.
**Implementation:** Created `commands/instance-update.md` — 12-step workflow with pre-flight checks, docker-compose backup, tag-based merge, conflict resolution strategy (auto-accept upstream for source, manual merge for docker-compose), syntax validation, container rebuild and verification.
**Rationale:** OpenClaw instances run as git clones with a local `dev` branch holding per-project docker-compose customizations. Updates require merging tagged releases (not branch tracking) while preserving these local changes. Modeled after `dify-ops/commands/update.md` but adapted for tag-based releases and docker-compose-centric customizations (vs Dify's .env-centric approach).
