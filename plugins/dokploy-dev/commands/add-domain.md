---
description: Add a custom domain to a Dokploy application
argument-hint: <domain> --app <app-name-or-id> [--port <port>] [--https]
allowed-tools: [Read, Bash, Skill, Agent]
---

# Add Domain

Add a custom domain to a Dokploy application with optional HTTPS.

## Arguments
Format: `<domain> --app <app-name-or-id> [--port <port>] [--https]`
- domain: Domain name, e.g. app.example.com (required)
- --app: Application name or ID (required)
- --port: Application port (default: 3000)
- --https: Enable HTTPS with Let's Encrypt certificate (optional flag)

Parse from "$ARGUMENTS".

## Process

1. **Resolve application** — if --app is a name, resolve via `project-all` and `project-one`.

1b. **DNS record (optional, v0.30+).** `domain-create` does not create the DNS record. If `dnsProvider-all` lists a provider whose zone (`dnsProvider-listZones`, `dnsProvider-listRecords`) covers the domain and no A/CNAME record exists yet, offer to create it — with explicit user confirmation, because it changes real DNS: `dnsProvider-createRecord { dnsProviderId, zoneId, type: "A", name: "<host>", content: "<server public IP>" }` (server IP from `server-publicIp` or `settings-getIp`). If that tool is not in your session (some MCP clients drop `dnsProvider-createRecord`), use the REST endpoint `POST /api/dnsProvider.createRecord` with the same body. No provider configured? Skip this step and tell the user to add the record at their DNS host.

2. **Create domain** using MCP tool `domain-create` with:
   - `host`: the domain name
   - `applicationId`: resolved application ID
   - `port`: specified port or 3000
   - `path`: `/`
   - `https`: true if --https flag provided

3. **Validate domain** using MCP tool `domain-validateDomain { domain: "<host>", serverId? }` — pass the **hostname string** (NOT the domainId) to check DNS resolution; add `serverId` when the application runs on a remote server so the check uses that server's IPs.

4. **Display result:**
   Show domain, port, HTTPS status, and validation result. If DNS not resolving, remind user to add an A record pointing to the server IP.

To take a domain out of service later without deleting it, use `domain-toggleEnable { domainId }` (v0.30+) — it flips `enabled`; certificate, path and middleware settings are kept. Applications change instantly; compose domains change on the next deploy.

## Example Usage
```
/dokploy-dev:add-domain app.example.com --app web-frontend --https
/dokploy-dev:add-domain api.example.com --app api-server --port 8000 --https
/dokploy-dev:add-domain staging.example.com --app web-frontend --port 3000
```
