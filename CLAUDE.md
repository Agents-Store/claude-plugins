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
7. Register in `.claude-plugin/marketplace.json` (exactly the 7 fields, version in sync with
   `plugin.json`)
8. Drop a `.scrub-strict` marker in the plugin root — every new plugin ships under the strict ruleset
9. Run `./scripts/scrub-check.sh plugins/<name>` — both passes must exit 0 before the plugin ships

Or use `plugin-creator` from the private marketplace: `/plugin-creator:create`

## Publication Gate

Everything in `plugins/` is published. `scripts/scrub-check.sh` runs **two passes** and blocks the
merge on either; it runs on every pull request (`.github/workflows/scrub.yml`).

```bash
./scripts/scrub-check.sh                  # whole repo    exit 0 clean · 1 fail · 2 warn
./scripts/scrub-check.sh plugins/<name>   # one plugin
./scripts/scrub-check.sh --strict <path>  # force the strict ruleset
./scripts/scrub-check.sh --no-lint <path> # content pass only, skip the structure pass
./scripts/plugin_lint.py plugins/<name>   # structure pass on its own
```

**Pass 1 — content (`scripts/scrub_check.py`).** Refuses: host and server names, private endpoints
and control-plane hostnames, routable IPv4 outside RFC 5737, instance names, deployment layout paths
with a literal segment, machine-identity file paths, home directories naming a person, UUIDs, bound
host ports, secret material, and personal identifiers. Rules are written as **shapes**, never as
literal values from a real deployment — a gate that hardcodes the strings it hunts becomes the leak
it was meant to stop. It scans tracked files **and** files not yet `git add`ed, so a brand-new plugin
cannot report clean simply by being invisible to `git ls-files`.

Four things the rules deliberately do NOT depend on, each of which was once a way through:

- **A vendor prefix.** `secret-material` knows a table of issued formats; `secret-kv` and
  `high-entropy` know the *shape* of a credential — a `…TOKEN/SECRET/KEY/PASSWORD =` name carrying a
  high-entropy value, and a bare mixed-case run of 40+ characters. A token whose prefix nobody
  listed is caught by shape. They over-fire on purpose: a false positive costs one reviewed baseline
  line, a miss costs a credential. Word-like identifiers, member expressions
  (`process.env.OPENAI_API_KEY` names a secret, it is not one), digests and `$ref` paths are filtered
  out, so the noise stays in the tens repo-wide, not the hundreds.
- **The file being text.** A binary is not skipped; its printable strings are pulled out and run
  through the reduced ruleset (`secret-material`, `secret-kv`, `home-path`, `identity-path`). A
  committed `.pyc` published the absolute source path of the machine that built it while the gate
  called the file clean — `home-path` is FAIL everywhere, and "everywhere" cannot have an exception
  carved out by file extension. `__pycache__` is likewise no longer skipped as a directory (and
  `.gitignore` keeps it out of the tree in the first place).
- **The language of the surrounding prose.** `INFRA_CONTEXT` carries Russian infrastructure stems
  as well as English ones — the LEARNINGS.md files here are Russian — and, more importantly, the
  rule no longer rests on prose at all: inside `plugins/` a non-allow-listed host that something is
  being **configured with** (`NAME=`, `URL:`, `HOST=`) fails on that fact alone, whatever the
  sentence around it says.
- **A URL being somewhere on the line.** `fleet-path` used to abandon the whole line the moment it
  saw `curl` or an `http` route, so "curl …, the config lives in `/docker/<real-name>`" shipped
  intact. Only the URL substring is now cut out. The one whole-line exemption left is a markdown
  table row whose first cell is an HTTP verb — an API route table, unambiguously.

`personal-id` is a **WARN across the whole repository** (and FAIL in strict scope), not a rule that
silently switches itself off outside strict scope, which is what the table below used to promise and
not deliver. Role mailboxes (`admin@`, `support@`, …) are still let through outside strict scope.

**Pass 2 — structure (`scripts/plugin_lint.py`).** Three rules, no baseline — these are fixed, not
excused. The first two `mutation-plan` triggers are self-declarations, so deleting `--yes` from an
`argument-hint` used to take a mutating command out of the contract entirely; the third trigger
reads the command's own code blocks for writes (apply flags, `curl -X POST`, container and service
restarts, `rm -rf`, `sed -i`, `git push`, `kubectl apply`, destructive SQL, `chmod`/`chown`) and one
apply flag — or two different kinds of write — is enough. Prose does not count, only code:

| Rule | What it requires | Severity |
|---|---|---|
| `mutation-plan` | a command taking `--yes`, or already speaking the dry-run vocabulary, **or whose body actually writes**, prints all eight blocks — `TARGET PRECHECK CHANGE BACKUP IMPACT VALIDATE ROLLBACK APPLY` — and its ROLLBACK is a **runnable command line**, not a sentence describing one | fail everywhere when the command declared the contract (`--yes` / the block names); warn · **fail** in strict scope when only its body gave it away |
| `skill-name` | one name across SKILL.md frontmatter, the skill directory, and `skill_name` in `evals/evals.json` | warn · **fail** in strict scope |
| `version-parity` | `plugins/<p>/.claude-plugin/plugin.json` version equals that plugin's entry in `.claude-plugin/marketplace.json` | warn · **fail** in strict scope |

**Strict scope.** A plugin that drops a `.scrub-strict` marker file in its root also gets: no host
that is not a vendor, upstream or example host; no absolute path that upstream does not document or
that lacks a placeholder; no hardcoded model id outside an `<!-- example-only -->` block; no bound
host port; no mailbox — and the two hygiene lint rules become hard failures. **Every new plugin
carries the marker**, and it is granted to an existing plugin as soon as that plugin passes
`--strict` cleanly on **both** passes. Marked today: `mem0`, `openclaw-ops`,
`postgresql-external-dev`, `stack-composable-stack-v1`. The rest are **debt, not policy** — run
`./scripts/scrub-check.sh --strict plugins/<name>` to see what one owes before its marker can land
(`codemap-dev` is one `skill-name` fix away; the large plugins are further).

**Fixing a finding**, in order of preference: a placeholder (`<instance>`, `<data-root>`,
`<compose-root>`, `example.com`, `203.0.113.10`) · runtime discovery · the operator's own config
file outside the repo. Only when none of those work, add a line to `scripts/scrub-allow.txt`
(`path:rule-id[#value-selector]:reason`, reason mandatory). Prefer the **narrowest** form: without a
selector the line exempts the whole file for that rule, which is how a credential-bearing URL once
hid behind a permit written for four harmless ones. `#sha256-<prefix>` pins the exception to one
value by the digest of the excerpt the gate prints, so the exception names no host or address and
the next real endpoint on the same surface still fails; `#<glob>` matches the excerpt directly. The
baseline may be **shrunk** in any pull request; a line may only be **added** — or narrowed, which
also counts as an added line — by a pull request that changes nothing else, and CI enforces it.

**What the gate does not cover: git history.** Both passes read the **working tree only**. A host,
address, identifier or credential that already reached a commit is invisible to them, and deleting
the line in a later commit does not remove it — the old blob stays fetchable by anyone who clones.
Such a leak is answered by **revoking the value at its source** (rotate the token, retire the
endpoint, move the host), never by editing a file. A green gate means "nothing new is leaving", not
"nothing has left".

## Patterns Worth Knowing

- **CONNECTORS pattern** (see `deep-research`): Uses `~~capability` placeholders instead of hard-coding tool names. Agents try providers in fallback order.
- **Tool name indirection**: Skills reference generic tool names. Agents discover actual MCP tool names at runtime.
- **Placeholder URLs**: `.mcp.json` uses placeholders (e.g. `https://your-instance.com/mcp`). Users replace with their own.
- The root `.mcp.json` is **committed** and aggregates every plugin's MCP entry, so it is the surface most likely to catch a pasted credential URL. It must carry only `${VAR}` references and published product endpoints; the publication gate holds it to that with a value-pinned exception (see **Publication Gate**). Real values belong in `.env` / `.claude/settings.local.json`, which are gitignored.

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

The repo ships an env-driven test harness. Real secrets live in **Infisical**, project **`claude-plugins`** (the workspace id is pinned in `.infisical.json`; the instance URL is deployment data — set `INFISICAL_DOMAIN` in the environment, the machine-identity file, or the gitignored `.env`, and the scripts pick it up in that order). Files involved:

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

### Authentication — machine identity

All three scripts authenticate with a **machine identity** by default, so they never
prompt and never depend on whoever happens to be logged into the CLI:

| File | Contents |
|------|----------|
| `/etc/infisical/<project>.env` | `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` + `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` (optionally `INFISICAL_DOMAIN`), mode 600 |

This follows the server-wide convention — one identity file per project under
`/etc/infisical/`, the same layout the OpenClaw deployments use. The identity needs
read access to project `claude-plugins`; grant write too if you intend to push.

`inf_ensure_login` exchanges those credentials for a short-lived token, exports it as
`INFISICAL_TOKEN`, and every call then passes `--token` explicitly. The credentials are
sourced into the environment rather than passed as flags, so the secret stays out of
`argv` and therefore out of `ps`; the secret is unset again once the token is in hand.

- point somewhere else for one run: `INFISICAL_IDENTITY_FILE=<path-to-identity>.env ./scripts/secrets-pull.sh`
- force the old interactive path: `INFISICAL_IDENTITY_FILE= ./scripts/secrets-pull.sh`
- the banner prints which mode is in use, so a silent fallback is always visible

When no identity file is readable the scripts fall back to the interactive user
session. That path needs the active-instance dance: the Infisical CLI keeps one
**active** instance and `infisical secrets` always reads it — `--domain` does not
switch it. The scripts detect this and run `infisical login --domain=…` when the active
instance is not ours. Override the instance for one run with `INFISICAL_DOMAIN=https://…`.

> When scripting `infisical login … --plain --silent`, capture **stdout only**. The CLI
> writes its update-check banner to stderr, so a `2>&1` concatenates that banner onto the
> JWT and every later call fails with a misleading "denied".

### OpenClaw plugins

`openclaw-ops` is the current plugin for operating a fleet of OpenClaw instances. It is a
Technology-level plugin: **no MCP server and no environment variables**. Every instance name,
path and port is discovered at run time from the live Docker state, and anything that cannot be
derived lives in an operator-owned config file outside this repo (`--strict` scrub scope, see
`scripts/scrub-check.sh`).

`openclaw-configurator` is **deprecated** and kept only for its workspace-authoring skills. Its
`OPENCLAW_INSTANCE_DIR` / `OPENCLAW_PROJECT_DIR` env vars were removed from `.env.example`:
they encoded one deployment's layout, which is exactly what a public plugin must not carry.

### Adding a new env var

1. Add the var name + a placeholder line to `.env.example`, in the section for its consumer.
2. Reference it as `${VAR_NAME}` in the plugin's `.mcp.json` / skills / commands.
3. Put the real value in `.env`, then `./scripts/secrets-push.sh --all-envs --yes` to send it
   to Infisical (or add it in the Infisical UI and skip to step 4).
4. `./scripts/secrets-pull.sh` so `.env` and the settings env block match, then restart Claude Code.
5. `./scripts/secrets-audit.sh` should report it as satisfied.
6. Never commit real values — `.env`, `.env.bak` and `.claude/settings.local.json` are gitignored.