# LEARNINGS — nocobase-dev

Accumulated fixes and discoveries for this plugin. New entries added by `plugin-creator:feedback` or `plugin-creator:wrap-up`.

Format:

```markdown
## [YYYY-MM-DD] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
```

## 2026-04-28 — nocobase-ui-builder: synced upstream commit `c34aaf9`

**Problem:** Bundled `nocobase-ui-builder` skill was frozen at the upstream snapshot we shipped in v1.0.0. Two new behaviours had landed upstream that block-authoring agents were missing: (a) tree-block "connect data block" became first-class via `settings.connectFields` / `changes.connectFields` (raw `filterManager` writes are now rejected); (b) numeric `settings.height` (and `changes.height`) is auto-paired with `heightMode: "specifyValue"` by both prepare-write and the localized preflight helper, including inside popup blocks. Plus an Ant Design icon allowlist (`ant-design-icon-names.js`) so the validator fails closed on icons the front-end doesn't ship, and a fix that stops misreading association `collectionName` metadata as a relation `target` (`o2o` and `mbm` interfaces now correctly require popups).

**Fix:** Synced all 17 files from `nocobase/skills@c34aaf9` verbatim — SKILL.md (Rule 11 + Rule 19 bodies), 6 reference docs, the `runtime/` JS module updates, the new `ant-design-icon-names.js`, the test suites, and `scripts/flow_payload_guard.{mjs,test.mjs}` (with three new blocker codes: `RAW_FILTER_MANAGER_NOT_PUBLIC`, `TREE_CONNECT_FLOWREGISTRY_NOT_PUBLIC`, `TREE_CONNECT_TARGET_DUPLICATE`). Diff stat matches upstream exactly: 17 files changed, +3766 / -155.

**Root cause:** Upstream skill content evolves on its own cadence; without a pull we drift behind on validator rules and silently produce payloads the runtime no longer accepts.

**Severity:** Major

## 2026-05-11 — plugin: promoted to nocobase-dev v2.0.0 with upstream auto-sync

**Problem:** Two parallel NocoBase dev plugins existed — the legacy hand-written `nocobase-dev` (v1.5.0, 22 custom skills) and `nocobase-2-dev` (v1.0.1) which already mirrored the official `nocobase/skills` library. The legacy plugin had drifted from upstream (e.g. it missed Rule 11 / Rule 19 from the 2026-04-28 ui-builder sync) and there was no automated mechanism to keep the upstream skills current, so any future upstream push would silently break agents using the plugin.

**Fix:** Deleted legacy `nocobase-dev/` tree. Renamed `nocobase-2-dev/` → `nocobase-dev/`, bumped to v2.0.0, refreshed bundled OpenAPI to v2.1.0-beta.29 (272 endpoints, +21 vs prior bundle). Added `scripts/sync-nocobase-skills.sh` (rsyncs only `skills/nocobase-*` directories — never touches hand-maintained custom skills) and `.github/workflows/sync-nocobase-skills.yml` (weekly cron + manual dispatch → auto-PR). Updated marketplace.json (rewrote `nocobase-dev` entry, removed `nocobase-2-dev`). README now documents the CLI-primary / REST-API-fallback rule, the env var contract (`NOCOBASE_URL`, `NOCOBASE_API_KEY`, `OAUTH_ACCESS_TOKEN`, `NB_CLI_ROOT`), and the auto-sync mechanism.

**Root cause:** Two issues compounded: (a) the original `nocobase-dev` was written before upstream shipped their own skill library, so it duplicated effort with worse fidelity; (b) once a mirror existed in `nocobase-2-dev`, there was no automation to keep it fresh — the only sync was the manual 2026-04-28 commit. Upstream pushes 2–3× per week.

**Severity:** Major
