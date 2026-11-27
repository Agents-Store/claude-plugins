# outline-ops — Learnings

Accumulated fixes and discoveries for the `outline-ops` plugin. Newest first.

<!-- Format:
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## 2026-11-27 — refresh: aligned with Outline v1.13.0, session-only routes and security notes

**Problem:** the plugin told users to mint and revoke API keys with `apiKeys.create`/`apiKeys.delete` and to change email with `users.updateEmail`, but all three accept only a signed-in browser session and answer `403` to an API key (email change since v1.11.0, GHSA-97vv-f6qq-6842; upstream dropped `users.updateEmail` from the spec). The settings page is named **API & Access**, not "API & Apps". `views.list` became paginated (default 100, v1.13.0), `documents.viewed` sorts only by `updatedAt`/`createdAt`, and `text` on `comments.update` arrived in v1.11.0. Servers before v1.12.0 kept serving unpublished documents through their share links (GHSA-rq53-m97j-f2pg).
**Fix:** re-downloaded `spec3.yml` (commit `fbc3545a1c`, 153 operations), removed `users.updateEmail`, marked the key routes as browser-only and pointed key management to the UI, corrected the settings label, documented the new `views.list` paging and `documents.viewed` sort values, added the unpublish/revoke caveat and a "run v1.12.0+" note to setup.
**Source:** https://github.com/outline/outline/releases (v1.11.0, v1.12.0, v1.13.0), https://github.com/outline/outline/security/advisories/GHSA-97vv-f6qq-6842, https://github.com/outline/outline/security/advisories/GHSA-rq53-m97j-f2pg, https://github.com/outline/openapi/commits/main
**Severity:** Major

## 2026-10-03 — api-reference: accuracy follow-ups after review

**Problem:** (1) the `collections.md` archive/restore/move/duplicate/import section carried a release-history sentence ("added to the API after the first plugin release") that belongs in history, not in the reference. (2) `auth.delete` was described as invalidating all API keys; the spec only says "all existing API tokens and sessions", and personal `ol_api_` keys are separate records, so it most likely does not revoke one. (3) The built-in MCP section omitted availability: v1.6.0 introduced it, disabled by default for existing workspaces; API-key header auth came in v1.6.1. (4) `users.update_role` listed three roles; `UserRole` also has `guest`.
**Fix:** moved the history here, softened the `auth.delete` wording, added the MCP availability line and hedged the tool list with "e.g.", added `guest` to the role enum, worded the `views.create` note as "may be rejected".
**Root cause:** wording went beyond what the spec and the release notes actually state.
**Severity:** Minor

## 2026-10-03 — api-reference: bundled spec was 42 operations behind upstream

**Problem:** the bundled OpenAPI snapshot had 112 operations; upstream `outline/openapi` `spec3.yml` had 154 (webhookSubscriptions, apiKeys, pins, subscriptions, notifications, reactions, collections.archive/restore/move/duplicate/import, attachments.createFromUrl/list, revisions.update/delete/export, groups.update_user, userMemberships, groupMemberships, users.resendInvite/updateEmail, auth.delete; `views.create` was removed). The curated `references/*.md` also said `comments.update` needs `data` (it takes `data` or `text`), and the README claimed "no MCP" although Outline had announced a built-in MCP server on 2026-02-18 (in releases since v1.6.0).
**Fix:** re-downloaded `spec3.yml` (commit `40f51b75ef`, 2026-09-23; Outline server v1.10.1), added a row for every new operation, documented `filters`, `lastRevision` (409), `preferences`, `reason`, `publish` on templates, `okf`/TextBundle export, and added a built-in MCP section to the README.
**Root cause:** the spec snapshot was taken once and never refreshed. Refresh with `curl -o skills/api-reference/references/outline-openapi.yml https://raw.githubusercontent.com/outline/openapi/main/spec3.yml`, then check that every `paths` key appears in some `references/*.md`.
**Severity:** Major
