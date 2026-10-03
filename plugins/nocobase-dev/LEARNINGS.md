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

> **Superseded in part (2026-10-03):** the env-var contract named in the **Fix** below (`NOCOBASE_URL`, `NOCOBASE_API_KEY`, `OAUTH_ACCESS_TOKEN`, `NB_CLI_ROOT`) was never the contract the files used. The real one is `NB_URL` + `NB_USER` + `NB_PASSWORD` (or `NB_TOKEN`), and since 2.1.0 the CLI-native path is `nb env add` / `nb env auth`. See the 2026-10-03 entry. The rest of this entry stands.

**Problem:** Two parallel NocoBase dev plugins existed — the legacy hand-written `nocobase-dev` (v1.5.0, 22 custom skills) and `nocobase-2-dev` (v1.0.1) which already mirrored the official `nocobase/skills` library. The legacy plugin had drifted from upstream (e.g. it missed Rule 11 / Rule 19 from the 2026-04-28 ui-builder sync) and there was no automated mechanism to keep the upstream skills current, so any future upstream push would silently break agents using the plugin.

**Fix:** Deleted legacy `nocobase-dev/` tree. Renamed `nocobase-2-dev/` → `nocobase-dev/`, bumped to v2.0.0, refreshed bundled OpenAPI to v2.1.0-beta.29 (272 endpoints, +21 vs prior bundle). Added `scripts/sync-nocobase-skills.sh` (rsyncs only `skills/nocobase-*` directories — never touches hand-maintained custom skills) and `.github/workflows/sync-nocobase-skills.yml` (weekly cron + manual dispatch → auto-PR). Updated marketplace.json (rewrote `nocobase-dev` entry, removed `nocobase-2-dev`). README now documents the CLI-primary / REST-API-fallback rule, the env var contract (`NOCOBASE_URL`, `NOCOBASE_API_KEY`, `OAUTH_ACCESS_TOKEN`, `NB_CLI_ROOT`), and the auto-sync mechanism.

**Root cause:** Two issues compounded: (a) the original `nocobase-dev` was written before upstream shipped their own skill library, so it duplicated effort with worse fidelity; (b) once a mirror existed in `nocobase-2-dev`, there was no automation to keep it fresh — the only sync was the manual 2026-04-28 commit. Upstream pushes 2–3× per week.

**Severity:** Major

## 2026-10-03 — cli-recipes, auth, overview, examples: synced upstream (12 → 20 skills) and rewrote the custom layer for `nb` 2.2

**Problem:** The weekly sync PR (#5, `sync upstream skills @ 686de87`) sat unmerged from 2026-06-08, so the vendored skills stayed at upstream `v2.0.4` while upstream reached `v2.0.58` (8 new skills: `ai-builder`, `ai-knowledge-base-manager`, `ai-manager`, `file-manager`, `notification-manage`, `portal-manage`, `prototype-repro`, `revision`). Meanwhile the hand-written custom files had drifted from the real `nb` CLI: they taught `nb start|stop|restart|upgrade` and `nb status`, `nb pm add|remove`, `nb backup ./x`, `nb restore`, `nb migration export|import`, `nb api collections|workflows trigger|app:clearCache`, `workflows:trigger` with a workflow key, `@nocobase/cli@beta`, Node.js 18, `@nocobase/plugin-oidc-client`, and `nc-mcp`. Several of those commands never existed in `nb` 2.x. The router still listed 11 skills and the counters said "11 upstream".

**Fix:** Ran `./scripts/sync-nocobase-skills.sh` locally against upstream `main` (`686de87` = `v2.0.58`; +113 files, 96 changed, none removed; 20 `nocobase-*` skills) and committed the result untouched. Rewrote `cli-recipes`, `auth`, `overview`, `examples` and `README.md` to the canonical forms confirmed against `@nocobase/cli` 2.2.20 (npm tarball plus `--help` of each command): `nb app start|stop|restart|upgrade|logs`, `nb env add|auth|use|list|info|status|update`, `nb plugin list|enable|disable|import` (the flat forms and `nb pm` are hidden aliases; `pm` has no add/remove), `nb backup create|restore --file --force`, generated `nb api <group>` commands (`data-modeling`, `workflow`, `flow-surfaces`, `acl`, `ai`, `kb`, `backup`, `migration`) with `--filter-by-tk`, `--body`/`--body-file`, `-j`, `-e`. Manual workflow run is `POST /api/workflows:execute?filterByTk=<integer id>` with the trigger context as the whole body (no `values` envelope; `:trigger` is only for custom-action triggers); the polling example now uses the real execution status enum (`null`/`0` running, `1` resolved, negative values failed/aborted). Channel decision (D4): stable `@nocobase/cli` (`latest`); `@alpha` only as a note for `nb portal`, which stable (2.2.20) and beta (2.3.0-beta.13) do not contain. Node.js >= 22 and NocoBase >= 2.1.0 for agent connection. `auth` now separates **IdP: OAuth** (`@nocobase/plugin-idp-oauth`, NocoBase as identity provider for the CLI device flow and MCP clients) from **Auth: OIDC** (commercial SSO sign-in plugin). `overview` routes all 20 upstream skills with `nocobase-portal-manage` as the only UI entry, and points at the built-in MCP endpoint (`/api/mcp`, `@nocobase/plugin-mcp-server`) instead of `nc-mcp`. `api-reference/tags-overview.md` gained the backup/migration tags the snapshot already contained.

**Root cause:** (a) a bot PR with no required reviewer and no check on it is easy to leave open for months; (b) the custom recipes were written from memory of the 1.x CLI and docs of a different channel, and nothing compared them with the shipped command tree; (c) the sync script overwrites whole skill directories, so any local edit to a vendored file is silently undone on the next run.

**Severity:** Major

**Open items (owner):**
- **OpenAPI snapshot not refreshed.** `references/openapi/nocobase.json` is still the 2.1.0-beta.29 snapshot (272 operations). The swagger document is assembled at runtime by the API documentation plugin from whichever plugins are enabled on a live app, so it cannot be rebuilt reproducibly from npm tarballs. Refresh from a >= 2.2.x stand (`swagger:getUrls`), then recount the counters in `README.md`, `plugin.json`, `skills/api-reference/SKILL.md` and `references/tags-overview.md`.
- **Scrub baseline for upstream text.** Upstream `nocobase-publish-manage/references/{test-playbook,v1-runtime-contract}.md` contain an author's home path (`/Users/<name>`) in sample download paths. An earlier local commit had replaced it with a placeholder, and the sync put it back. Handled with two value-pinned lines in `scripts/scrub-allow.txt` (own commit, `scripts/scrub-allow.txt` only). The proper fix is upstream.
- **Upstream issue pending (not filed).** Proposed for `nocobase/skills`: vendored skills carry non-spec frontmatter keys at top level (`owner`, `last-reviewed`, `risk-level`, `version`); ask to move them under `metadata:`, and to replace the sample home path in the two publish-manage references with a placeholder. Also worth reporting: `nocobase-workflow-manage/references/http-api/workflows.md` shows the `workflows:execute` body wrapped in `values`, while its own CLI reference and the server spec treat the whole body as the trigger context. Link to be recorded here once filed.
- **`nocobase/nocobase` schema defect.** Eleven `flow_surfaces_*` MCP tools (`add_block(s)`, `add_field(s)`, `add_action(s)`, `add_record_action(s)`, `apply_blueprint`, `apply_approval_blueprint`, `compose`) are rejected by some MCP clients because `defaultFilter.allOf[0].type` is declared as `object,boolean`; an issue against `nocobase/nocobase` is pending.
