# dokploy-dev

Dokploy self-hosted PaaS development plugin for Claude Code. Deploy applications, provision databases, manage domains, Docker Compose stacks, backups, server operations — **and debug failed deployments end-to-end** with AI-powered log analysis.

Uses the **official** `@dokploy/mcp` server (maintained by the Dokploy team). Aligned with Dokploy **v0.29.x**.

## Interfaces

| Interface | Package | Tools/Endpoints |
|-----------|---------|-----------------|
| MCP Server | `@dokploy/mcp` | 500+ tools across 49 categories |
| REST API | — | 500+ endpoints |
| CLI | `@dokploy/cli` | 40+ commands |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify MCP connection, CLI installation, and API access |
| `mcp-patterns` | Core MCP tools by category with usage patterns (filterable via `DOKPLOY_ENABLED_TAGS`) |
| `api-reference` | REST API endpoint reference across 7 reference files (projects/apps, databases, domains, compose/docker, server/settings, ai-and-debugging, schedule-patch-previews) |
| `cli-recipes` | CLI commands and workflow recipes |
| `debug-deploy` | End-to-end failed-deployment decision tree — failed-run lookup → build log → container/Traefik inspection → AI summary → recovery |
| `ai-assist` | Configure AI providers and call `ai-analyzeLogs` / `ai-suggest` for log analysis and recommendations |
| `troubleshoot` | Symptom-to-cause reference table (domain, database, Docker, Traefik, MCP issues) |
| `examples` | End-to-end deployment AND debug scenarios with concrete tool chains |

## Commands

| Command | Description |
|---------|-------------|
| `/dokploy-dev:list-projects` | List all projects |
| `/dokploy-dev:list-apps` | List applications in a project |
| `/dokploy-dev:create-project` | Create a new project |
| `/dokploy-dev:create-app` | Create an application in a project |
| `/dokploy-dev:create-db` | Create a managed database (Postgres, MySQL, MariaDB, Mongo, Redis, LibSQL) |
| `/dokploy-dev:add-domain` | Attach a domain (with HTTPS) to an application or compose stack |
| `/dokploy-dev:deploy` | Deploy or redeploy an application or compose stack (detects compose-mode mismatch) |
| `/dokploy-dev:status` | Check current state and recent deployments |
| `/dokploy-dev:debug` | **Full failed-deploy decision tree** — locate, log, container, Traefik, AI, recover |
| `/dokploy-dev:logs` | Read logs for any resource (app / compose / db / deployment) with build-log fallback |
| `/dokploy-dev:analyze` | AI-summarise a failed deployment via the configured `ai-*` provider |
| `/dokploy-dev:rollback` | Roll an application or compose stack back to a previous version |
| `/dokploy-dev:cleanup` | Guided disk-space cleanup chain with per-step confirmation |

## Debugging Workflow

When a deploy fails, the canonical path is:

```
/dokploy-dev:debug [resource]
```

The command runs through `debug-deploy/SKILL.md`:

1. **Step 0** — platform health (`settings-checkInfrastructureHealth`, `getDockerDiskUsage`)
2. **Step 1** — locate the failed run (`deployment-all`, save `deploymentId` + `logPath`)
3. **Step 2** — read the build log (`application-readLogs` for metadata; Beszel/SSH for content — Dokploy doesn't yet expose runtime stdout via REST, see [issue #3719](https://github.com/Dokploy/dokploy/issues/3719))
4. **Step 3** — inspect the container (`docker-getContainersByAppLabel`, `docker-getConfig`)
5. **Step 4** — check Traefik routing (`application-readTraefikConfig`)
6. **Step 5** — recover with the smallest safe action (`killBuild` / `cleanQueues` / `dropDeployment` / `rollback-rollback`)
7. **Step 6** — AI-summarise (`ai-analyzeLogs` if a provider is configured — see `ai-assist`)
8. **Step 7** — verify (`application-redeploy`, poll `deployment-all`, curl the endpoint)

`/dokploy-dev:analyze` is the one-shot wrapper around step 6.

## Agent

- **dokploy-assistant** — Developer assistant for deploying apps, managing projects, provisioning databases, configuring domains, AND running the full debug workflow on failed deploys

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
| `DOKPLOY_ENABLED_TAGS` | Comma-separated category filter (e.g. `project,application,domain,compose,postgres,deployment,docker,settings,ai,rollback,schedule`) to reduce the exposed tool surface from 500+ down to what you actually need. Include `ai` and `docker` to keep the `/dokploy-dev:debug` workflow working |
| `DOKPLOY_TIMEOUT` | Per-request timeout in ms (default `30000`) |
| `DOKPLOY_RETRY_ATTEMPTS` | Retry count on transient failure (default `3`) |
| `DOKPLOY_RETRY_DELAY` | Retry backoff in ms (default `1000`) |

## Optional: CLI

```bash
npm install -g @dokploy/cli
dokploy authenticate
```
