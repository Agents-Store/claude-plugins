---
description: End-of-session review — find plugin and template improvements, process captured backlog, push fixes to sources
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

# Unified Session Wrap-Up

Review the current session for discoveries that should be pushed to parent templates or plugins. Also process any items captured via `/capture`.

## Instructions

1. Read the wrap-up skill at `${CLAUDE_PLUGIN_ROOT}/skills/wrap-up/SKILL.md`
2. Follow all phases: backlog → review → categorize → user decision → apply or record → summary
3. For template fixes, delegate to `${CLAUDE_PLUGIN_ROOT}/skills/feedback/SKILL.md`
4. For plugin fixes, invoke `/plugin-creator:feedback` via the Skill tool

## User request

$ARGUMENTS
