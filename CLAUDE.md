# CLAUDE.md

CLAUDE PLUGIN PUBLIC

This file provides guidance to Claude Code when working with code in this repository.

## Repository Purpose

A monorepo of **public Claude Code plugins** for the AGENTS.STORE marketplace. Each plugin lives in `plugins/<name>/` and provides agents, skills, commands, and optionally MCP server configs to extend Claude Code for a specific platform or workflow.

A private companion repo (`claude-plugins-private`) contains the `plugin-creator` toolchain and internal plugins.

## Plugin Architecture — 4 Levels

| Level | Type | Naming | Has MCP? | Scope |
|-------|------|--------|----------|-------|
| 1 | Technology | `{tool}-{process}` | No | User |
| 1.5 | Process | `{name}-{process}` | Yes (OAuth) | User |
| 2 | Stack | `stack-{name}-{process}` | Yes (`${VAR}`) | Project |
| 3 | Project | CLAUDE.md, .claude/rules/ | — | Project |

Process suffixes:
- **dev** — for developers (API, SDK, CLI, code patterns)
- **ops** — for business users (data entry, views, reports, CRUD)
- **provision** — for admins (schema design, roles, migrations, setup)

**Technology plugins MUST NOT have .mcp.json or environment variables.** They contain only file-based knowledge.

## Plugin Anatomy

```
plugins/<name>/
├── .claude-plugin/plugin.json   # Manifest (required)
├── .mcp.json                    # MCP connections (Stack/Process only)
├── skills/                      # Knowledge blocks
│   └── skill-name/
│       ├── SKILL.md             # Frontmatter + instructions
│       ├── references/          # Supporting docs
│       └── evals/               # Per-skill test cases (skill-creator format)
│           └── evals.json       # In git. workspace/ in .gitignore
│   └── examples/                # Convention: scenario walkthroughs
│       ├── SKILL.md
│       └── references/scenarios/
├── commands/                    # Slash commands (.md)
├── agents/                      # Agent definitions (.md)
├── hooks/                       # Optional: hooks.json
├── rules/                       # Optional: .claude/rules
├── LEARNINGS.md                 # Accumulated feedback and fixes (in git)
└── README.md
```

## File Formats

### plugin.json
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "...",
  "author": { "name": "AGENTS.STORE" },
  "keywords": ["tag1", "tag2"],
  "mcpServers": "./.mcp.json"       // Only for Stack/Process plugins
}
```

### SKILL.md frontmatter
```yaml
---
name: skill-name
description: When/why to trigger this skill
disable-model-invocation: true      # For reference-only or manual skills
---
```

### Command frontmatter
```yaml
---
description: What this command does
argument-hint: [arg-names]
allowed-tools: [Read, Write, Edit, Bash, Skill, Agent]
---
```

### Agent frontmatter
```yaml
---
name: agent-name
description: |
  Multi-line description with <example> blocks
tools: mcp__prefix__*
model: sonnet
---
```

### Hooks
`hooks/hooks.json` must use record style: `{ "hooks": { "PostToolUse": [...] } }` — not array at root.

## LEARNINGS.md

Each plugin has a `LEARNINGS.md` in its root. Accumulates all fixes and discoveries. Format:

```markdown
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

**In git** — it's documentation. Created empty by hand for new plugins. Filled automatically by `plugin-creator:feedback` and `plugin-creator:wrap-up` from the private marketplace's plugin-creator.

## evals/

Test cases for Anthropic's `skill-creator` plugin. Located **per-skill** (not per-plugin):

```
skills/<skill-name>/evals/evals.json    # In git — skill_name matches skill frontmatter
skills/<skill-name>/evals/workspace/    # In .gitignore — generated outputs
```

Format follows the official skill-creator schema:
```json
{
  "skill_name": "<skill-frontmatter-name>",
  "evals": [
    { "id": 1, "prompt": "...", "expected_output": "...", "files": [], "expectations": [] }
  ]
}
```

Created automatically when skill-creator first tests a skill.

## Marketplace Registry

`.claude-plugin/marketplace.json` is the central index. Every new plugin must be added here with `name`, `source`, `description`, `version`, `author`, `keywords`, and `category`.

## Creating a New Plugin

1. Research the target platform's official docs before writing
2. Create directory structure under `plugins/<name>/`
3. Create `.claude-plugin/plugin.json` manifest
4. Add agents, commands, skills (always include an `examples` skill with scenario walkthroughs)
5. For MCP plugins: add `.mcp.json` with placeholder URL
6. Create empty `LEARNINGS.md`
7. Register in `.claude-plugin/marketplace.json`

Or use `plugin-creator` from the private marketplace: `/plugin-creator:create`

## Patterns Worth Knowing

- **CONNECTORS pattern** (see `deep-research`): Uses `~~capability` placeholders instead of hard-coding tool names. Agents try providers in fallback order.
- **Tool name indirection**: Skills reference generic tool names. Agents discover actual MCP tool names at runtime.
- **Placeholder URLs**: `.mcp.json` uses placeholders (e.g. `https://your-instance.com/mcp`). Users replace with their own.
- The root `.mcp.json` is gitignored — contains real endpoints for local dev only.

## Cross-Repo Plugin Source Access

The `plugin-creator` plugin routes feedback to the correct repo via env vars:

| Variable | Points to |
|----------|-----------|
| `PLUGINS_PUBLIC_SOURCE_DIR` | This repo's plugins directory |
| `PLUGINS_PRIVATE_SOURCE_DIR` | Private marketplace plugins directory |

Skills check **both** directories to find a plugin automatically.

## Skill Improvement System

Three methods for improving plugin skills:

1. **Human feedback** — `/plugin-creator:feedback` during work → fix SKILL.md → LEARNINGS.md → commit
2. **GitHub CI** — Issue with label `skill-improvement` → GitHub Action runs Claude → PR
3. **Session scanner** — `/plugin-creator:scan-sessions` → grep .jsonl logs → create Issues → CI fixes

GitHub Action workflow: `.github/workflows/improve-skills.yml`

## Commit Convention

```
feat(<plugin>): <description>
fix(<plugin>): <description>
chore(<plugin>): <description>
```

## Key Conventions

- Skill names: kebab-case, unique within a plugin
- Commands: `/plugin-name:command-name`
- Tool references: `mcp__server-id__tool-name`
- Agent descriptions must include trigger examples
- Skills with `disable-model-invocation: true` are context-only
- Complex skills use `references/` subdirectories
- Bump version in **both** `plugin.json` and `marketplace.json`

## Local Testing

The repo ships an env-driven test harness. Real secrets live in **Infisical** — instance `https://k.macstack.ai`, project **`claude-plugins`** (`5374e01e-dd78-494c-a589-b29c5dd431bf`, pinned in `.infisical.json`). Files involved:

| File | Committed? | Purpose |
|------|------------|---------|
| `.env.example` | yes | documentation — full catalogue of every var any plugin or `.mcp.json` needs |
| `.env` | **no** | real values, generated by `secrets-pull.sh` — for shell tools (`docker compose`, `nb`, `gws`, `openclaw doctor`, …) |
| `.env.bak` | **no** | previous `.env`, kept automatically by each pull |
| `.mcp.json` | yes | aggregated MCP catalog; only `${VAR}` references |
| `.claude/settings.json` | yes | enables project MCPs + permissions, no env block |
| `.claude/settings.local.json` | **no** | env-block with real values, generated by `secrets-pull.sh`; also holds personal permissions / plugin dirs |

### How `${VAR}` in `.mcp.json` resolves

Claude Code merges env from `settings.json` → `settings.local.json` → OS env, then expands `${VAR}` in `.mcp.json` from the result. The **`env` block in `.claude/settings.local.json` is the source of truth for the session** — you do not need to `source .env` before launching `claude`. `.env` exists only for shell tooling outside Claude Code. Both are written from the same fetch, so they cannot drift apart.

### The three scripts

| Script | Direction | Default |
|--------|-----------|---------|
| `scripts/secrets-pull.sh` | Infisical → `.env` + `settings.local.json` | writes both |
| `scripts/secrets-push.sh` | `.env` → Infisical | **dry-run** (needs `--yes`) |
| `scripts/secrets-audit.sh` | read-only | reports drift, prints no values |

`scripts/setup.sh` still works — it is an alias for `secrets-pull.sh` with the same argument order. Slash commands: `/setup-tokens`, `/secrets-push`, `/secrets-audit`.

### Workflow

```bash
# 1. Pull secrets from Infisical into both .env and the settings.local.json env block.
#    Positional args (all optional): <env> [env-file] [settings-file]
./scripts/secrets-pull.sh              # == dev .env .claude/settings.local.json

# 2. Launch (or restart) Claude Code — the env block is read at startup.
claude

# 3. Inside Claude Code, verify MCPs:
#    /mcp        — every server in .mcp.json should connect

# Changed or added a value locally? Send it back up, or the next pull discards it:
./scripts/secrets-push.sh                  # dry-run: shows NEW / UPDATE / SKIPPED
./scripts/secrets-push.sh --all-envs --yes # dev + staging + prod (kept identical here)

# Not sure what is out of sync:
./scripts/secrets-audit.sh
```

Pull **merges** into the existing `env` block of `settings.local.json` (permissions, plugin dirs and everything else survive), so it is safe to re-run.

### Guard rails

Both directions refuse to replace a **real** value with a **placeholder** (`replace-me`, `your-…example.com`, empty):

- pull stops with **exit 3** and names the keys — push them up first, or re-run with `--force`
- push **skips** those keys and says so — `--force` to override
- a failed or empty Infisical fetch never touches the destination files
- push is an upsert: dropping a key from `.env` does not delete it in Infisical
- pushed secrets go through a mode-600 temp file, never argv, so they stay out of `ps`

The Infisical CLI keeps one **active** instance and `infisical secrets` always reads it — `--domain` does not switch it. The scripts detect this and run `infisical login --domain=…` when the active instance is not ours. Override for one run with `INFISICAL_DOMAIN=https://…`.

### Path-anchored plugins (OpenClaw)

`openclaw-configurator` honors two env vars that target a specific OpenClaw deployment regardless of CWD:

| Var | What it points to | Used by |
|-----|-------------------|---------|
| `OPENCLAW_INSTANCE_DIR` | Runtime instance dir (`openclaw.json`, `workspace/`, `agents/`, etc.) — typically `~/.openclaw-{name}/` | `workspace-scan`, `config-validate`, `workspace-optimize`, permission-fix hook |
| `OPENCLAW_PROJECT_DIR` | Git/docker-compose project dir — typically `/docker/openclaw-{name}/` | `instance-update`; also `docker compose` working dir when fixing permissions |

For Docker deployments these are **different** paths. Workspace-aware commands resolve in this order:

```
OPENCLAW_INSTANCE_DIR  >  OPENCLAW_PROJECT_DIR  >  $(pwd)
```

Set them in Infisical (or hand-add to the `env` block of `settings.local.json`). When both are unset, everything falls back to `$(pwd)` and the legacy single-dir layout still works.

### Adding a new env var

1. Add the var name + a placeholder line to `.env.example`, in the section for its consumer.
2. Reference it as `${VAR_NAME}` in the plugin's `.mcp.json` / skills / commands.
3. Put the real value in `.env`, then `./scripts/secrets-push.sh --all-envs --yes` to send it
   to Infisical (or add it in the Infisical UI and skip to step 4).
4. `./scripts/secrets-pull.sh` so `.env` and the settings env block match, then restart Claude Code.
5. `./scripts/secrets-audit.sh` should report it as satisfied.
6. Never commit real values — `.env`, `.env.bak` and `.claude/settings.local.json` are gitignored.