# atlassian-ops

Jira + Confluence Cloud **ops** plugin for Agents Store. Drive the full **Jira Cloud REST API v3** and **Confluence Cloud REST API v2** by `curl`, with both official OpenAPI specs bundled as the source of truth (snapshot 2026-10-03). One Atlassian API token authenticates both products — a classic (unscoped) token on your site URL, or a scoped token through the `api.atlassian.com` gateway.

## What it covers

**Jira (REST v3, `/rest/api/3`)**
- Issues — create, edit, assign, transition, delete (ADF bodies), bulk create/edit/fetch (`bulkfetch` up to 1000 issues), archive
- Search — bounded JQL (`/search/jql`, token pagination, `reconcileIssues`), approximate counts, JQL tooling
- Comments, worklogs (time tracking), and issue properties
- Attachments (multipart), issue links, remote links
- Projects, versions (releases), components, roles, categories, features, templates
- Fields, custom field contexts & options, field configurations, screens & screen schemes
- Workflows (search via `/workflows/search`, copy), workflow schemes (+ drafts), statuses, issue types & schemes
- Users & groups (`accountId`), permissions & schemes, security, notifications, priorities, resolutions
- Dashboards, gadgets, filters & sharing; Advanced Roadmaps plans & teams

**Confluence (REST v2, `/wiki/api/v2`)**
- Pages & blog posts — create/update (versioned, storage or ADF bodies), hierarchy, custom content, whiteboards, databases, folders, smart links
- Spaces, space properties, permissions (+ bulk permission-to-role transition), roles
- Footer & inline comments, attachments, versions, likes, tasks, operations
- Labels, content properties, classification levels, data policies, redactions

## Skills

| Skill | Use it to |
|-------|-----------|
| `setup` | Authenticate (Basic auth: email + API token, classic or scoped), choose REST vs the Rovo MCP server, and learn the conventions both APIs share |
| `jira-operations` | Plain-language playbooks for everyday Jira work |
| `confluence-operations` | Plain-language playbooks for everyday Confluence work |
| `api-reference` | The full per-domain endpoint catalog + the bundled OpenAPI specs (reference-only) |
| `examples` | Worked end-to-end scenarios chaining real API calls |
| `troubleshoot` | Map 400/401/403/404/409/429 and the common pitfalls to fixes |

There is one agent, `atlassian-assistant`, that drives all of the above.

## Prerequisites

- An Atlassian Cloud site (`https://your-domain.atlassian.net`)
- An API token: https://id.atlassian.com/manage-profile/security/api-tokens — expires after 1–365 days (1 year by default), so rotate it before it lapses
- `curl` and `jq` available in the shell

## Quick start

```bash
export ATLASSIAN_SITE_URL="https://your-domain.atlassian.net"
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="…"   # from id.atlassian.com

# Verify Jira + Confluence in two calls
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "$ATLASSIAN_SITE_URL/rest/api/3/myself" | jq '{accountId, displayName}'
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "$ATLASSIAN_SITE_URL/wiki/api/v2/spaces?limit=1" | jq '.results[0] | {id, key, name}'
```

## Authentication

```bash
# HTTP Basic auth: email + API token. Jira at /rest/api/3, Confluence at /wiki/api/v2.
# JQL on /search/jql must be BOUNDED (a restriction before ORDER BY) — a bare ORDER BY returns 400.
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "$ATLASSIAN_SITE_URL/rest/api/3/search/jql" -H "Content-Type: application/json" \
  -X POST -d '{"jql":"created >= -30d ORDER BY created DESC","maxResults":3,"fields":["summary","status"]}'
```

Set `ATLASSIAN_SITE_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN` in your shell or repo `.env`. Never commit the token.

### Scoped API token (gateway base URL)

A token created with **Create API token with scopes** works only through the Atlassian API gateway, **not** on `https://your-domain.atlassian.net` — use your site's `cloudId` in the base URL. Without it a scoped token gets `401`/`403` on the site URL.

```bash
# cloudId of the site (public tenant-info document)
export ATLASSIAN_CLOUD_ID="$(curl -s "${ATLASSIAN_SITE_URL%/}/_edge/tenant_info" | jq -r .cloudId)"

# Jira   -> https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/...
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "https://api.atlassian.com/ex/jira/$ATLASSIAN_CLOUD_ID/rest/api/3/myself" | jq '{accountId, displayName}'
# Confluence -> https://api.atlassian.com/ex/confluence/{cloudId}/wiki/api/v2/...
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "https://api.atlassian.com/ex/confluence/$ATLASSIAN_CLOUD_ID/wiki/api/v2/spaces?limit=1" | jq '.results[0] | {id, key, name}'
```

Set `ATLASSIAN_CLOUD_ID` **only** when the token is scoped — the `setup` skill switches every base URL on it. Grant only the scopes you need (for example `read:jira-work`, `write:jira-work`, `read:confluence-content.all`, `write:confluence-content`); a missing scope returns `403`.

### Official Atlassian Rovo MCP server (alternative)

Atlassian runs its own MCP server at `https://mcp.atlassian.com/v2/mcp` (OAuth 2.1 in the browser, or an API token / service-account key in the `Authorization` header; an org admin must allow it). The old v1 endpoint is switched to v2 automatically on 2027-03-01 — point new setups at the v2 URL.

| Use the MCP server when | Use this plugin's `curl` recipes when |
|---|---|
| quick reads and edits of issues, JQL searches, Confluence page reads/updates, with OAuth and no token in `.env` | you need the full API: workflows, fields and schemes, permission schemes, bulk operations, Confluence v1 (labels, attachments, CQL) |
| an interactive session in a client that already holds the connection | scripts, CI, or an admin has disabled the MCP server (Data Security Policy) |

The two can coexist; this plugin does not configure the MCP server for you.

## Notes

- **Jira rich text is ADF (JSON), not markdown** — `description` and comment `body` must be Atlassian Document Format documents.
- **Jira users are `accountId`** (not username/email) — resolve via `GET /rest/api/3/user/search`.
- **Confluence updates are read-then-write** — fetch the current `version.number`, then `PUT` with `number + 1`, or you get a `409`. In a space that **requires approval before publishing**, a direct `PUT` on a published page will return `409` whatever the version (CHANGE-3432, announced 2026-09-28, rollout pending). Atlassian says to save a draft, get it approved, then publish the approved draft; no REST draft→approval→publish flow is documented yet — use the UI or ask a Confluence admin.
- **Pagination differs**: Jira uses `startAt`/`maxResults` (and `nextPageToken` on `/search/jql`, which has no `total`); Confluence v2 uses cursor pagination (`_links.next`).
- **`/search/jql` needs a bounded JQL and returns only `id` unless you list `fields`.** To fetch many issues, search for ids and then `POST /issue/bulkfetch` (up to 1000 issues per call when `fields` is an explicit list without multi-value fields; 100 otherwise).
- **Workflow search is `GET /workflows/search`** — the older singular path was scheduled for removal on 2026-06-01 (CHANGE-2569); treat it as gone.
- **Rate limits:** API-token traffic is governed by per-endpoint burst limits (`429` + `Retry-After`, `X-RateLimit-*`, `RateLimit-Reason`); the points-based quotas enforced from 2026-03-02 apply to Forge/Connect/OAuth apps, not to API tokens.
- **Not in the bundled specs**: Scrum boards/sprints/backlog are the Jira Software Agile API (`/rest/agile/1.0`); Confluence label writes, attachment uploads, and CQL full-text search are the Confluence v1 API (`/wiki/rest/api`).
- The bundled `skills/api-reference/references/jira-openapi-v3.json` (423 paths, 620 operations) and `confluence-openapi-v2.json` (151 paths, 218 operations) are the exhaustive source of truth — grep them by `operationId` for exact schemas. They are re-downloaded from developer.atlassian.com; the counts and sources are in `skills/api-reference/SKILL.md`.

## License

Part of the AGENTS.STORE marketplace.
