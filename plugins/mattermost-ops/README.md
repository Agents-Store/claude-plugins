# mattermost-ops

Drive the **full [Mattermost](https://mattermost.com/) REST API v4** from Claude Code. Mattermost is an open-source, self-hostable team collaboration platform; this plugin teaches Claude every operation its API exposes — no MCP server required, just `curl` and a session token obtained from your admin credentials.

Built from the official API reference: https://docs.mattermost.com/api (OpenAPI 3.0 spec bundled in `skills/api-reference/references/mattermost-openapi-v4.yaml` — 512 path templates / 640 operations, built from the official sources of server v11.11.1).

## What it covers

Every documented resource group, including system administration:

- **Auth & users** — login/logout, sessions, personal access tokens (expiry, rotation), MFA, users CRUD, search/autocomplete, activation/deactivation, roles, preferences, status, profile images
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

- **No MCP dependency.** This is a pure REST knowledge plugin so it can cover *all* operations. Mattermost now ships an **official MCP server inside its Agents plugin** (server v11.2+): enable *System Console → Plugins → Agents → Model Context Protocol (MCP) → Enable Mattermost MCP Server (HTTP)*, then point your MCP client at `https://<your-server>/plugins/mattermost-ai/mcp-server/mcp` (streamable HTTP; a personal access token works out of the box, OAuth 2.0 needs *Enable OAuth 2.0 Service Provider* on, plus *Dynamic Client Registration* for automatic client registration). It exposes 16 native tools — read/search/create posts, DMs, channels, teams, members, `list_agents` — plus an on-demand extended catalogue, and runs with the calling user's permissions; read-only tools work on every licence, state-changing ones need Enterprise or above. See the [Agents admin guide](https://docs.mattermost.com/administration-guide/configure/agents-admin-guide.html#mattermost-mcp-server) and the [announcement](https://mattermost.com/blog/mattermost-mcp-server/). It is optional and not a match for full admin work (RBAC, config, compliance); community servers (`kakehashi-inc/mcp-server-mattermost`, `pvev/mattermost-mcp`) exist too.
- **Token lives in a header.** Unlike most APIs, Mattermost returns the session token in the `Token` HTTP response header on login — the `setup` skill extracts it. A `401` mid-session means it expired: log in again.
- **Personal access tokens can expire (v11.9+).** Create them with `expires_at` (Unix milliseconds); an admin may force an expiry through `MaximumPersonalAccessTokenLifetimeDays`; an expired PAT answers `401`; v11.10 adds `POST /users/tokens/rotate`, DM warnings 7/3/1 days before expiry and a bulk revoke of non-compliant tokens. Tokens made without `expires_at` (and all older ones) never expire. Details: `setup` and `references/auth-sessions.md`.
- **Admin role required for system endpoints.** A `403` on `/api/v4/system/*`, `/config`, `/roles`, `/ldap`, etc. means the account lacks the System Admin role — not a workaround target.
- **Heads-up for Mattermost v12.0 (October 2026).** A user session or PAT can no longer set sender-identity `props` (`from_webhook`, `override_username`, `override_icon_url`, …) on posts — the server **silently** drops them (use an incoming webhook or a bot instead); channel-member responses omit `last_viewed_at`/`last_update_at` for other users instead of returning `-1`; the built-in Slack team import endpoint is gone (use `mmetl` + `mmctl import`). Removed already: `POST /posts/ids/reactions` (v11.11) and the `format` parameter on `/config/client`.

## License

Part of the [AGENTS.STORE](https://agents.store) Claude Code plugin marketplace.
