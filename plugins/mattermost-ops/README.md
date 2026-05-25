# mattermost-ops

Drive the **full [Mattermost](https://mattermost.com/) REST API v4** from Claude Code. Mattermost is an open-source, self-hostable team collaboration platform; this plugin teaches Claude every operation its API exposes — no MCP server required, just `curl` and a session token obtained from your admin credentials.

Built from the official API reference: https://api.mattermost.com/ (OpenAPI 3.0 spec bundled in `skills/api-reference/references/mattermost-openapi-v4.yaml`).

## What it covers

Every documented resource group, including system administration:

- **Auth & users** — login/logout, sessions, personal access tokens, MFA, users CRUD, search/autocomplete, activation/deactivation, roles, preferences, status, profile images
- **Teams** — teams CRUD, members, invites, stats, search, team schemes
- **Channels** — public/private channels, direct & group messages, members, stats, bookmarks, sidebar categories, moderation
- **Posts** — posts & threads, replies, pinning, reactions, drafts, ephemeral messages, full-text search
- **Files & emoji** — multipart uploads, metadata, thumbnails/previews, custom emoji
- **Integrations** — incoming/outgoing webhooks, slash commands, bots, OAuth apps, interactive dialogs
- **System administration** — server config, license, analytics & logs, compliance, data retention, plugins, jobs, cluster, ping/health, cloud
- **Access control** — RBAC roles, schemes, and LDAP/SAML groups

## Skills

| Skill | Auto-loads? | Purpose |
|-------|-------------|---------|
| `setup` | yes | Obtain the session token from username/password (read from the `Token` response header); learn the global conventions (Bearer header, base path, pagination, rate limits) |
| `common-operations` | yes | Plain-language playbooks for everyday work — post messages, manage channels & members, onboard users, run reports |
| `api-reference` | on request | Full endpoint catalog, split across 9 domain files under `references/`, plus the raw OpenAPI spec |
| `troubleshoot` | yes | Symptom → cause → fix for 401/403/404/429, empty `Token` header, name-vs-ID mistakes, pagination |
| `examples` | yes | End-to-end scenarios: onboard a team, channel management, bulk messaging, admin audit |

Plus the **`mattermost-assistant`** agent — a plain-language collaboration assistant that orchestrates these operations.

## Prerequisites

Set these environment variables (shell, or this repo's `.env`):

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `MATTERMOST_API_URL` | yes | `https://mattermost.mycompany.com` | Server root — the API is served under `/api/v4`. No trailing slash needed. |
| `MATTERMOST_ADMIN_USERNAME` | yes | `admin` | Username **or** email used to log in. |
| `MATTERMOST_ADMIN_PASSWORD` | yes | `••••••••` | Password for that account (must hold the System Admin role for admin operations). |
| `MATTERMOST_TOKEN` | derived | — | Obtained at runtime by the `setup` skill from the login `Token` header; reused for the session. |

In this repo, add the three input vars to `.env.example`, store real values in Infisical, and run `./scripts/setup.sh dev .env .claude/settings.local.json` to pull them locally.

## Quick start

Ask Claude in plain language, e.g.:

- "Log into Mattermost and list my teams"
- "Post an announcement to #general in the Engineering team"
- "Create a 'Launch' team with #announcements and #support, then add these 4 users"
- "Give me a report of inactive users and channel counts per team"
- "Create an incoming webhook on the #alerts channel"

## Authentication flow

```bash
# setup skill runs this for you — the token comes back in the Token RESPONSE HEADER, not the body
MATTERMOST_TOKEN=$(curl -si -X POST "${MATTERMOST_API_URL%/}/api/v4/users/login" \
  -H "Content-Type: application/json" \
  -d "{\"login_id\":\"${MATTERMOST_ADMIN_USERNAME}\",\"password\":\"${MATTERMOST_ADMIN_PASSWORD}\"}" \
  | awk 'tolower($1)=="token:"{print $2}' | tr -d '\r')
# sent on every call as: Authorization: Bearer ${MATTERMOST_TOKEN}
```

## Notes

- **No MCP dependency.** This is a pure REST knowledge plugin so it can cover *all* operations. The official Mattermost MCP server and community ones (`kakehashi-inc/mcp-server-mattermost`, `pvev/mattermost-mcp`) authenticate with Personal Access Tokens and expose only a handful of tools (read/search/create posts) — optional convenience, not required and not a match for full admin operations.
- **Token lives in a header.** Unlike most APIs, Mattermost returns the session token in the `Token` HTTP response header on login — the `setup` skill extracts it. A `401` mid-session means it expired: log in again.
- **Admin role required for system endpoints.** A `403` on `/api/v4/system/*`, `/config`, `/roles`, `/ldap`, etc. means the account lacks the System Admin role — not a workaround target.

## License

Part of the [AGENTS.STORE](https://agents.store) Claude Code plugin marketplace.
