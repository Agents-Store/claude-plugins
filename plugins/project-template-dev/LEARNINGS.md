# LEARNINGS -- project-template-dev

## 2026-09-26 — plugin: renamed from `project-template-creator` to `project-template-dev`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `project-template-dev` — template hierarchy management for developers. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `project-template-creator` at `project-template-dev`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `project-template-creator:` to `project-template-dev:`. Every `/project-template-creator:<cmd>` reference in README, skills and examples now reads `/project-template-dev:<cmd>`.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor

## 2026-09-27 — The author's GitHub organization was hard-coded

**Problem:** Every clone, remote and `gh pr create --repo` command named the plugin author's own GitHub organization, and the setup docs pointed `PROJECT_TEMPLATES_DIR` at the author's local folder. For anyone else the commands cloned from the wrong place.
**Fix:** The organization is now `$PROJECT_TEMPLATES_GITHUB_ORG` (documented next to `PROJECT_TEMPLATES_DIR`; if unset, ask the user). Reference docs and examples use the fictional `acme-templates`. Minor bump: a new environment variable.
**Root cause:** Written from inside one team's setup and published as is.
**Severity:** Minor
