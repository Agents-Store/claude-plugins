---
name: setup
description: |
  Verify NocoBase API connectivity and authentication. Use when:
  - "check my NocoBase connection"
  - "verify NocoBase API access"
  - "test NocoBase setup"
  - "is NocoBase API reachable?"
  - "troubleshoot NocoBase authentication"
---

# NocoBase Setup Verification

Verify NocoBase connectivity across MCP, CLI, and HTTP transports before running any operations.

## MCP smoke test (preferred)

```
# 1. Check auth works
auth_check()

# 2. Read schema
collections_list_meta()

# 3. Confirm ACL action registry (trivial tool, verifies full stack)
available_actions_list()
```

All three should return `{ data: [...] }` with no error. If any fail, see `troubleshoot`.

Before first MCP call in a fresh session: bulk-load schemas with `ToolSearch(query: "nc-mcp", max_results: 30)`.

## CLI smoke test

```bash
nocobase-ctl --version
nocobase-ctl auth check
nocobase-ctl data-modeling collections list --page-size 1 -j
```

## HTTP smoke test (universal fallback)

See steps below. Works even if MCP and CLI are unavailable.

## Additional install/upgrade/diagnose references

Upstream env-bootstrap content merged under `references/env-bootstrap/`:

- `references/env-bootstrap/install-runbook.md` — Docker/create-nocobase-app/git install paths
- `references/env-bootstrap/upgrade-runbook.md` — version bumping procedures
- `references/env-bootstrap/mcp-runbook.md` — MCP client setup (including claude.ai OAuth)
- `references/env-bootstrap/mcp-client-templates.md` — MCP client config templates
- `references/env-bootstrap/mcp-call-examples.md` — example MCP tool calls
- `references/env-bootstrap/mcp-tool-shapes.md` — canonical parameter shapes
- `references/env-bootstrap/mcp-troubleshooting.md` — MCP-specific error diagnosis
- `references/env-bootstrap/preflight-checklist.md` — pre-install environment checks
- `references/env-bootstrap/troubleshooting.md` — general troubleshooting matrix
- `references/env-bootstrap/usage-guide.md` — daily operations
- `references/env-bootstrap/app-env-manage.md` — multi-env app management

## Prerequisites

Before running verification, confirm:

1. **NocoBase instance is running** -- a V2 instance accessible over HTTP/HTTPS.
2. **API key is generated** -- create one in the NocoBase admin panel under Settings > API keys (for HTTP path).
3. **MCP is connected** (optional but recommended) -- `nc-mcp` available under `*`.
4. **Environment variables are set** in the user's project or shell (for HTTP fallback).

## Environment Variables

Set these in the project's `.env`, shell profile, or pass them inline:

| Variable | Required | Description |
|----------|----------|-------------|
| `NOCOBASE_URL` | Yes | Base URL of the NocoBase instance (e.g., `https://nocobase.example.com`) |
| `NOCOBASE_API_KEY` | Yes | API key for Bearer token authentication |

The plugin references these as `${NOCOBASE_URL}` and `${NOCOBASE_API_KEY}` in all curl examples.

## Verification Steps

Run these checks in order. Stop at the first failure and consult the troubleshooting table.

### Step 1 -- Check API Connectivity

Confirm the NocoBase server is reachable and responds to unauthenticated requests.

```bash
curl -s "${NOCOBASE_URL}/api/app:getInfo"
```

**Pass:** Returns JSON with application metadata (version, name, lang).

```json
{
  "data": {
    "version": "2.0.0",
    "lang": "en-US",
    "name": "nocobase"
  }
}
```

**Fail:** Connection refused, timeout, or non-JSON response. The instance is not running or the URL is wrong.

### Step 2 -- Test Authentication

Verify the API key is valid and the authenticated user is recognized.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/auth:check"
```

**Pass:** Returns the authenticated user object with `id`, `nickname`, and `roles`.

```json
{
  "data": {
    "id": 1,
    "nickname": "Admin",
    "roles": [{ "name": "admin", "title": "Admin" }]
  }
}
```

**Fail:** 401 Unauthorized means the API key is invalid, expired, or missing. 403 Forbidden means the key exists but lacks the required role.

### Step 3 -- Verify Read Access

Confirm the authenticated user can read collection metadata.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?page=1&pageSize=5"
```

**Pass:** Returns a paginated list of collections with `data` array and `meta` object.

```json
{
  "data": [
    { "name": "users", "title": "Users", "fields": [...] }
  ],
  "meta": { "count": 12, "page": 1, "pageSize": 5, "totalPage": 3 }
}
```

**Fail:** 403 means the API key's role does not have permission to list collections. Check role assignments in the admin panel.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Connection refused | Instance not running or wrong URL | Verify the URL in a browser; check that the NocoBase service is up |
| 401 Unauthorized | Invalid or expired API key | Regenerate the key in Admin Panel > Settings > API keys |
| 403 Forbidden | API key role lacks permission | Assign the correct role to the API key user; check role permissions |
| Timeout (no response) | Network issue, firewall, or DNS | Check network connectivity; verify DNS resolves correctly |
| 404 Not Found | Wrong base path or old API version | Confirm `/api/` is the correct prefix; check NocoBase version |
| 502 Bad Gateway | Reverse proxy misconfiguration | Check Nginx/Caddy config; verify upstream points to NocoBase port |
| SSL certificate error | Self-signed or expired cert | Use `-k` flag for testing, or fix the certificate |
| Empty collections list | No collections created yet | Create collections through the NocoBase UI first |

## What This Skill Does NOT Cover

- **Installing NocoBase** -- refer to the official NocoBase deployment docs for Docker, source, or cloud setup.
- **Creating API keys** -- generate keys through the NocoBase admin panel under Settings > API keys.
- **Role and permission configuration** -- configure roles in Admin Panel > Roles & Permissions.
- **Plugin management** -- enable/disable NocoBase plugins through the plugin manager UI.

## After Verification

Once all three steps pass, proceed to:

- Learn the API URL patterns and query parameters with the **api-patterns** skill.
- Manage collections and fields with the **collections-and-fields** skill.
- Create, read, update, and delete records with the **record-operations** skill.

## See also

- `mcp-patterns` — MCP transport conventions
- `api-patterns` — HTTP URL pattern and filter syntax
- `troubleshoot` — diagnosing connection, auth, and permission errors
