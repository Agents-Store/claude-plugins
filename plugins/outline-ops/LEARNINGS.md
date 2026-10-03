# outline-ops — Learnings

Accumulated fixes and discoveries for the `outline-ops` plugin. Newest first.

<!-- Format:
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## 2026-10-03 — api-reference: bundled spec was 42 operations behind upstream

**Problem:** the bundled OpenAPI snapshot had 112 operations; upstream `outline/openapi` `spec3.yml` had 154 (webhookSubscriptions, apiKeys, pins, subscriptions, notifications, reactions, collections.archive/restore/move/duplicate/import, attachments.createFromUrl/list, revisions.update/delete/export, groups.update_user, userMemberships, groupMemberships, users.resendInvite/updateEmail, auth.delete; `views.create` was removed). The curated `references/*.md` also said `comments.update` needs `data` (it takes `data` or `text`), and the README claimed "no MCP" although every workspace has had a built-in MCP server since 2026-02-18.
**Fix:** re-downloaded `spec3.yml` (commit `40f51b75ef`, 2026-09-23; Outline server v1.10.1), added a row for every new operation, documented `filters`, `lastRevision` (409), `preferences`, `reason`, `publish` on templates, `okf`/TextBundle export, and added a built-in MCP section to the README.
**Root cause:** the spec snapshot was taken once and never refreshed. Refresh with `curl -o skills/api-reference/references/outline-openapi.yml https://raw.githubusercontent.com/outline/openapi/main/spec3.yml`, then check that every `paths` key appears in some `references/*.md`.
**Severity:** Major
