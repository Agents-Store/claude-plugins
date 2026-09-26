---
description: Create a new project template at Level 1, 1.5, or 2 by cloning and customizing a parent template
argument-hint: "Template description (e.g., 'Level 1 template for Directus + Next.js', 'demo for Supabase + Nuxt')"
allowed-tools:
  [
    "Read",
    "Write",
    "Edit",
    "Grep",
    "Glob",
    "Bash",
    "AskUserQuestion",
    "Skill",
    "Agent",
  ]
---

# Create Project Template

Create a new project template by cloning and customizing a parent template.

## Instructions

1. Read the create skill at `${CLAUDE_PLUGIN_ROOT}/skills/create/SKILL.md`
2. Follow all steps: gather info → generate name → clone parent → customize stack.json → customize CLAUDE.md → customize files → find plugins → validate → commit
3. Use references from `${CLAUDE_PLUGIN_ROOT}/skills/create/references/` for stack.json schema and level checklists
4. For design decisions, use the `template-architect` agent
5. Run validation at the end using `${CLAUDE_PLUGIN_ROOT}/skills/validate/SKILL.md`

## User request

$ARGUMENTS
