# Learnings

## 2026-09-26 — CONNECTORS.md: reference to a renamed plugin

**Problem:** CONNECTORS.md pointed at the `deep-research` plugin for its fallback pattern; that plugin is now `deep-research-ops`.
**Fix:** Reference updated. Patch bump.
**Root cause:** Cross-plugin reference by name; the rename happened in another plugin.
**Severity:** Minor
