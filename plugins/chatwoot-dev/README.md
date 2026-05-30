# chatwoot-dev

Complete **Chatwoot API + CLI** coverage for Claude Code — a Technology (dev) plugin for the
Agents Store marketplace. Knowledge-only: **no MCP server, no bundled credentials**. Every
example runs through `curl` or the official `chatwoot` CLI on your machine, against Chatwoot
Cloud (`https://app.chatwoot.com`) or a self-hosted instance.

## What it covers

The three Chatwoot API families plus the official CLI:

- **Application API** (`/api/v1/accounts/{id}`) — agent/account automation: conversations,
  messages, contacts, inboxes, teams, agents, agent bots, canned responses, custom
  attributes & filters, automation rules, webhooks, help center, reports, audit logs.
- **Platform API** (`/platform/api/v1`) — installation provisioning: accounts, users,
  account-users, agent bots, SSO links.
- **Public/Client API** (`/public/api/v1/inboxes/{inbox_identifier}`) — building a custom
  chat widget (unauthenticated).

The raw OpenAPI specs are bundled under
`skills/api-reference/references/openapi/` so the agent can grep authoritative schemas.

## Skills

| Skill | Use it for |
|-------|------------|
| `setup` | Get an access token, set `CHATWOOT_*` env vars, install the CLI, verify access |
| `api-reference` | All endpoints, per-family guides, and the bundled OpenAPI specs (manual-load: `disable-model-invocation`) |
| `cli-recipes` | The `chatwoot` CLI — grammar, `-o json`/`-q` output contract, triage recipes, safety |
| `webhooks-automation` | Webhooks (+ HMAC signature verification), automation rules, agent bots, integrations |
| `troubleshoot` | 401/403/404/422/429, CLI auth, webhook signature mismatches |
| `examples` | Worked end-to-end scenarios (seed conversation, agent bot, bulk import, CLI triage) |

## Agent

`chatwoot-assistant` — a Chatwoot specialist that picks the right API family + token, writes
integration code, builds bots and webhook handlers, scripts the CLI, and debugs auth issues.
It confirms before any customer-visible write.

## Commands

- `/chatwoot-dev:api-call [resource/action]` — build (and run, for GETs) an authenticated
  request against the correct API family; confirms before writes.
- `/chatwoot-dev:troubleshoot [symptom]` — run read-only connectivity/auth/scope checks and
  report the fix.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `CHATWOOT_API_KEY` | Application user **access token** (Profile Settings → Access Token). Auth header is `api_access_token`. |
| `CHATWOOT_BASE_URL` | Instance origin, e.g. `https://app.chatwoot.com` or your self-hosted URL (no trailing slash). |
| `CHATWOOT_ACCOUNT_ID` | Numeric account id from the dashboard URL `.../app/accounts/{id}/...`. |
| `CHATWOOT_PLATFORM_TOKEN` | (Optional) Platform app token, only for `/platform/api/v1` provisioning. |

No plugin configuration is required — set the env vars in your shell or secrets manager.

## Quick start

```bash
export CHATWOOT_BASE_URL="https://app.chatwoot.com"
export CHATWOOT_API_KEY="your_access_token"
export CHATWOOT_ACCOUNT_ID="1"

# REST
curl -s -H "api_access_token: ${CHATWOOT_API_KEY}" \
  "${CHATWOOT_BASE_URL}/api/v1/accounts/${CHATWOOT_ACCOUNT_ID}/conversations" | jq '.data.meta'

# CLI
curl -fsSL https://chwt.app/install-cli | sh
chatwoot auth login
chatwoot convs
```

## Notes

- Several community Chatwoot **MCP servers** exist, but there is no official/public one and
  this plugin is intentionally CLI- and API-focused (no `.mcp.json`).
- Built from the official Chatwoot API docs (https://developers.chatwoot.com) and the
  official CLI (https://github.com/chatwoot/cli). The `cli-recipes` skill adapts the upstream
  `chatwoot-cli` agent skill (MIT).

---

Made by **AGENTS.STORE**.
