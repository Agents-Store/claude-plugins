# outline-ops

Drive the **full [Outline](https://www.getoutline.com/) REST API** from Claude Code. Outline is an open-source, self-hostable team knowledge base / wiki; this plugin teaches Claude every operation its API exposes — no MCP server required, just `curl` and a Bearer API key.

Built from the official API reference: https://www.getoutline.com/developers (OpenAPI 3.0 spec bundled in `skills/api-reference/references/outline-openapi.yml` — 112 operations across 18 resource groups).

## What it covers

Every documented resource group:

- **Documents** — create/import, read, update (append/prepend/replace/patch), search (full-text & title), move, archive/restore, trash & empty-trash, duplicate, templatize, unpublish, export (markdown/HTML/PDF/zip), insights, drafts, recently-viewed, AI answers, and per-document user/group memberships
- **Collections** — CRUD, document tree, user & group memberships, export / export-all
- **Comments** — create (inc. inline anchored & threaded replies), read, update, delete, list
- **Stars & Views** — star/unstar documents & collections, reorder, list view counts
- **Sharing & access** — public share links (create/update/revoke/list), access requests (create/approve/dismiss), auth info & config
- **Users & groups** — invite, list/filter, update, change role, suspend/activate, delete; group CRUD and membership management
- **Attachments & file operations** — create upload, redirect-to-file, delete; import/export job status, list, redirect, delete
- **Revisions** — list and retrieve historical document snapshots
- **Templates** — CRUD, restore, duplicate (reusable document starting points)
- **Events** — the workspace audit trail / activity stream
- **OAuth** — OAuth client CRUD + secret rotation, and user OAuth authentication management
- **Data attributes** — custom document metadata fields (Business / Enterprise)

## Skills

| Skill | Auto-loads? | Purpose |
|-------|-------------|---------|
| `setup` | yes | Read `OUTLINE_API_KEY` + `OUTLINE_API_URL`, verify with `auth.info`, and learn the global conventions (RPC POST style, Bearer header, response envelope, limit/offset pagination, sorting, rate limits, policies) |
| `common-operations` | yes | Plain-language playbooks for everyday work — create/find/update documents, organize collections, share, manage people & permissions, run reports |
| `api-reference` | on request | Full endpoint catalog, split across 8 domain files under `references/`, plus the raw OpenAPI spec |
| `troubleshoot` | yes | Symptom → cause → fix for 401/403/404/429/400, empty `.data`, title-vs-UUID mistakes, self-hosted URL/SSL issues |
| `examples` | yes | End-to-end scenarios: publish a knowledge base, document lifecycle, search & report, onboard users & permissions |

Plus the **`outline-assistant`** agent — a plain-language knowledge-base assistant that orchestrates these operations.

## Prerequisites

Set these environment variables (shell, or this repo's `.env`):

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `OUTLINE_API_URL` | yes | `https://app.getoutline.com/api` | API base **including `/api`**. Self-hosted: `https://wiki.mycompany.com/api`. |
| `OUTLINE_API_KEY` | yes | `ol_api_••••` | Personal API key, created under **Settings → API Keys**. Always starts with `ol_api_`. Treat it like a password. |

In this repo, add the two vars to `.env.example`, store real values in Infisical, and run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull them locally.

## Quick start

Ask Claude in plain language, e.g.:

- "Search Outline for our onboarding docs and show me the top 5"
- "Create a 'Handbook' collection and add a 'Welcome' document under it, then publish"
- "Share the Welcome doc publicly and give me the link"
- "Invite alice@acme.com and bob@acme.com as members and add them to the Handbook collection"
- "Give me a report of the most-viewed documents this month"

## Authentication

```bash
# Every call is a POST to ${OUTLINE_API_URL}/<method> with a Bearer key.
curl -s -X POST "${OUTLINE_API_URL%/}/auth.info" \
  -H "Authorization: Bearer ${OUTLINE_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" | jq '.data'
```

## Notes

- **No MCP dependency.** This is a pure REST knowledge plugin so it can cover *all* operations. Community Outline MCP servers exist (Python [`Vortiago/mcp-outline`](https://github.com/Vortiago/mcp-outline), npm [`outline-mcp-server`](https://www.npmjs.com/package/outline-mcp-server), Rust [`nizovtsevnv/outline-mcp-rs`](https://github.com/nizovtsevnv/outline-mcp-rs)) and use the same `OUTLINE_API_KEY`/`OUTLINE_API_URL` variables — they expose a convenient subset (search/read/create/edit) and are optional, not required.
- **RPC style.** Outline's API is not REST-by-noun — every endpoint is a `POST` to `${OUTLINE_API_URL}/<method>` (e.g. `documents.info`), with parameters in a JSON body. There are no path parameters.
- **Bearer key, no login flow.** Unlike session-based APIs, Outline authenticates with a static `ol_api_…` key on every call. A `401` means the key is missing, wrong, or revoked.
- **Policies, not roles, gate writes.** Most responses include a `policies` array describing what the current key may do to each object. A `403` is a real boundary — respect it rather than routing around it.

## License

Part of the [AGENTS.STORE](https://agents.store) Claude Code plugin marketplace.
