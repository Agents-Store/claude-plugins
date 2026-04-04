# dokploy-dev

Dokploy self-hosted PaaS development plugin for Claude Code. Deploy applications, provision databases, manage domains, Docker Compose stacks, backups, and server operations.

## Interfaces

| Interface | Package | Tools/Endpoints |
|-----------|---------|-----------------|
| MCP Server | `@ahdev/dokploy-mcp` | 67 tools |
| REST API | — | 463 endpoints |
| CLI | `@dokploy/cli` | 40+ commands |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify MCP connection, CLI installation, and API access |
| `mcp-patterns` | All 67 MCP tools organized by category with usage patterns |
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

- **dokploy_url** — Your Dokploy server API URL (e.g., `https://dokploy.example.com/api`)
- **dokploy_api_key** — Your Dokploy API authentication token

## Optional: CLI

```bash
npm install -g @dokploy/cli
dokploy authenticate
```
