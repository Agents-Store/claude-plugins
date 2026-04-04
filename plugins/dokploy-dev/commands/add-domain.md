---
description: Add a custom domain to a Dokploy application
argument-hint: <domain> --app <app-name-or-id> [--port <port>] [--https]
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

2. **Create domain** using MCP tool `domain-create` with:
   - `host`: the domain name
   - `applicationId`: resolved application ID
   - `port`: specified port or 3000
   - `path`: `/`
   - `https`: true if --https flag provided

3. **Validate domain** using MCP tool `domain-validateDomain` to check DNS resolution.

4. **Display result:**
   Show domain, port, HTTPS status, and validation result. If DNS not resolving, remind user to add an A record pointing to the server IP.

## Example Usage
```
/dokploy-dev:add-domain app.example.com --app web-frontend --https
/dokploy-dev:add-domain api.example.com --app api-server --port 8000 --https
/dokploy-dev:add-domain staging.example.com --app web-frontend --port 3000
```
