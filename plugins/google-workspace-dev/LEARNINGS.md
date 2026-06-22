# LEARNINGS — google-workspace-dev

Accumulated fixes and discoveries for this plugin. Newest first.

Format:

```
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

> **Note on vendored skills:** `gws-*`, `persona-*`, and `recipe-*` skills are a mirror of
> [`googleworkspace/cli`](https://github.com/googleworkspace/cli) and are overwritten by the weekly
> sync. Do **not** hand-edit them — fixes will be silently dropped. File issues upstream, or fix the
> behavior in a custom skill (`google-workspace-setup`, `examples`). Only custom skills and the sync
> tooling are safe to edit here.

---

## 2026-06-22 — plugin created

Initial release. Vendored ~95 official skills (44 `gws-*`, 10 `persona-*`, 41 `recipe-*`) from
`googleworkspace/cli` @ `a3768d0` via `scripts/sync-google-workspace-skills.sh`, plus custom
`google-workspace-setup` and `examples` skills. Weekly upstream sync wired up at the repo root.
