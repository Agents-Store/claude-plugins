# atlassian-ops — Learnings

Accumulated fixes and discoveries for the `atlassian-ops` plugin. Newest first.

<!-- Format:
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## 2026-10-03 — readme, api-reference, setup, troubleshoot: freshness pass against the live Atlassian docs

**Problem:** The README quick start sent a JQL made only of `order by created DESC` to `/search/jql`, which returns `400` (unbounded JQL). The workflows reference pointed at the search endpoint with the singular `workflow` path, scheduled for removal on 2026-06-01 (CHANGE-2569). Nothing covered scoped API tokens (gateway base URL, `cloudId`), token expiry, burst-only rate limits for API tokens, the `409` on direct page updates in approval spaces (CHANGE-3432), `bulkfetch` up to 1000 issues, or the official Rovo MCP server. The bundled specs were out of date (Jira 420 paths / Confluence 147 paths).
**Fix:** Bounded-JQL example and a "bounded JQL, `fields` defaults to `id`, no `total`, `reconcileIssues`" section in `search-jql.md`; `/workflows/search` plus `/workflows/copy`; a scoped-token section with `ATLASSIAN_CLOUD_ID` and a gateway-aware base-URL block in `setup` (reused by the operations skills and scenarios); a REST-vs-Rovo-MCP section (v2 URL only); 401/403/409/429 updates in `troubleshoot`; deprecation marks (`/pages/{id}/children`, `/fieldconfiguration*`, `…/context/defaultValue`, `GET /priority`, `GET /resolution`, `DELETE /version/{id}`, `GET /project`, `PUT /mypreferences/locale`); `bulkfetch`; the Confluence `space-permissions/transition/*` endpoints; both OpenAPI specs re-downloaded (Jira 423 paths / 620 operations / 100 tags, Confluence 151 paths / 218 operations / 30 tags).
**Root cause:** The plugin was written once against an earlier snapshot of the specs and docs; Atlassian removed or restricted several behaviours since. Live behaviour (the `400`, the gateway `401`/`403`, the approval-space `409`) was not re-checked from this environment — verify against a sandbox site.
**Severity:** Major
