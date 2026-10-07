---
description: Check that a Vaultwarden server is reachable and that the local Bitwarden CLI version is compatible with it (read-only)
argument-hint: [server-url]
allowed-tools: [Read, "Bash(curl:*)", "Bash(bw --version)", "Bash(bw config server)", "Bash(bw status:*)", "Bash(npm view:*)", "Bash(jq:*)"]
---

# Check Vaultwarden / bw compatibility

Read-only diagnosis of a Vaultwarden server. The URL comes from the command argument; without one, use the server configured in `bw config server`; if that still points at Bitwarden's own cloud (the CLI default when no server was configured), ask the user for the URL. Nothing is changed on the server or in the CLI configuration.

## 1. Collect

Run each probe and keep going if one fails — a failure is itself a finding.

```bash
URL="$ARGUMENTS"
[ -n "$URL" ] || URL="$(bw config server 2>/dev/null)"
URL="${URL%/}"
echo "server url: $URL"
curl -sS -o /dev/null -w 'alive: %{http_code}\n' "$URL/alive"
echo "vaultwarden: $(curl -fsS "$URL/api/version" | tr -d '"')"
curl -fsS "$URL/api/config" | jq -r '"emulates bitwarden: \(.version)  server: \(.server.name // "?")  git: \(.gitHash // "?")"'
echo "bw: $(bw --version 2>/dev/null || echo 'not installed')"
echo "bw configured server: $(bw config server 2>/dev/null || echo '-')"
bw status 2>/dev/null | jq -r '"bw status: \(.status)  last sync: \(.lastSync // "-")"'
echo "latest bw on npm: $(npm view @bitwarden/cli version 2>/dev/null || echo '?')"
```

`$ARGUMENTS` is replaced by the command argument when the command runs; with no argument it is empty and the configured server is used.

## 2. Judge

Read the version matrix at `${CLAUDE_PLUGIN_ROOT}/skills/troubleshoot/references/version-matrix.md` (the single source for version advice in this plugin) and compare. In addition:

| Condition | Verdict |
|---|---|
| `/alive` not 200 | server or reverse proxy down — stop, see `vaultwarden-dev:troubleshoot` |
| `server.name` is not `Vaultwarden` | this is not a Vaultwarden instance (official Bitwarden server?) — plugin advice may not apply |
| configured `bw` server ≠ checked URL | the CLI talks to a different server — `bw logout`, then `bw config server <url>` |
| client below the matrix minimum for this server | **broken** — upgrade the server, or pin `bw` per the matrix |
| server ≥ 1.37.4 and `bw` older than 2026.8.0 | **risky** — may still call the removed prelogin route; upgrade `bw` |
| none of the above | compatible |

Version comparison helper:

```bash
vge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]; }   # vge A B  → A >= B
vge "1.37.4" "1.37.2" && echo "1.37.4 >= 1.37.2"
```

## 3. Report

Answer in a few lines: server version, CLI version, verdict (compatible / risky / broken), and the one action to take if not compatible. Do not print tokens, session keys or `bw status` fields other than status, server URL and last sync.
