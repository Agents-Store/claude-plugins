# Learnings

## 2026-09-26 — plugin: renamed from `multi-bank` to `multi-bank-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `multi-bank-ops` — balances, statements, payments and budgets for the account holder; the broadcast-pattern skills are secondary. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `multi-bank` at `multi-bank-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `multi-bank:` to `multi-bank-ops:`. The globs the agents and commands use to find `scripts/` now name the new directory. The data directory `~/.multi-bank/` keeps its name on purpose: renaming it would orphan existing encrypted data and the event log.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor
