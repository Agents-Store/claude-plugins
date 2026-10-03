---
name: validate
description: >
  Use this skill when the user asks to "validate template", "check template
  structure", "is my template correct", "verify template conventions", "validate
  project template", "check template files", or needs to verify that a project
  template follows the Level 0/1/1.5/2 conventions and has all required files.
disable-model-invocation: true
---

# Validate Project Template

Comprehensive validation checklist for project templates. Run each check against the template directory and report pass/fail.

## Step 1: Determine Template Level

Read `stack.json` from the template root and classify:

```bash
cat stack.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Level: {d[\"level\"]}, Stack: {d.get(\"stack\",\"none\")}, Parent: {d.get(\"parent\",\"none\")}')"
```

| Level | Indicator |
|-------|-----------|
| 0 | `level: 0`, `parent: null`, `stack: null` |
| 1 | `level: 1`, `parent: "project-template"`, stack filled |
| 1.5 | `level: 1.5`, parent is a Level 1 template |
| 2 | `level: 2`, parent is a Level 1 template |

If `stack.json` is missing or invalid, flag as critical error and stop.

## Step 2: Validate stack.json

- [ ] Valid JSON (parseable)
- [ ] `stack` field present (`null` at L0, non-empty string at L1+)
- [ ] `version` present and in semver format (X.Y.Z)
- [ ] `level` is 0, 1, 1.5, or 2
- [ ] `parent` is `null` at L0, non-empty string at L1+
- [ ] `layers` object with `data`, `logic`, `interface` keys (all arrays)
- [ ] `layers` arrays empty at L0, at least one non-empty at L1+
- [ ] `plugins` object with `technology`, `process`, `stack` keys (all arrays)
- [ ] `plugins.technology` non-empty at L1+ (at least one tech plugin)

## Step 3: Check Required Files — All Levels

### Root Files
- [ ] `stack.json` exists
- [ ] `AGENTS.md` exists (shared rules for every coding tool)
- [ ] `CLAUDE.md` exists and starts with `@AGENTS.md` (or is a symlink to `AGENTS.md`)
- [ ] `README.md` exists
- [ ] `.env.example` exists
- [ ] `.mcp.json` exists and is tracked by git (empty `mcpServers` is fine at Level 0)
- [ ] `.gitignore` exists
- [ ] `.gitignore` excludes `.env`, `.env.local`, `.claude/settings.local.json`, `node_modules`
- [ ] `.gitignore` does NOT exclude `.mcp.json`

Legacy layout (WARN, not FAIL — recommend migrating): `.mcp.json.example` plus a gitignored `.mcp.json`; `AGENTS.md` generated from `CLAUDE.md` by `sync-context.sh`.

### `.claude/` Directory
- [ ] `.claude/settings.json` exists with `extraKnownMarketplaces` and `enabledPlugins` objects
- [ ] `.claude/settings.local.json.example` exists

### Core Skills (inherited from Level 0)
- [ ] `.claude/skills/brainstorming/SKILL.md` exists
- [ ] `.claude/skills/planning/SKILL.md` exists
- [ ] `.claude/skills/tdd/SKILL.md` exists
- [ ] `.claude/skills/debugging/SKILL.md` exists
- [ ] `.claude/skills/verification/SKILL.md` exists
- [ ] `.claude/skills/project-config/SKILL.md` exists

### Core Workflow Skills
- [ ] `.claude/skills/init-stack/SKILL.md` exists
- [ ] `.claude/skills/commit/SKILL.md` exists
- [ ] `.claude/skills/pr/SKILL.md` exists
- [ ] `.claude/skills/plan-feature/SKILL.md` exists
- [ ] `.claude/skills/code-review-project/SKILL.md` exists
- [ ] `.claude/skills/sync/SKILL.md` exists

Legacy layout (WARN — recommend migrating): the same workflows as `.claude/commands/<name>.md`. A command named `review` never runs (the built-in `/review` alias of `/code-review` takes the name) and `plan` collides with the built-in `/plan` — flag both and suggest `code-review-project` and `plan-feature`.

### Core Agent
- [ ] `.claude/agents/code-reviewer.md` exists

### Core Rules
- [ ] `.claude/rules/safety.md` exists
- [ ] `.claude/rules/search-before-building.md` exists
- [ ] `.claude/rules/project-conventions.md` exists

### Documentation
- [ ] `docs/architecture.md` exists
- [ ] `docs/code-style.md` exists
- [ ] `docs/api-conventions.md` exists

## Step 4: Check Level-Specific Requirements

### Level 1+ Additional Checks
- [ ] At least one stack-specific skill beyond the core set (e.g., `new-page`, `new-component`)
- [ ] `.claude/settings.json` `enabledPlugins` contains every plugin from `stack.json` `plugins` (technology, process, stack) as `<name>@<marketplace>`
- [ ] Every plugin named in `stack.json` exists in the marketplace; stack plugins are named `stack-{name}` (no process suffix)
- [ ] `.env.example` has stack-specific variables uncommented
- [ ] `CLAUDE.md` has filled Tech Stack section (no `[e.g.,` placeholders)
- [ ] `CLAUDE.md` has filled Installed Plugins section

### Level 1.5 Additional Checks
- [ ] Has application source code (`src/` or equivalent)
- [ ] Has sample data or seed scripts
- [ ] Has deployment config (Dockerfile, docker-compose.yml, or equivalent)

### Level 2 Additional Checks
- [ ] `project-config/SKILL.md` has actual resource IDs (no empty tables)
- [ ] `.env` or `.env.local` exists locally (warn if missing, but don't fail — it's gitignored)
- [ ] Every `${VAR}` referenced in `.mcp.json` has a value locally, in `.env` or the `env` block of `.claude/settings.local.json` (warn if missing — both are gitignored)

## Step 5: Check CLAUDE.md Quality

The sections below may live in `CLAUDE.md` or in the `AGENTS.md` it imports — check the combined content.

- [ ] Total line count under 100, counting the imported `AGENTS.md` (the 100-line limit is this template system's own rule; Anthropic's guidance is under 200 — WARN between 100 and 200, FAIL above 200)
- [ ] Has `## Tech Stack` section
- [ ] Has `## Architecture` section (pointing to `docs/architecture.md` by plain path)
- [ ] Has `## Installed Plugins` section
- [ ] Has `## Quick Commands` section
- [ ] Has `## Critical Rules` section
- [ ] No placeholder text remaining: grep for `\[e\.g\.,`, `\[Project Name\]`, `TODO`, `TBD`, `fill in`, `<!-- .*-->` with empty content around it
- [ ] At L1+: Tech Stack lists actual technologies (not `[e.g., NocoDB, Supabase, Directus]`)
- [ ] At L1+: Installed Plugins lists actual plugins with descriptions
- [ ] Long reference content is linked by plain path or lives in `.claude/rules/*.md` with `paths:`. An `@docs/...` import is not a way to shrink CLAUDE.md: imported files load at launch and count toward the line budget

## Step 6: Check Consistency

- [ ] Technologies in `stack.json` `layers` match CLAUDE.md Tech Stack section
- [ ] Plugins in `stack.json` `plugins` match CLAUDE.md Installed Plugins section
- [ ] Environment variables in `.env.example` cover every `${VAR}` that `.mcp.json` references
- [ ] Workflows listed in CLAUDE.md Quick Commands exist as `.claude/skills/*/SKILL.md` (legacy: `.claude/commands/*.md`)
- [ ] Skills referenced in CLAUDE.md exist as `.claude/skills/*/SKILL.md` directories
- [ ] `CLAUDE.md` imports `AGENTS.md` (or is a symlink to it); there is no second copy of the rules to keep in sync. If `AGENTS.md` is generated from `CLAUDE.md`, WARN and recommend the one-source layout
- [ ] `.claude/settings.json` `enabledPlugins` matches `stack.json` `plugins`

## Step 7: Check Security

- [ ] No `.env` file committed (check `git status` and `.gitignore`)
- [ ] The tracked `.mcp.json` holds only `${VAR}` references — no literal token, key or deployment host (see the check below)
- [ ] No hardcoded API keys or tokens in any tracked file: grep for patterns like `sk-`, `Bearer `, `token: "`, `key: "` with actual-looking values
- [ ] No real service URLs in `.env.example` (only placeholders)
- [ ] `.claude/settings.json` (committed) has no `env` values or tokens — only `enabledPlugins` and `extraKnownMarketplaces`
- [ ] `.claude/settings.local.json` is gitignored
- [ ] No `.env.local` committed

### Committed `.mcp.json` Holds Only References

`.mcp.json` is meant to be committed, so validate its content, not its presence. Both commands must print nothing:

```bash
# a credential-looking key whose value is not a ${VAR} reference
grep -niE '"[A-Za-z_-]*(token|key|secret|password|authorization)[A-Za-z_-]*"\s*:\s*"[^"]{8,}"' .mcp.json | grep -v '\${'
# "Bearer" followed by anything other than a ${VAR}
grep -nE 'Bearer +[^$ "]' .mcp.json
```

Also read every `url`, `command`, `args`, `headers` and `env` value: anything that differs per deployment (a host, port, path, account id) must be `${VAR}` or `${VAR:-default}`. A literal URL is acceptable only for a published product endpoint that is the same for every user. A literal secret is **CRITICAL** — rotate it at the source; editing the file does not remove it from git history.

### Git-Tracked Secrets (Critical)

The .gitignore check above only verifies RULES — it does not catch files that were committed BEFORE the gitignore rule was added. Run `git ls-files` to find actually tracked sensitive files:

```bash
# Check for tracked secrets that should be gitignored
git ls-files | grep -E '\.env\.local$|\.env$|settings\.local\.json$'
```

- [ ] `git ls-files` returns NO matches for `.env`, `.env.local`, or `settings.local.json` (`.mcp.json` is expected to be tracked)
- [ ] If matches found: flag as **CRITICAL** — these files contain real credentials and are being tracked by git. Fix: `git rm --cached <file>` and rotate all exposed tokens
- [ ] Check `.claude/settings.local.json.example` for real URLs or tokens (should contain only placeholders like `https://your-instance.example.com`)

## Output Format

Present validation results as:

```
## Template Validation Report: {template-name}

**Level:** {0 / 1 / 1.5 / 2}
**Stack:** {stack name or "universal base"}
**Parent:** {parent name or "none"}

### Results

| Category | Status | Details |
|----------|--------|---------|
| stack.json | PASS / FAIL | {details} |
| Required Files | PASS / FAIL | {missing files count} |
| Core Skills | PASS / FAIL | {missing skills} |
| Core Workflow Skills | PASS / WARN / FAIL | {missing skills, legacy commands} |
| Level-Specific | PASS / FAIL / N/A | {details} |
| CLAUDE.md Quality | PASS / WARN / FAIL | {details} |
| Consistency | PASS / FAIL | {mismatches} |
| Security | PASS / FAIL | {issues} |

### Issues Found
1. {issue description and how to fix}
2. ...

### Overall: VALID / {N} issues to fix
```
