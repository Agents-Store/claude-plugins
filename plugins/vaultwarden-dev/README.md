# vaultwarden-dev

Developer plugin for [Vaultwarden](https://github.com/dani-garcia/vaultwarden) — the self-hosted, Rust re-implementation of the Bitwarden server. It teaches the agent what Vaultwarden's API can and cannot do, how to script it safely, and how to keep decrypted secrets out of the conversation.

File-based knowledge: no MCP server, no stored credentials, no environment variables required by the plugin itself. Verified against Vaultwarden 1.37.4 (2026-10-05) and Bitwarden CLI 2026.9.

## What Vaultwarden exposes

| Surface | Path | Auth | Good for |
|---|---|---|---|
| Bitwarden client API | `/identity`, `/api` | bearer from `/identity/connect/token` | org members, policies, events, item delete/restore |
| Admin panel API | `/admin` | `ADMIN_TOKEN` → `VW_ADMIN` cookie | users, 2FA reset, orgs, config, SQLite backup |
| Public API (partial) | `/api/public/organization/import` | org API key | directory sync only |
| Bitwarden CLI / `bw serve` | local | API key + master password | anything touching encrypted vault content |

Vault content is end-to-end encrypted, so item reads and writes go through `bw`; Secrets Manager (`bws`) is not implemented by Vaultwarden.

## Skills

| Skill | Purpose |
|---|---|
| `setup` | pick the right surface, health checks, `bw config server`, API-key login, unlock, bearer token, admin token hash |
| `api-reference` | route tables, token grants, master-password hash, Public API import (manual-invoke reference) |
| `admin-panel` | `/admin` login with the cookie, every admin route, recipes, config keys and backup layout |
| `cli-recipes` | `bw` recipes: find, capture, create, edit, move, confirm members, generate, export; `bw serve` local API |
| `secret-hygiene` | rules that keep master passwords, session keys and item secrets out of the transcript, argv and git |
| `sdk-patterns` | `python-vaultwarden` (admin and org clients) and the `maxlaverse/bitwarden` Terraform provider |
| `mcp-patterns` | wiring `warden-mcp` or the official Bitwarden MCP server yourself, and what does not work on Vaultwarden |
| `troubleshoot` | version coupling, login/token errors, rate limits, admin panel, org and sync problems |
| `examples` | onboarding, offboarding, CI secrets, backup and upgrade walkthroughs |

## Agent

`vaultwarden-developer` — writes and debugs integrations (scripts, services, CI, Terraform) against Vaultwarden, respecting the encryption boundary and asking before destructive calls.

## Command

`/vaultwarden-dev:check-version [server-url]` — read-only: server health and version, local `bw` version, and a compatibility verdict.

## Hook

A `PreToolUse` hook on Bash (`scripts/bw_guard.py`, needs `python3`) answers **ask** before a command would print decrypted vault data into the conversation: `bw list items`, `bw get item|password|totp|notes`, uncaptured `bw unlock`/`bw login`, plain-text `bw export`, `bw serve` exposed beyond localhost, `bw serve` secret endpoints, `rbw get`, and echoing `BW_SESSION`/`BW_PASSWORD`/admin tokens. Output captured into a variable (`X="$(bw get password <id>)"`), redirected to a file or piped to the clipboard passes silently; a capture that is echoed straight back still asks. It never blocks, makes no network calls and fails open. Agents that drop hooks get the same rules from the `secret-hygiene` skill.

## Installation

```bash
claude plugin marketplace add Agents-Store/claude-plugins
claude plugin install vaultwarden-dev@agents-store
```

## Prerequisites

- A reachable Vaultwarden server (any user account; the admin panel needs `ADMIN_TOKEN` set by the operator).
- `curl` and `jq`; the Bitwarden CLI (`npm install -g @bitwarden/cli`) for vault content; `python3` for the guard hook.
- Credentials are entered by you at run time (`read -r -s`) or come from your own secret store — the plugin never asks you to paste them into the chat.

## Sources

- Vaultwarden source (`src/api/`) and wiki: https://github.com/dani-garcia/vaultwarden
- Bitwarden CLI source: https://github.com/bitwarden/clients/tree/main/apps/cli — user docs and the Vault Management API (`bw serve`) spec are in the Bitwarden Help Center
- python-vaultwarden: https://github.com/numberly/python-vaultwarden
- Terraform provider: https://github.com/maxlaverse/terraform-provider-bitwarden
