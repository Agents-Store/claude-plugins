# dokploy-dev

Dokploy self-hosted PaaS development plugin for Claude Code. Deploy applications, provision databases, manage domains, Docker Compose stacks, backups, and server operations.

Uses the **official** `@dokploy/mcp` server (maintained by the Dokploy team).

## Interfaces

| Interface | Package | Tools/Endpoints |
|-----------|---------|-----------------|
| MCP Server | `@dokploy/mcp` | 500+ tools across 49 categories |
| REST API | — | 463 endpoints |
| CLI | `@dokploy/cli` | 40+ commands |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify MCP connection, CLI installation, and API access |
| `mcp-patterns` | Core MCP tools by category with usage patterns (filterable via `DOKPLOY_ENABLED_TAGS`) |
| `api-reference` | REST API endpoint reference (463 endpoints across 30+ tags) |
| `cli-recipes` | CLI commands and workflow recipes |
| `troubleshoot` | Diagnose deployment failures, domain issues, database problems |
| `examples` | End-to-end deployment scenarios and walkthroughs |

## Agent

- **dokploy-assistant** — Developer assistant for deploying apps, managing projects, provisioning databases, and configuring domains

## Prerequisites

- A running Dokploy instance
- Dokploy API key (generate in Dokploy dashboard under user settings)

## Configuration

When enabling this plugin, you will be prompted for:

- **dokploy_url** — Your Dokploy server base URL **without** `/api` (e.g., `https://dokploy.example.com`). The MCP server and REST API are served from `/api/…` under this URL.
- **dokploy_api_key** — Your Dokploy API authentication token

### Optional env vars (set in `.mcp.json` `env` block)

| Variable | Purpose |
|----------|---------|
| `DOKPLOY_ENABLED_TAGS` | Comma-separated category filter (e.g. `project,application,domain,compose,postgres`) to reduce the exposed tool surface from 500+ down to what you actually need |
| `DOKPLOY_TIMEOUT` | Per-request timeout in ms (default `30000`) |
| `DOKPLOY_RETRY_ATTEMPTS` | Retry count on transient failure (default `3`) |
| `DOKPLOY_RETRY_DELAY` | Retry backoff in ms (default `1000`) |

## Optional: CLI

```bash
npm install -g @dokploy/cli
dokploy authenticate
```
