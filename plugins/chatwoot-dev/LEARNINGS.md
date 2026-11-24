# chatwoot-dev — Learnings

Accumulated fixes and discoveries for this plugin. Format:

## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor

## 2026-10-03 — setup, troubleshoot, api-reference: send `api-access-token`, not `api_access_token`

**Problem:** Every example sent the underscore header `api_access_token` and the docs said it was the only valid spelling. Behind nginx (default `underscores_in_headers off`) or Caddy 2.6.4+ the header is dropped before it reaches Chatwoot, so a valid token gets `401`.
**Fix:** All examples now send the hyphenated `api-access-token`; `pagination-errors.md` explains the proxy behaviour and a two-spelling diagnostic is in `troubleshoot`. The official CLI made the same change in v0.7.0 (chatwoot/cli#41).
**Root cause:** Rack turns both spellings into `HTTP_API_ACCESS_TOKEN`, which is the only thing Chatwoot reads (`access_token_auth_helper.rb`), so the underscore form has no advantage and a real proxy failure mode. "Never Bearer" was also dropped: Chatwoot v4.19.0 (not yet released on 2026-10-03) accepts `Authorization: Bearer`.
**Severity:** Major

## 2026-11-24 — refresh: Bearer and three `develop`-only endpoints are in releases now (aligned to v4.20.1)

**Problem:** The text still said v4.18.0 was the latest release, that `Authorization: Bearer` was something to avoid "until v4.19.0", and that two Application and one Platform operation exist only on `develop`. It also listed the portal routes with `{id}`.
**Fix:** Bearer is described as accepted by v4.19.0+ (`401` on older instances); `GET /portals/{portal_slug}`, `update_last_seen` and Platform `POST /users/{id}/token` are marked v4.19.0; the release counts are 125 / 18 / 12 / 1 (v4.20.1); the portal parameter is `{portal_slug}` with a note that it is the slug, not the numeric id; the webhook event allow-list is re-checked against v4.20.1. Source: release notes v4.19.0, v4.20.0, v4.20.1 and the swagger and `access_token_auth_helper.rb` at those tags (github.com/chatwoot/chatwoot).
**Root cause:** The plugin was written one release before v4.19.0 shipped; the portal route was always looked up by slug, only the spec's parameter name was wrong (corrected in v4.20.0). Webhook signing, the allow-list and CLI v0.7.0 are unchanged.
**Severity:** Minor

**Follow-up (same refresh):** the `troubleshoot` description now also names `502` and a self-hosted instance, matching the body table that already covered `404`/`502` behind a proxy; the Russian "HTML instead of JSON, sometimes 502" trigger case missed in two quick L2 runs, and on the unmodified plugin it missed in one of two.
