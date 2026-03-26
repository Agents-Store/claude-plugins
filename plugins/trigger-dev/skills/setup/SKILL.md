---
name: setup
description: This skill should be used when the user asks to "verify trigger.dev connection", "check trigger.dev MCP", "test trigger.dev setup", "is trigger.dev working", "trigger.dev self-hosted setup", "install trigger.dev MCP server", or needs to confirm that the Trigger.dev MCP integration is operational.
---

# Trigger.dev Setup Verification

Verify that the Trigger.dev MCP connection is working and the self-hosted v4 instance is accessible.

## Prerequisites

- Trigger.dev v4 self-hosted instance running (webapp + supervisor)
- Valid `TRIGGER_SECRET_KEY` with appropriate permissions
- MCP server configured (official or via Stack Plugin)

## Installing the Official MCP Server

Trigger.dev provides an **official MCP server** shipped with the CLI. Install it:

```bash
npx trigger.dev@latest mcp
```

This launches an interactive wizard to choose your AI coding tool (Cursor, Claude Code, VSCode Copilot, Windsurf, etc.) and configure the installation scope.

### MCP Server Configuration (manual)

```json
{
  "mcpServers": {
    "trigger": {
      "command": "npx",
      "args": ["trigger.dev@latest", "mcp"]
    }
  }
}
```

### Dev-Only Mode (security)

Prevents MCP from accessing production data:

```json
{
  "mcpServers": {
    "trigger": {
      "command": "npx",
      "args": ["trigger.dev@latest", "mcp", "--dev-only"]
    }
  }
}
```

### Installing Agent Rules

Install code-generation rules for your AI assistant:

```bash
npx trigger.dev@latest install-rules
```

Rules are available for Cursor, Claude Code, VSCode Copilot, Windsurf, Cline, Gemini CLI, and more. Rules auto-update when you run `npx trigger.dev@latest dev`.

For Claude Code, a `trigger-dev-expert` subagent is also available.

## Verification Steps

### 1. Check MCP Connection

```
Tool: tds-list_orgs
Input: {}
```

**Expected:** Returns a list of organizations with slug and ID.

### 2. Verify Project Access

```
Tool: tds-list_projects
Input: {}
```

**Expected:** Returns your projects with `projectRef` (proj_xxx).

### 3. Check Worker Status

```
Tool: tds-get_current_worker
Input: {"environment": "dev"}
```

**Expected:** Returns worker version and list of deployed tasks with payload schemas.

### 4. Verify Documentation Access

```
Tool: tds-search_docs
Input: {"query": "getting started"}
```

**Expected:** Returns relevant documentation pages.

## Self-Hosted v4 Instance Checks

### v4 Architecture Overview

Trigger.dev v4 self-hosted has two main components:

- **Webapp** — Dashboard, API, database (PostgreSQL), Redis, container registry, object storage (MinIO)
- **Worker (Supervisor)** — Manages task execution containers. Can run on same or separate machine.

The v3 coordinator+provider are replaced by a single **supervisor**. Docker Socket Proxy is used instead of direct socket access.

### Verify Instance Health

```bash
# Check all webapp services
cd trigger.dev/hosting/docker/webapp
docker compose ps

# Check webapp logs
docker compose logs -f webapp

# Check supervisor/worker
cd trigger.dev/hosting/docker/worker
docker compose ps
docker compose logs -f supervisor
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TRIGGER_API_URL` | Self-hosted instance URL | `https://trigger.example.com` |
| `TRIGGER_SECRET_KEY` | Per-environment secret key | `tr_dev_xxx` or `tr_prod_xxx` |
| `TRIGGER_ACCESS_TOKEN` | Personal access token (CI/CD) | `tr_pat_xxx` |
| `TRIGGER_PREVIEW_BRANCH` | Preview branch name (optional) | `feature/my-task` |

### Worker Token (v4)

When running webapp and worker on separate machines, a worker token is required:

```bash
# Token is printed on first webapp start:
# TRIGGER_WORKER_TOKEN=tr_wgt_xxxxx

# Set in worker's .env file
TRIGGER_WORKER_TOKEN=tr_wgt_xxxxx
```

### CLI Login for Self-Hosted

```bash
# Login with API URL
npx trigger.dev@latest login -a https://trigger.example.com

# Login with named profile
npx trigger.dev@latest login -a https://trigger.example.com --profile self-hosted

# Switch profiles
npx trigger.dev@latest switch

# List profiles
npx trigger.dev@latest list-profiles

# Verify
npx trigger.dev@latest whoami
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection refused | Instance not running | `docker compose up -d` in webapp/ and worker/ |
| 401 Unauthorized | Invalid secret key | Check `TRIGGER_SECRET_KEY` format (tr_dev_xxx or tr_prod_xxx) |
| No projects found | Wrong org or no projects | Create a project via UI or MCP |
| No tasks in worker | Tasks not deployed or dev server not running | Run `npx trigger.dev@latest dev` |
| MCP timeout | Instance unreachable | Check network, DNS, firewall |
| SSL error | Invalid certificate | Check reverse proxy SSL config |
| Deploy fails at push | No registry access | Login to built-in registry: `docker login -u <user> <registry-url>` |
| Redirected to cloud | Missing `-a` flag | Use `login -a <your-url>` or set `TRIGGER_API_URL` |

## What This Skill Does NOT Cover

- Installing the self-hosted instance (see trigger.dev/docs/self-hosting/docker)
- Kubernetes deployment (see trigger.dev/docs/self-hosting/kubernetes)
- Creating API keys (see Trigger.dev dashboard → Settings → API Keys)
