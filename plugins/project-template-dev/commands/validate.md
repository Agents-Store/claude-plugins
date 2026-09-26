---
description: Validate a project template against Level 0/1/1.5/2 conventions and required file structure
argument-hint: "Path to template directory (defaults to current directory)"
allowed-tools:
  [
    "Read",
    "Grep",
    "Glob",
    "Bash",
  ]
---

# Validate Project Template

Run comprehensive compliance checks against a project template directory.

## Instructions

1. Read the validate skill at `${CLAUDE_PLUGIN_ROOT}/skills/validate/SKILL.md`
2. Determine the template directory: use `$ARGUMENTS` if provided, otherwise use the current working directory
3. Execute all validation steps: determine level, check stack.json, verify required files, check CLAUDE.md quality, verify consistency, run security scan
4. Present the final validation report
5. If issues are found, provide specific fix instructions

## Template path

$ARGUMENTS
