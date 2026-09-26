---
description: Sync the current child project from its parent template — pull latest skills, commands, rules, and configs
argument-hint: ""
allowed-tools:
  [
    "Read",
    "Write",
    "Edit",
    "Grep",
    "Glob",
    "Bash",
    "Skill",
    "Agent",
  ]
---

# Sync from Parent Template

Pull improvements from a parent template into the current project.

## Instructions

1. Read the sync skill at `${CLAUDE_PLUGIN_ROOT}/skills/sync/SKILL.md`
2. Follow all steps: read stack.json → locate parent → compare files → present diff → user decision → apply → summary
3. Be careful NOT to overwrite project-specific files (stack.json, CLAUDE.md, .env.example, project-config)

## User request

$ARGUMENTS
