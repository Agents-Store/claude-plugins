# Learnings

## 2026-09-26 — plugin: renamed from `deep-research` to `deep-research-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `deep-research-ops` — research runs and reports for the person asking — no API or SDK teaching, so ops rather than dev. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `deep-research` at `deep-research-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `deep-research:` to `deep-research-ops:`. The MCP server keeps its name `deep-research`, and so does the `deep-research` skill — only the plugin was renamed.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
