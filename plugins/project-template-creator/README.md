# project-template-creator

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
/project-template-creator:feedback add VERCEL_TOKEN to .env.example

# End-of-session template review
/project-template-creator:wrap-up

# Create a new Level 1 stack template
/project-template-creator:create Level 1 template for Directus + Next.js

# Validate current template
/project-template-creator:validate
```

## Skills

| Skill | Description |
|-------|-------------|
| `feedback` | Push improvements from child project to parent template |
| `wrap-up` | End-of-session review of template improvements |
| `create` | Create new template from parent (Level 1, 1.5, or 2) |
| `validate` | Check template structure per level conventions |
| `template-reference` | Reference docs for template hierarchy and conventions |

## Commands

| Command | Description |
|---------|-------------|
| `/project-template-creator:feedback` | Report and fix a parent template issue |
| `/project-template-creator:wrap-up` | Session review for template improvements |
| `/project-template-creator:create` | Create new project template |
| `/project-template-creator:validate` | Validate template structure |

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
    "PROJECT_TEMPLATES_DIR": "/path/to/STACKMAKERS"
  }
}
```

This points to the directory containing all template repos (`project-template`, `project-directus-nextjs`, etc.).

### How Template Routing Works

When you give feedback, the plugin:
1. Reads `stack.json` in the current project to find the `parent` field
2. Looks for `$PROJECT_TEMPLATES_DIR/{parent}/`
3. If not found locally, offers to clone from `git@github.com:stackmakers-ai/{parent}.git`

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

## What Can Be Pushed to Parent Templates

- Skills (`.claude/skills/`)
- Commands (`.claude/commands/`)
- Agents (`.claude/agents/`)
- Rules (`.claude/rules/`)
- CLAUDE.md updates
- `.env.example` variables
- Documentation (`docs/`)
- Config files, scripts, dependencies
- `.mcp.json.example` updates
- Settings templates

## What Stays in the Client Project

- Resource IDs (table IDs, workflow IDs)
- Real credentials (`.env`, `.mcp.json`)
- Client-specific business logic
- Domain-specific skills
- Custom agents for client workflows

## Dependencies

This plugin complements the Agents Store ecosystem:
- Works alongside `plugin-creator` for plugin-level feedback
- Works alongside Technology plugins (e.g., `directus-dev`) for tool knowledge
- Works alongside Stack plugins (e.g., `stack-directus-nextjs-dev`) for integration patterns
- Templates reference plugins via `stack.json` → `plugins` arrays

## Installation

```bash
claude plugin add /path/to/project-template-creator
```
