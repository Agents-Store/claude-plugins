# Learnings

## 2026-09-26 — plugin: renamed from `document-generator` to `document-generator-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `document-generator-ops` — business documents (proposals, invoices, contracts, NDAs) for business users. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `document-generator` at `document-generator-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `document-generator:` to `document-generator-ops:`. The glob every command uses to find its own scripts (`**/document-generator/scripts/...`) now names the new directory — the old pattern would match nothing after the move. The user-data directory `~/.document-generator/` keeps its name on purpose: renaming it would orphan every existing user's preferences and logos.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
