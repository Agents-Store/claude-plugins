# outline-ops

Drive the **full [Outline](https://www.getoutline.com/) REST API** from Claude Code. Outline is an open-source, self-hostable team knowledge base / wiki; this plugin teaches Claude every operation its API exposes — no MCP server required, just `curl` and a Bearer API key. (Outline also ships a [built-in MCP server](#built-in-outline-mcp-server) in every workspace; it is optional and complementary.)

Built from the official API reference: https://www.getoutline.com/developers (OpenAPI 3.0 spec bundled in `skills/api-reference/references/outline-openapi.yml` — 154 operations across 26 resource groups; snapshot of [`outline/openapi`](https://github.com/outline/openapi) `spec3.yml` at commit `40f51b75ef`, 2026-09-23, matching Outline server v1.10.1).

## What it covers

Every documented resource group:

- **Documents** — create/import, read, update (append/prepend/replace/patch, optimistic concurrency via `lastRevision`), search (full-text & title) and list with structured `filters`, move, archive/restore, trash & empty-trash, duplicate, templatize, unpublish, export (markdown/HTML/PDF/TextBundle/zip), insights, drafts, recently-viewed, AI answers, and per-document user/group memberships
- **Collections** — CRUD, archive/restore, reorder, duplicate, import, document tree, user & group memberships, export / export-all
- **Comments & reactions** — create (inc. inline anchored & threaded replies), read, update (markdown `text` or editor `data`), delete, list, resolve/unresolve, emoji reactions
- **Pins, subscriptions & notifications** — pin documents to a collection or home screen, subscribe to documents/collections, read and clear notifications, choose notification types
- **Stars & Views** — star/unstar documents & collections, reorder, list view counts
- **Sharing, access & webhooks** — public share links (create/update/revoke/list), access requests (create/approve/dismiss), auth info & config, workspace webhook subscriptions (admin)
- **Users & groups** — invite/resend, list/filter, update, change email and role, suspend/activate, delete; group CRUD, group roles and membership management; documents shared with the current user or their groups
- **Attachments & file operations** — create upload, create from a URL, list, redirect-to-file, delete; import/export job status, list, redirect, delete
- **Revisions** — list, retrieve, name, delete and export historical document snapshots
- **Templates** — CRUD (draft/published), restore, duplicate (reusable document starting points)
- **Events** — the workspace audit trail / activity stream
- **API keys & OAuth** — personal API key create/list/revoke, OAuth client CRUD + secret rotation, and user OAuth authentication management
- **Data attributes** — custom document metadata fields (Business / Enterprise)

## Skills

| Skill | Auto-loads? | Purpose |
|-------|-------------|---------|
| `setup` | yes | Read `OUTLINE_API_KEY` + `OUTLINE_API_URL`, verify with `auth.info`, and learn the global conventions (RPC POST style, Bearer header, response envelope, limit/offset pagination, sorting, rate limits, policies) |
| `common-operations` | yes | Plain-language playbooks for everyday work — create/find/update documents, organize collections, share, manage people & permissions, run reports |
| `api-reference` | on request | Full endpoint catalog (154 operations), split across 8 domain files under `references/`, plus the raw OpenAPI spec |
| `troubleshoot` | yes | Symptom → cause → fix for 401/403/404/429/400, empty `.data`, title-vs-UUID mistakes, self-hosted URL/SSL issues |
| `examples` | yes | End-to-end scenarios: publish a knowledge base, document lifecycle, search & report, onboard users & permissions |

Plus the **`outline-assistant`** agent — a plain-language knowledge-base assistant that orchestrates these operations.

## Prerequisites

Set these environment variables (shell, or this repo's `.env`):

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `OUTLINE_API_URL` | yes | `https://app.getoutline.com/api` | API base **including `/api`**. Self-hosted: `https://wiki.mycompany.com/api`. |
| `OUTLINE_API_KEY` | yes | `ol_api_••••` | Personal API key, created under **Settings → API & Apps** (or with `apiKeys.create`). Always starts with `ol_api_`. Treat it like a password. |

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

## Built-in Outline MCP server

Since 2026-02-18 every Outline workspace — cloud and self-hosted — has an MCP server built in ([announcement](https://www.getoutline.com/changelog/mcp), [setup guide](https://docs.getoutline.com/s/guide/doc/mcp-6j9jtENNKL)). This plugin does **not** ship or require it; it is a complement for interactive use.

- **Transport & URL:** Streamable HTTP only. The URL is the workspace origin plus `/mcp` — `https://<yoursubdomain>.getoutline.com/mcp` on cloud, `https://<your-outline-domain>/mcp` when self-hosted. It is **not** `OUTLINE_API_URL` (that one ends in `/api`).
- **Enable it:** an admin can toggle MCP under **Settings → Workspace → AI**; if clients cannot connect, check that it has not been disabled. The same page has a field for extra guidance shown to MCP clients.
- **Authentication:** OAuth by default — the client opens a sign-in window. API-key auth is also supported with the header `Authorization: Bearer <your-api-key>`.
- **Claude Code (OAuth):**
  ```bash
  claude mcp add --transport http outline https://<yoursubdomain>.getoutline.com/mcp
  # then run /mcp inside Claude Code and follow the sign-in flow
  ```
- **Claude Code (API key, in a project `.mcp.json` — the key stays in the environment):**
  ```json
  {
    "mcpServers": {
      "outline": {
        "type": "http",
        "url": "https://<your-outline-domain>/mcp",
        "headers": { "Authorization": "Bearer ${OUTLINE_API_KEY}" }
      }
    }
  }
  ```
- **Tool names:** because you connect the server yourself, its tools appear under the name you chose — `mcp__outline__<tool>` for a server called `outline`. List them with `/mcp`; the exact set grows with Outline releases (search, read, create/edit/delete for documents and collections, document restore, templates, comments).
- **STDIO-only clients** can bridge with `npx -y mcp-remote https://<yoursubdomain>.getoutline.com/mcp`.
- **REST or MCP?** Use the MCP server for interactive search/read/edit with OAuth sign-in and no static key. Use this plugin's REST skills for scripting, admin (users, groups, API keys, webhooks, OAuth clients), bulk and file operations (import/export, attachments) and anything the MCP tool list does not cover.

## Notes

- **No MCP dependency.** This is a pure REST knowledge plugin so it can cover *all* operations. Besides Outline's built-in MCP server (above), community Outline MCP servers exist (Python [`Vortiago/mcp-outline`](https://github.com/Vortiago/mcp-outline), npm [`outline-mcp-server`](https://www.npmjs.com/package/outline-mcp-server), Rust [`nizovtsevnv/outline-mcp-rs`](https://github.com/nizovtsevnv/outline-mcp-rs)) and use the same `OUTLINE_API_KEY`/`OUTLINE_API_URL` variables — they expose a convenient subset (search/read/create/edit) and are optional, not required.
- **RPC style.** Outline's API is not REST-by-noun — every endpoint is a `POST` to `${OUTLINE_API_URL}/<method>` (e.g. `documents.info`), with parameters in a JSON body. There are no path parameters.
- **Bearer key, no login flow.** Unlike session-based APIs, Outline authenticates with a static `ol_api_…` key on every call. A `401` means the key is missing, wrong, or revoked.
- **Policies, not roles, gate writes.** Most responses include a `policies` array describing what the current key may do to each object. A `403` is a real boundary — respect it rather than routing around it.

## License

Part of the [AGENTS.STORE](https://agents.store) Claude Code plugin marketplace.
