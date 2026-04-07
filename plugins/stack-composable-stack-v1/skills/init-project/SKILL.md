---
name: init-project
description: This skill should be used when the user asks to "set up composable stack", "initialize project", "configure environment", "connect MCP services", or needs to set up all MCP connections and environment variables for the Composable Stack v1.
---

# Initialize Composable Stack v1

Set up environment variables, verify all MCP connections, and create project configuration for the Composable Stack.

## Architecture Overview

| Layer | Service | MCP Server | Transport |
|-------|---------|------------|-----------|
| Data | PostgreSQL + NocoDB | `nocodb` | HTTP |
| Logic | n8n | `n8n-mcp-external` + `n8n-native-mcp` | stdio + HTTP |
| Logic | Trigger.dev | `trigger-dev` | stdio |
| Interface | NocoBase + NocoDB | — (via NocoBase API + NocoDB MCP) | — |

## Step 1: Environment Variables

### Using Infisical (recommended)

Pull all secrets from Infisical in one command:

```bash
./scripts/setup.sh dev .env .claude/settings.local.json
```

This writes `.env` and injects variables into `.claude/settings.local.json` for MCP resolution.

### Manual Setup

Copy the template and fill in values:

```bash
cp templates/.env.example .env
```

Required variables:

| Variable | Service | Description |
|----------|---------|-------------|
| `TRIGGER_SECRET_KEY` | Trigger.dev | Dev environment secret key (`tr_dev_xxx`) |
| `TRIGGER_API_URL` | Trigger.dev | Self-hosted instance URL |
| `N8N_API_URL` | n8n | Instance base URL |
| `N8N_API_KEY` | n8n | API authentication key |
| `N8N_NATIVE_MCP_URL` | n8n | Full native MCP URL (`{N8N_API_URL}/mcp-server/http`) |
| `N8N_MCP_TOKEN` | n8n | Native MCP bearer token |
| `NOCODB_MCP_URL` | NocoDB | MCP server URL (full URL with `/mcp` path) |
| `NOCODB_TOKEN` | NocoDB | MCP authentication token |
| `NOCOBASE_URL` | NocoBase | Instance URL |
| `NOCOBASE_API_KEY` | NocoBase | API key for NocoBase operations |

## Step 2: Verify MCP Connections

Test each service connection in order.

### 2a. NocoDB (Data layer)

```
Tool: mcp__nocodb__getTablesList
```

Expected: returns a list of tables from the connected NocoDB base.

### 2b. n8n External MCP (Logic layer)

```
Tool: mcp__n8n-mcp-external__searchNodes
Input: { "query": "webhook" }
```

Expected: returns matching n8n node types.

### 2c. n8n Native MCP (Logic layer)

```
Tool: mcp__n8n-native-mcp__listWorkflows
```

Expected: returns workflows from the n8n instance.

### 2d. Trigger.dev (Logic layer)

```
Tool: mcp__trigger-dev__list_runs
```

Expected: returns recent task runs.

### 2e. NocoBase (Interface layer)

NocoBase uses its own MCP from the `nocobase-dev` technology plugin. Verify with:

```
Tool: mcp__nocobase__listCollections
```

Expected: returns NocoBase collections.

## Step 3: Create CLAUDE.md

Copy the template:

```bash
cp templates/CLAUDE.md.template CLAUDE.md
```

Replace `{{PROJECT_NAME}}` with your project name.

## Step 4: Verify Installed Plugins

Confirm all technology plugins are enabled in `.claude/settings.json`:

- `trigger-dev@agents-store-claude-plugins`
- `n8n-dev@agents-store-claude-plugins`
- `nocodb-ops@agents-store-claude-plugins`
- `nocobase-dev@agents-store-claude-plugins`
- `postgresql-external-dev@agents-store-claude-plugins`
- `n8n-provision@agents-store-claude-plugins`

These provide tool-specific knowledge. The stack plugin provides integration patterns between services.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| MCP connection refused | Service not running or wrong URL | Verify URL in `.env`, check service health |
| 401 on NocoDB | Invalid token | Regenerate token in NocoDB settings |
| 401 on n8n | Expired API key | Create new API key in n8n settings |
| Trigger.dev timeout | Wrong `TRIGGER_API_URL` | Verify the self-hosted instance URL |
| n8n native MCP 403 | Wrong MCP token | Generate new MCP token in n8n → Settings → API |
