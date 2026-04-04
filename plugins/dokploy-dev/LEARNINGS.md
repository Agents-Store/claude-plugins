# LEARNINGS.md — dokploy-dev

## 2026-04-04 — all skills: Prompting quality improvements

**Problem:** Skill descriptions used "Use when..." format instead of required third-person "This skill should be used when...". Agent examples lacked commentary. `examples/references/scenarios/` was 2 levels deep (max 1). api-reference SKILL.md was 104 lines (must be under 100). Reference files over 100 lines lacked table of contents.
**Fix:** Updated all 6 skill descriptions to third-person format. Added commentary to 3 agent examples. Flattened scenarios/ dir up one level. Trimmed api-reference from 104 to 62 lines. Added TOC to all 8 reference files over 100 lines.
**Root cause:** Initial generation didn't follow all Agents Store prompting quality conventions from the validation checklist.
**Severity:** Minor

## 2026-04-04 — commands: Add slash commands for standard operations

**Problem:** Plugin had no slash commands — users had to describe operations in natural language or remember MCP tool names.
**Fix:** Added 8 commands: list-projects, create-project, list-apps, create-app, deploy, status, create-db, add-domain. Each with argument parsing, project/app name resolution, and usage examples.
**Root cause:** Initial plugin creation focused on skills and agent, skipped commands component.
**Severity:** Major
