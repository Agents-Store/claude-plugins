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

## 2026-10-03 — examples: `+meeting-prep` has no `--timezone`

**Problem:** `skills/examples/references/scenarios.md` (scenario 4) told readers to override the timezone with `gws workflow +meeting-prep --timezone America/New_York`; the flag does not exist and the command would be rejected.
**Fix:** The scenario now says `+meeting-prep` takes only `--calendar` and `--format`, that it uses the Google account's timezone, and points to `gws calendar +agenda --today --timezone America/New_York` for an explicit zone. Vendored skills untouched: a control run of `scripts/sync-google-workspace-skills.sh` produced an empty diff (still `a3768d0`, identical to upstream v0.22.5).
**Root cause:** The flag was guessed from `calendar +agenda` when the custom `examples` skill was written. Checked against the vendored `gws-workflow-meeting-prep` and `gws-calendar-agenda` skills and against `build_meeting_prep_cmd()` in upstream v0.22.5 (`helpers/workflows.rs`).
**Severity:** Minor

## 2026-06-22 — plugin created

Initial release. Vendored ~95 official skills (44 `gws-*`, 10 `persona-*`, 41 `recipe-*`) from
`googleworkspace/cli` @ `a3768d0` via `scripts/sync-google-workspace-skills.sh`, plus custom
`google-workspace-setup` and `examples` skills. Weekly upstream sync wired up at the repo root.
