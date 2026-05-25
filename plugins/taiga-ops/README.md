# taiga-ops

Drive the **full [Taiga](https://www.taiga.io/) REST API** from Claude Code. Taiga is an open-source Scrum/Kanban project-management platform; this plugin teaches Claude every operation its API exposes — no MCP server required, just `curl` and an auth token obtained from your admin credentials.

Built from the official API reference: https://docs.taiga.io/api.html

## What it covers

Every documented resource group:

- **Projects & access** — projects, templates, memberships/invitations, roles, permissions, tags, modules, stats, duplicate, logo
- **Work items** — epics, user stories, tasks, issues — full lifecycle (create, edit, move, assign, tag, comment, attach, vote, watch, bulk operations)
- **Classifiers** — statuses, issue types, priorities, severities, points, and custom attributes (+ values) for each item type
- **Sprints & wiki** — milestones (with stats), wiki pages, wiki links, attachments
- **Activity** — history & comments, webhooks, webhook logs, notify policies
- **Discovery & data** — search, resolver, project/sprint/system stats, export/import, and Trello/GitHub/Jira importers

## Skills

| Skill | Auto-loads? | Purpose |
|-------|-------------|---------|
| `setup` | yes | Obtain the auth token from username/password; learn the global conventions (headers, pagination, `version` locking, resolver) |
| `common-operations` | yes | Plain-language playbooks for everyday work — create items, plan sprints, triage bugs, manage members, report |
| `api-reference` | on request | Full endpoint catalog, split across 9 domain files under `references/` |
| `troubleshoot` | yes | Symptom → cause → fix for 401/403/404, version conflicts, pagination, classifier IDs |
| `examples` | yes | End-to-end scenarios: bootstrap a project, sprint planning, bug triage, reporting & export |

Plus the **`taiga-assistant`** agent — a plain-language PM assistant that orchestrates these operations.

## Prerequisites

Set these environment variables (shell, or this repo's `.env`):

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `TAIGA_API_URL` | yes | `https://taiga.mycompany.com` or `https://api.taiga.io` | Instance root — the API is served under `/api/v1`. No trailing slash needed. |
| `TAIGA_ADMIN_USERNAME` | yes | `admin` | Username or email used to log in. |
| `TAIGA_ADMIN_PASSWORD` | yes | `••••••••` | Password for that account. |
| `TAIGA_AUTH_TOKEN` | derived | — | Obtained at runtime by the `setup` skill via `POST /api/v1/auth`; reused for the session. |

In this repo, add the three input vars to `.env.example`, store real values in Infisical, and run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull them locally.

## Quick start

Ask Claude in plain language, e.g.:

- "Log into Taiga and show my projects"
- "Create a two-week sprint in the Apollo project and add these 5 stories"
- "File a high-severity bug about checkout failing and assign it to me"
- "Summarize open issues and remaining sprint points for Apollo"
- "Give me the curl to create a webhook on project 7"

## Authentication flow

```bash
# setup skill runs this for you
curl -s -X POST "${TAIGA_API_URL%/}/api/v1/auth" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"normal\",\"username\":\"${TAIGA_ADMIN_USERNAME}\",\"password\":\"${TAIGA_ADMIN_PASSWORD}\"}" \
  | jq -r .auth_token   # -> TAIGA_AUTH_TOKEN, sent as: Authorization: Bearer <token>
```

## Notes

- **No MCP dependency.** This is a pure REST knowledge plugin so it can cover *all* operations. Community MCP servers (`greddy7574/taiga-mcp-server`, `talhaorak/pytaiga-mcp`) exist and cover a subset (~33 tools) — optional convenience, not required.
- **Optimistic locking.** Taiga rejects edits that omit or use a stale `version`. The skills always `GET` an item before editing it.
- **Swimlanes** are not part of the documented REST API and are intentionally omitted.

## License

Part of the [AGENTS.STORE](https://agents.store) Claude Code plugin marketplace.
