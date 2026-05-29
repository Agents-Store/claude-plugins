# atlassian-ops

Jira + Confluence Cloud **ops** plugin for Agents Store. Drive the full **Jira Cloud REST API v3** and **Confluence Cloud REST API v2** by `curl`, with both official OpenAPI specs bundled as the source of truth. One Atlassian API token authenticates both products.

## What it covers

**Jira (REST v3, `/rest/api/3`)**
- Issues — create, edit, assign, transition, delete (ADF bodies), bulk operations, archive
- Search — JQL (`/search/jql`), approximate counts, JQL tooling
- Comments, worklogs (time tracking), and issue properties
- Attachments (multipart), issue links, remote links
- Projects, versions (releases), components, roles, categories, features, templates
- Fields, custom field contexts & options, field configurations, screens & screen schemes
- Workflows, workflow schemes (+ drafts), statuses, issue types & schemes
- Users & groups (`accountId`), permissions & schemes, security, notifications, priorities, resolutions
- Dashboards, gadgets, filters & sharing; Advanced Roadmaps plans & teams

**Confluence (REST v2, `/wiki/api/v2`)**
- Pages & blog posts — create/update (versioned, storage or ADF bodies), hierarchy, custom content, whiteboards, databases, folders, smart links
- Spaces, space properties, permissions, roles
- Footer & inline comments, attachments, versions, likes, tasks, operations
- Labels, content properties, classification levels, data policies, redactions

## Skills

| Skill | Use it to |
|-------|-----------|
| `setup` | Authenticate (Basic auth: email + API token) and learn the conventions both APIs share |
| `jira-operations` | Plain-language playbooks for everyday Jira work |
| `confluence-operations` | Plain-language playbooks for everyday Confluence work |
| `api-reference` | The full per-domain endpoint catalog + the bundled OpenAPI specs (reference-only) |
| `examples` | Worked end-to-end scenarios chaining real API calls |
| `troubleshoot` | Map 400/401/403/404/409/429 and the common pitfalls to fixes |

There is one agent, `atlassian-assistant`, that drives all of the above.

## Prerequisites

- An Atlassian Cloud site (`https://your-domain.atlassian.net`)
- An API token: https://id.atlassian.com/manage-profile/security/api-tokens
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
curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_API_TOKEN" -H "Accept: application/json" \
  "$ATLASSIAN_SITE_URL/rest/api/3/search/jql" -H "Content-Type: application/json" \
  -X POST -d '{"jql":"order by created DESC","maxResults":3,"fields":["summary","status"]}'
```

Set `ATLASSIAN_SITE_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN` in your shell or repo `.env`. Never commit the token.

## Notes

- **Jira rich text is ADF (JSON), not markdown** — `description` and comment `body` must be Atlassian Document Format documents.
- **Jira users are `accountId`** (not username/email) — resolve via `GET /rest/api/3/user/search`.
- **Confluence updates are read-then-write** — fetch the current `version.number`, then `PUT` with `number + 1`, or you get a `409`.
- **Pagination differs**: Jira uses `startAt`/`maxResults` (and `nextPageToken` on `/search/jql`); Confluence v2 uses cursor pagination (`_links.next`).
- **Not in the bundled specs**: Scrum boards/sprints/backlog are the Jira Software Agile API (`/rest/agile/1.0`); Confluence label writes, attachment uploads, and CQL full-text search are the Confluence v1 API (`/wiki/rest/api`).
- The bundled `skills/api-reference/references/jira-openapi-v3.json` and `confluence-openapi-v2.json` are the exhaustive source of truth — grep them by `operationId` for exact schemas.

## License

Part of the AGENTS.STORE marketplace.
