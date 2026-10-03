# project-template-dev

Manage the 4-level project template hierarchy. Send feedback from child projects to parent templates, create new stack templates, and validate template conventions.

## Template Hierarchy

| Level | Pattern | Parent | Example |
|-------|---------|--------|---------|
| 0 | `project-template` | none | Universal base |
| 1 | `project-{stack}` | `project-template` | `project-directus-nextjs` |
| 1.5 | `demo-{stack}` | `project-{stack}` | `demo-directus-nextjs` |
| 2 | `{client}-{project}` | `project-{stack}` | `acme-website` |

Each level inherits from its parent. Templates own project-level knowledge (how THIS project works); plugins own tool-level knowledge (how to USE a specific tool).

## Quick Start

While working in any child project:

```bash
# Send feedback to parent template
/project-template-dev:feedback add VERCEL_TOKEN to .env.example

# End-of-session template review
/project-template-dev:wrap-up

# Create a new Level 1 stack template
/project-template-dev:create Level 1 template for Directus + Next.js

# Validate current template
/project-template-dev:validate
```

## Skills

| Skill | Description |
|-------|-------------|
| `feedback` | Push improvements from child project to parent template |
| `wrap-up` | End-of-session review of template and plugin improvements |
| `capture` | Quick-capture an improvement idea into the backlog for wrap-up |
| `improve` | Route an improvement to the right plugin or parent template |
| `sync` | Pull parent-template changes down into the current project |
| `create` | Create new template from parent (Level 1, 1.5, or 2) |
| `validate` | Check template structure per level conventions |
| `audit-stack` | Scan a codebase, classify its technologies into layers, recommend a template and `stack.json` |
| `template-reference` | Reference docs for template hierarchy and conventions |
| `examples` | End-to-end scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/project-template-dev:feedback` | Report and fix a parent template issue |
| `/project-template-dev:wrap-up` | Session review for template improvements |
| `/project-template-dev:capture` | Jot down an improvement for the wrap-up |
| `/project-template-dev:improve` | Auto-route an improvement to a plugin or a template |
| `/project-template-dev:sync` | Sync the project from its parent template |
| `/project-template-dev:create` | Create new project template |
| `/project-template-dev:validate` | Validate template structure |
| `/project-template-dev:audit-stack` | Audit a project's stack and recommend a template |

## Agent

| Agent | Purpose |
|-------|---------|
| `template-architect` | Helps decide Level 0 vs Level 1 routing, plans template structure |

## Setup

### Environment Variable

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "PROJECT_TEMPLATES_DIR": "/path/to/project-templates",
    "PROJECT_TEMPLATES_GITHUB_ORG": "your-github-org"
  }
}
```

`PROJECT_TEMPLATES_DIR` points to the directory containing all template repos (`project-template`, `project-directus-nextjs`, etc.);
`PROJECT_TEMPLATES_GITHUB_ORG` is the GitHub organization that hosts them. If it is unset, the plugin asks for it.

### How Template Routing Works

When you give feedback, the plugin:
1. Reads `stack.json` in the current project to find the `parent` field
2. Looks for `$PROJECT_TEMPLATES_DIR/{parent}/`
3. If not found locally, offers to clone from `git@github.com:$PROJECT_TEMPLATES_GITHUB_ORG/{parent}.git`

### Optional: Plugin Search

For the `create` workflow to find matching Agents Store plugins, also set:

```json
{
  "env": {
    "PLUGINS_PUBLIC_SOURCE_DIR": "/path/to/claude-public-plugins/plugins",
    "PLUGINS_PRIVATE_SOURCE_DIR": "/path/to/claude-plugins-private/plugins"
  }
}
```

## Template Conventions

What `create` generates and `validate` checks:

- **One rules file.** `AGENTS.md` holds the rules every coding tool reads; `CLAUDE.md` starts with `@AGENTS.md` and adds Claude-specific lines. Nothing is generated from `CLAUDE.md`; `scripts/sync-context.sh` only mirrors the rules into `.cursor/`.
- **`.mcp.json` is committed** and holds `${VAR}` references only. The values live in `.env` and `.claude/settings.local.json`, both gitignored.
- **`.claude/settings.json` is committed** with `enabledPlugins` and `extraKnownMarketplaces`, so the plugins listed in `stack.json` are offered to everyone who clones the template.
- **Workflows are skills** (`.claude/skills/<name>/SKILL.md`), not `.claude/commands/` files. Base workflows are named `plan-feature` and `code-review-project`, because the built-in `/plan` and `/review` shadow plain `plan` and `review`.
- **CLAUDE.md stays short.** The template rule is under 100 lines (Anthropic's guidance is under 200). An `@docs/...` import does not save context, because imported files load at launch; link long documents by plain path or move file-specific rules into `.claude/rules/*.md` with `paths:`.
- **Stack plugins are named `stack-{name}`** (no process suffix), technology plugins `{tool}-{process}`.

## What Can Be Pushed to Parent Templates

- Skills (`.claude/skills/`), including the workflow skills (`commit`, `pr`, `plan-feature`, ...); the older `.claude/commands/<name>.md` form still works
- Agents (`.claude/agents/`)
- Rules (`.claude/rules/`)
- CLAUDE.md updates
- `.env.example` variables
- Documentation (`docs/`)
- Config files, scripts, dependencies
- `.mcp.json` entries (`${VAR}` references only)
- `.claude/settings.json` (`enabledPlugins`, `extraKnownMarketplaces`)
- Settings templates

## What Stays in the Client Project

- Resource IDs (table IDs, workflow IDs)
- Real credentials and endpoints (`.env`, `.claude/settings.local.json`) — `.mcp.json` is committed, but only with `${VAR}` references
- Client-specific business logic
- Domain-specific skills
- Custom agents for client workflows

## Dependencies

This plugin complements the Agents Store ecosystem:
- Optional: the private `plugin-creator` plugin (not in the public marketplace) receives plugin-level feedback from `improve` and `wrap-up`; without it they fall back to editing the plugin source, a GitHub issue or `LEARNINGS.md`
- Works alongside Technology plugins (e.g., `directus-dev`) for tool knowledge
- Works alongside Stack plugins (e.g., `stack-directus-nextjs`) for integration patterns
- Templates reference plugins via `stack.json` → `plugins` arrays

## Installation

Add the Agents Store marketplace once, then install the plugin from it:

```bash
claude plugin marketplace add Agents-Store/claude-plugins
claude plugin install project-template-dev@agents-store-claude-plugins
```

Inside a Claude Code session the same install is `/plugin install project-template-dev@agents-store-claude-plugins`. To try a local checkout for one session without installing it, start Claude Code with `claude --plugin-dir /path/to/project-template-dev`.

The plugin name is `project-template-dev` (formerly `project-template-creator`); the marketplace `renames` map moves installed copies to the new name.
