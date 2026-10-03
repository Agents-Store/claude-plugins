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
