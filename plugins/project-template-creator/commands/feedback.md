---
description: Report an issue in the current project that should be fixed in a parent template (Level 0 or Level 1)
argument-hint: "Description of what to fix (e.g., 'add VERCEL_TOKEN to .env.example', 'create a new-api-route skill')"
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

# Template Feedback

Report and fix an issue in a parent project template.

## Instructions

1. Read the feedback skill at `${CLAUDE_PLUGIN_ROOT}/skills/feedback/SKILL.md`
2. Follow all steps: identify improvement → read stack.json → locate parent → apply fix → record in LEARNINGS.md → commit
3. If the parent template cannot be found locally, offer to clone from GitHub (stackmakers-ai org)
4. For ambiguous Level 0 vs Level 1 routing, use the `template-architect` agent

## User request

$ARGUMENTS
