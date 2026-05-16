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

The repo ships an env-driven test harness. Real secrets live in **Infisical** and are pulled to the machine via `scripts/setup.sh`. Files involved:

| File | Committed? | Purpose |
|------|------------|---------|
| `.env.example` | yes | documentation — full list of vars any plugin might need |
| `.env` | **no** | real values, generated by `setup.sh` — for shell tools (`docker compose`, `nb`, `openclaw doctor`, etc.) |
| `.mcp.json` | yes | aggregated MCP catalog; only `${VAR}` references |
| `.claude/settings.json` | yes | enables project MCPs + permissions, no env block |
| `.claude/settings.local.json` | **no** | env-block with real values, generated by `setup.sh`; also holds personal permissions / plugin dirs |

### How `${VAR}` in `.mcp.json` resolves

Claude Code merges env from `settings.json` → `settings.local.json` → OS env, then expands `${VAR}` in `.mcp.json` from the result. The **`env` block in `.claude/settings.local.json` is the source of truth for the session** — you do not need to `source .env` before launching `claude`. `.env` exists only for shell tooling outside Claude Code.

### Workflow

```bash
# 1. Pull secrets from Infisical into both .env and the settings.local.json env block.
#    Mode arg = Infisical environment (dev | staging | prod).
./scripts/setup.sh dev .env .claude/settings.local.json

# 2. Launch (or restart) Claude Code.
claude

# 3. Inside Claude Code, verify MCPs:
#    /mcp        — every server in .mcp.json should connect
```

`setup.sh` **merges** into the existing `env` block of `settings.local.json` (preserves permissions, plugin dirs, etc.), so it is safe to re-run.

### Path-anchored plugins (OpenClaw)

`openclaw-configurator` honors `OPENCLAW_PROJECT_DIR`. Set it in Infisical (or hand-add to the `env` block of `settings.local.json`) — commands like `/openclaw-configurator:workspace-scan` then target that instance regardless of CWD. When unset, behavior falls back to `$(pwd)`.

### Adding a new env var

1. Add the var name + a placeholder line to `.env.example`.
2. Add the real value to Infisical under the relevant environment.
3. Reference it as `${VAR_NAME}` in the plugin's `.mcp.json` / skills / commands.
4. Re-run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull it locally.
5. Never commit real values — `.env` and `.claude/settings.local.json` are gitignored.