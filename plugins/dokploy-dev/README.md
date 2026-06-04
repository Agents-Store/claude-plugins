# dokploy-dev

Dokploy self-hosted PaaS development plugin for Claude Code. Deploy applications, provision databases, manage domains, Docker Compose stacks, backups, server operations — **and debug failed deployments end-to-end** with AI-powered log analysis.

Uses the **official** `@dokploy/mcp` server (maintained by the Dokploy team). Aligned with Dokploy **v0.29.5**.

**Reads runtime logs of every container** — including each container in a Docker Compose stack — over the API/MCP (no SSH/Beszel), and diagnoses errors end-to-end.

## Interfaces

| Interface | Package | Tools/Endpoints | Logs/debug? |
|-----------|---------|-----------------|-------------|
| MCP Server | `@dokploy/mcp` | 500+ tools across 49 categories | ✅ runtime + build logs, AI analysis, docker introspection |
| REST API | — | 500+ endpoints (OpenAPI v0.29.5) | ✅ `GET /api/*.readLogs` |
| CLI | `@dokploy/cli` | provisioning/deploy commands (project, app, database, env, auth) | ❌ no log/debug command — use MCP/API |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify MCP connection, CLI installation, and API access |
| `mcp-patterns` | Core MCP tools by category with usage patterns (filterable via `DOKPLOY_ENABLED_TAGS`) |
| `api-reference` | REST API endpoint reference across 7 reference files (projects/apps, databases, domains, compose/docker, server/settings, ai-and-debugging, schedule-patch-previews) |
| `cli-recipes` | CLI commands and workflow recipes |
| `read-logs` | Read runtime + build logs of any resource — app, **every container in a Compose stack**, database, or deployment — with `tail`/`since`/`search` and AI-triage handoff |
| `debug-deploy` | End-to-end failed-deployment decision tree — failed-run lookup → build/runtime logs → container/Traefik inspection → AI summary → recovery |
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
| `/dokploy-dev:logs` | Read runtime/build logs for any resource (app / db / deployment) with `tail`/`since`/`search` |
| `/dokploy-dev:compose-logs` | **Read EVERY container's logs in a Compose stack** and highlight errors per container |
| `/dokploy-dev:analyze` | AI-summarise a failure (fetches the log text, then `ai-analyzeLogs`) via the configured `ai-*` provider |
| `/dokploy-dev:rollback` | Roll an application or compose stack back to a previous version |
| `/dokploy-dev:cleanup` | Guided disk-space cleanup chain with per-step confirmation |

## Debugging Workflow

When a deploy fails, the canonical path is:

```
/dokploy-dev:debug [resource]
```

The command runs through `debug-deploy/SKILL.md`:

1. **Step 0** — platform health (`settings-checkInfrastructureHealth`, `getDockerDiskUsage`)
2. **Step 1** — locate the failed run (`deployment-all`, save `deploymentId`)
3. **Step 2** — read the logs (v0.29.5, all over MCP/REST): build → `deployment-readLogs { deploymentId, tail }`; app runtime → `application-readLogs { applicationId, tail, since, search }`; **Compose → every container** via `docker-getContainersByAppNameMatch` then `compose-readLogs { composeId, containerId }` per container (`/dokploy-dev:compose-logs`); db → `{type}-readLogs`
4. **Step 3** — inspect the container (`docker-getContainersByAppLabel { appName, type }`, `docker-getConfig`)
5. **Step 4** — check Traefik routing (`application-readTraefikConfig`)
6. **Step 5** — recover with the smallest safe action (`killBuild` / `cleanQueues` / `dropDeployment` / `rollback-rollback`)
7. **Step 6** — AI-summarise (`ai-analyzeLogs { aiId, logs, context }` if a provider is configured — see `ai-assist`)
8. **Step 7** — verify (`application-redeploy`, poll `deployment-all`, curl the endpoint)

`/dokploy-dev:analyze` is the one-shot AI wrapper; `/dokploy-dev:compose-logs` reads every container in a stack.

## Agent

- **dokploy-assistant** — Developer assistant for deploying apps, managing projects, provisioning databases, configuring domains, AND running the full debug workflow on failed deploys

## Prerequisites

- A running Dokploy instance
- Dokploy API key (generate in Dokploy dashboard under user settings)

## Configuration

The plugin reads two environment variables, used across all three interfaces:

| Variable | Description | Used by |
|----------|-------------|---------|
| `DOKPLOY_URL` | Dokploy server base URL **without** `/api` (e.g. `https://dokploy.example.com`). MCP/REST endpoints live at `/api/…` under it | MCP, REST API |
| `DOKPLOY_API_KEY` | Dokploy access token (Settings > API/Tokens) | MCP, REST API |

`.mcp.json` injects these into the `@dokploy/mcp` server via `${DOKPLOY_URL}` / `${DOKPLOY_API_KEY}` — set them in your Claude Code environment (e.g. the `env` block of `.claude/settings.local.json`, or your shell). The **CLI** uses the same access token via `dokploy authenticate` (stored in its own `config.json`).

> After changing either value, **restart Claude Code or reconnect the `dokploy` MCP server** (`/mcp` → reconnect) — a stdio MCP server reads its env once at startup. Symptoms of a stale process: "Invalid URL" (empty `DOKPLOY_URL`) or 401 (bad key).

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
