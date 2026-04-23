---
name: setup
description: "This skill should be used when verifying Dokploy MCP connection, CLI installation, and API access. Use when user says \"set up dokploy\", \"verify dokploy connection\", \"check dokploy\", \"test dokploy access\", or enables the dokploy-dev plugin for the first time."
---

# Dokploy Setup and Verification

Verify all three access methods to Dokploy: MCP tools, CLI, and REST API. Run each step in order. Report the result of each step before moving to the next.

---

## Prerequisites

The `dokploy-dev` plugin requires two configuration values set via `userConfig` in `plugin.json`:

| Config Key | Description | Example |
|---|---|---|
| `dokploy_url` | Dokploy server **base URL** (no `/api` suffix) | `https://dokploy.example.com` |
| `dokploy_api_key` | API authentication token | `dk_abc123...` |

These values are referenced as `$DOKPLOY_URL` and `$DOKPLOY_API_KEY` throughout the plugin. The MCP server and REST API are served from `/api/…` under the base URL.

Before running verification, confirm both values are configured. If either is missing, instruct the user to set them in their Claude Code plugin settings.

### Optional: reduce the exposed tool surface

The official `@dokploy/mcp` server exposes 500+ tools across 49 categories. If that is more than you need, set `DOKPLOY_ENABLED_TAGS` in the plugin's `.mcp.json` `env` block to a comma-separated list of categories (e.g. `project,application,domain,compose,postgres,settings,deployment,docker`). The server will then only expose tools from those categories.

### How to obtain an API key

1. Log in to the Dokploy dashboard.
2. Navigate to **Settings > API/Tokens**.
3. Click **Generate Token**.
4. Copy the token immediately — it is shown only once.

---

## Step 1: Verify MCP Connection

Call the MCP tool to list all projects:

```
mcp__dokploy__project-all
```

**No parameters required.**

### Expected result

A JSON array of project objects. Even an empty array `[]` confirms the MCP connection is working.

### If the call succeeds

Report: "MCP connection verified. Found N project(s)."

### If the call fails

Check these causes in order:

1. **MCP server not running** — The `.mcp.json` file must point to a running Dokploy MCP server. Verify the `command` and `args` fields are correct.
2. **Environment variables missing** — The MCP server needs `DOKPLOY_URL` and `DOKPLOY_API_KEY` passed via `env` in `.mcp.json`. Confirm they resolve to real values.
3. **npx resolution failure** — If the MCP server is launched via `npx`, ensure `@dokploy/mcp` is available. Run:
   ```bash
   npx @dokploy/mcp --version
   ```
4. **Network unreachable** — The MCP server connects to the Dokploy API. If the server is on a private network, verify the machine running Claude Code can reach it.

Report the specific error message from the MCP call to help diagnose.

---

## Step 2: Verify CLI Installation

Run the Dokploy CLI verification command:

```bash
dokploy verify
```

### If the command succeeds

Report: "Dokploy CLI is installed and authenticated."

### If `dokploy` is not found

Install the CLI globally:

```bash
npm install -g @dokploy/cli
```

Then authenticate with the server:

```bash
dokploy authenticate
```

When prompted, provide:
- **Server URL** — The Dokploy instance URL (e.g. `https://dokploy.example.com`). Do NOT include `/api` suffix for CLI auth.
- **API Key** — The same token used in `userConfig`.

After authentication, re-run:

```bash
dokploy verify
```

### If authentication fails

Check these causes:

1. **Wrong URL format** — The CLI expects the base URL without `/api`. If `dokploy_url` is `https://dokploy.example.com/api`, use `https://dokploy.example.com` for CLI auth.
2. **Expired token** — Generate a new token from the Dokploy dashboard.
3. **Self-signed certificate** — If the server uses a self-signed cert, set:
   ```bash
   export NODE_TLS_REJECT_UNAUTHORIZED=0
   ```
   Then retry. This is acceptable for local/dev environments only.

---

## Step 3: Verify API Access

Make a direct HTTP request to the health endpoint:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  "$DOKPLOY_URL/api/settings.health" \
  -H "x-api-key: $DOKPLOY_API_KEY"
```

Replace `$DOKPLOY_URL` (base URL, no `/api`) and `$DOKPLOY_API_KEY` with the actual configured values.

### Expected result

HTTP status code `200`.

### If 200 is returned

Report: "API access verified. Dokploy server is healthy."

### If a non-200 status is returned

| Status Code | Cause | Fix |
|---|---|---|
| `401` | Invalid or expired API key | Generate a new token in **Settings > API/Tokens**. Also verify you used the `x-api-key` header (NOT `Authorization: Bearer`) |
| `403` | Token lacks required permissions | Check token scope — it must have admin access |
| `404` | Wrong URL path | `dokploy_url` must be the base URL **without** `/api` (e.g. `https://dokploy.example.com`). Append `/api/<endpoint>` in curl calls |
| `000` or connection refused | Server unreachable | Check URL, DNS, firewall rules, and that Dokploy is running |
| `502` / `503` | Server is starting or overloaded | Wait 30 seconds and retry |

### Additional API verification (optional)

To confirm full read/write access, call a non-destructive endpoint:

```bash
curl -s "$DOKPLOY_URL/api/project.all" \
  -H "x-api-key: $DOKPLOY_API_KEY" \
  -H "Content-Type: application/json"
```

This should return the same project list as the MCP call in Step 1.

---

## Verification Summary

After completing all three steps, produce a summary table:

| Check | Status | Details |
|---|---|---|
| MCP Connection | PASS/FAIL | N projects found / error message |
| CLI Installation | PASS/FAIL | Version / not installed |
| API Access | PASS/FAIL | HTTP 200 / status code |

If all three pass, report: "Dokploy setup is complete. All access methods are working."

If any step fails, provide the specific fix instructions from the relevant section above.

---

## Common Issues

| Problem | Symptoms | Solution |
|---|---|---|
| MCP not connecting | Tool calls return "server not found" or timeout | Verify `.mcp.json` exists, `npx @dokploy/mcp` works, and env vars are set |
| CLI auth fails | `dokploy authenticate` returns 401 | Use base URL without `/api` suffix; regenerate token |
| API 401 Unauthorized | `curl` returns 401 | Token expired or invalid — regenerate in dashboard |
| API connection refused | `curl` returns 000 or "connection refused" | Wrong URL, server down, or firewall blocking the port |
| Self-signed cert errors | `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | Set `NODE_TLS_REJECT_UNAUTHORIZED=0` for dev environments |
| MCP tools exist but return errors | Tool calls return API errors | `dokploy_url` is the **base URL without `/api`** for MCP, REST, and CLI. MCP server and REST endpoints live at `/api/…` under that base |
| Wrong port | Connection refused on default port | Dokploy defaults to port 3000; verify the actual port in your deployment |

---

## What This Skill Does NOT Cover

- **Application deployment workflows** — See the `mcp-patterns` skill for MCP tool sequences to deploy apps, provision databases, and manage domains.
- **API endpoint details** — See the `api-reference` skill for the full list of 463 REST API endpoints with parameters and response schemas.
- **CLI command recipes** — See the `cli-recipes` skill for common CLI workflows like deploying from a local directory, managing Docker Compose stacks, and backup operations.
- **Troubleshooting deployment issues** — See the `troubleshoot` skill for diagnosing failed deployments, container crashes, and Traefik routing problems.
