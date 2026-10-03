# dokploy-dev

Dokploy self-hosted PaaS development plugin for Claude Code. Deploy applications, provision databases, manage domains, Docker Compose stacks, backups, server operations — **and debug failed deployments end-to-end** with AI-powered log analysis.

Uses the **official** `@dokploy/mcp` server (maintained by the Dokploy team). Aligned with Dokploy **v0.30.x** (OpenAPI verified on v0.30.7; upstream latest v0.30.8).

**Reads runtime logs of every container** — including each container in a Docker Compose stack — over the API/MCP (no SSH/Beszel), and diagnoses errors end-to-end.

## Interfaces

| Interface | Package | Tools/Endpoints | Logs/debug? |
|-----------|---------|-----------------|-------------|
| MCP Server | `@dokploy/mcp` | 604 tools across 57 categories (secret fields redacted by default) | ✅ runtime + build logs, AI analysis, docker introspection |
| REST API | — | 604 endpoints (OpenAPI v0.30.7) | ✅ `GET /api/*.readLogs` |
| CLI | `@dokploy/cli` | 604 auto-generated commands in 57 groups (`dokploy <group> <action>`), 1:1 with the API | ✅ `<group> read-logs` commands |

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Verify MCP connection, CLI installation, and API access |
| `mcp-patterns` | Core MCP tools by category with usage patterns, Docker networks, vault/DNS providers, and the redaction rules (filterable via `DOKPLOY_TOOL_PRESET` / `DOKPLOY_ENABLED_TAGS`) |
| `api-reference` | REST API endpoint reference: two exhaustive operation indexes (604 operations) plus 7 curated reference files (projects/apps, databases, domains, compose/docker, server/settings, ai-and-debugging, schedule-patch-previews) |
| `cli-recipes` | Auto-generated CLI (0.30.x): auth, command model, provisioning + read-logs recipes |
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

1. **Step 0** — platform health (`settings-checkInfrastructureHealth`, `getDockerDiskUsage`, and on v0.30+ `docker-getServerHealth` / `docker-getEvents` for inotify limits, disk, memory/CPU reservations, network IP-pool usage and daemon events)
2. **Step 1** — locate the failed run (`deployment-all`, save `deploymentId`)
3. **Step 2** — read the logs (all over MCP/REST/CLI): build → `deployment-readLogs { deploymentId, tail }`; app runtime → `application-readLogs { applicationId, tail, since, search }`; **Compose → every container** via `docker-getContainersByAppNameMatch` then `compose-readLogs { composeId, containerId }` per container (`/dokploy-dev:compose-logs`); db → `{type}-readLogs`
4. **Step 3** — inspect the container (`docker-getContainersByAppLabel { appName, type }`, `docker-getConfig` — its `Env` is `[REDACTED]` unless `DOKPLOY_REDACT_ENV=false`)
5. **Step 4** — check Traefik routing (`application-readTraefikConfig`)
6. **Step 5** — recover with the smallest safe action (`killBuild` / `cleanQueues` / `deployment-removeDeployment` / `rollback-rollback`)
7. **Step 6** — AI-summarise (`ai-analyzeLogs { aiId, logs, context }` if a provider is configured — see `ai-assist`)
8. **Step 7** — verify (`application-redeploy`, poll `deployment-all`, curl the endpoint)

`/dokploy-dev:analyze` is the one-shot AI wrapper; `/dokploy-dev:compose-logs` reads every container in a stack.

## Dokploy v0.30 coverage

v0.30 added features this plugin documents (tool tables in `mcp-patterns`, per-operation params in the `api-reference` indexes):

- **Docker networks** — `network-*` (create/inspect/remove/recreate/resync/import) and per-service attachment: `networkIds` + `detachDokployNetwork` on `application-update` and the six database `*-update` tools, `serviceNetworks` on `compose-update`. Replaces the now-deprecated Isolated Deployment (`compose-isolatedDeployment`).
- **Vault (secrets) providers** — `vaultProvider-*`; env values like `DB_PASSWORD=${{vault.<provider>.<ref>}}` are resolved at deploy time and never stored in Dokploy. Providers: HashiCorp Vault / OpenBao, Infisical, AWS Secrets Manager, AWS Parameter Store, Doppler, Azure Key Vault, Scaleway, Phase.
- **DNS providers** — `dnsProvider-*` (Cloudflare, Route 53, Porkbun, Infomaniak, OVHcloud): browse zones and manage records; `domain-toggleEnable` switches a domain off without deleting it.
- **Docker host diagnostics** — `docker-getServerHealth`, `docker-getEvents`, `dockerDiskUsage-*`, `dockerImage-*`, `dockerVolume-*`, `docker-listContainerFiles` / `docker-readContainerFile` (read-only parts are safe for `/dokploy-dev:debug`).
- **Overview and fresh volumes** — `overview-services` / `overview-backups` / `overview-domains`, `server-getServices`, and `freshVolumes` on `compose-deploy` / `compose-redeploy`.

Removed in v0.30: `settings-cleanRedis` / `settings-reloadRedis` were removed in v0.30.0 (Dokploy no longer uses Redis). `domain-validateDomain`: `serverIp` was replaced by `serverId` in v0.30. `settings-cleanAll` now runs in the background (it returns `{ status: "scheduled" }`) and does containers + `image prune --all` + builder + `system prune --all`, never volumes or monitoring data.

## Agent

- **dokploy-assistant** — Developer assistant for deploying apps, managing projects, provisioning databases, configuring domains, AND running the full debug workflow on failed deploys

## Prerequisites

- A running Dokploy instance
- Dokploy API key (generate in Dokploy dashboard under user settings)
- Recommended Dokploy server >= v0.30.0 (includes the v0.29.13 command-injection/IDOR security batch and the 20 fixes backported in its hotfix, the Route53 SSRF and compose `serviceName` command-injection fixes, and Traefik 3.6.25). The v0.30 features listed above (networks, vault/DNS providers, Docker host diagnostics) need a v0.30 server

## Configuration

The plugin reads two environment variables, used across all three interfaces:

| Variable | Description | Used by |
|----------|-------------|---------|
| `DOKPLOY_URL` | Dokploy server base URL **without** `/api` (e.g. `https://dokploy.example.com`). MCP/REST endpoints live at `/api/…` under it | MCP, REST API |
| `DOKPLOY_API_KEY` | Dokploy access token (Settings > API/Tokens) | MCP, REST API |

`.mcp.json` injects these into the `@dokploy/mcp` server via `${DOKPLOY_URL}` / `${DOKPLOY_API_KEY}` — set them in your Claude Code environment (e.g. the `env` block of `.claude/settings.local.json`, or your shell). The **CLI** reads the same `DOKPLOY_URL`/`DOKPLOY_API_KEY` env vars directly (or `dokploy auth -u <url> -t <token>` to persist them).

> **Secrets are redacted by default.** `@dokploy/mcp` ≥ 0.30.0 sets `DOKPLOY_REDACT_ENV=true`, so MCP responses show `[REDACTED]` instead of `env`, passwords and tokens — you can still *write* them (`application-saveEnvironment`), but not read them back. Direct REST/CLI calls are not redacted. Details and a names-only recipe: "Redaction" in the `mcp-patterns` skill.

> After changing either value, **restart Claude Code or reconnect the `dokploy` MCP server** (`/mcp` → reconnect) — a stdio MCP server reads its env once at startup. Symptoms of a stale process: "Invalid URL" (empty `DOKPLOY_URL`) or 401 (bad key).

### Optional env vars (set in `.mcp.json` `env` block)

| Variable | Purpose |
|----------|---------|
| `DOKPLOY_TOOL_PRESET` | Predefined toolset (`@dokploy/mcp` ≥ 0.30.0): `all` (default), `minimal` = project + application, `core` = project + server + application, `deploy` = project + environment + server + application + compose + domain + deployment, `databases` = postgres + redis + mysql + mariadb + mongo + libsql, `git` = github + gitlab + bitbucket + gitea + gitProvider + registry + sshKey. An unknown value falls back to `all` with a warning. The server logs a warning above 150 tools. **No preset includes `docker`, `ai`, `settings`, `rollback` or `schedule`** — for `/dokploy-dev:debug` use `DOKPLOY_ENABLED_TAGS` or add them back (see below) |
| `DOKPLOY_ENABLED_TAGS` | Comma-separated category filter (e.g. `project,application,domain,compose,postgres,deployment,docker,settings,ai,rollback,schedule`) to reduce the exposed tool surface from 604 down to what you actually need. **Takes priority over `DOKPLOY_TOOL_PRESET`.** Include `ai` and `docker` to keep the `/dokploy-dev:debug` workflow working |
| `DOKPLOY_DISABLED_TAGS` | Comma-separated categories to drop from the selected toolset (≥ 0.30.0). Applied **last**, after the preset or `DOKPLOY_ENABLED_TAGS` — e.g. `DOKPLOY_TOOL_PRESET=deploy` + `DOKPLOY_DISABLED_TAGS=domain` |
| `DOKPLOY_CUSTOM_HEADERS` | JSON object of extra headers sent to the upstream Dokploy API (string values only; `x-api-key`, `content-type` and `accept` are reserved and rejected) |
| `DOKPLOY_REDACT_ENV` | **Default `true`** in `@dokploy/mcp` ≥ 0.30.0 (it was `false` before 0.30): every response field whose name ends in `env`, `buildArgs`, `composeFile`, `password`, `token`, `apiKey`, `secret`, `privateKey`, … comes back as `[REDACTED]`. That includes the `env` of `application-one` / `compose-one` / `{db}-one`, the `Env` of `docker-getConfig`, and 27 whole operations in `settings-getOpenApiDocument`. Set `DOKPLOY_REDACT_ENV=false` only when you knowingly want raw values in the model context. See "Redaction" in the `mcp-patterns` skill |
| `DOKPLOY_REDACT_FIELDS` | Comma-separated response field names to redact when `DOKPLOY_REDACT_ENV=true`; **replaces** the built-in default list (not additive). Matched case-insensitively as a key **suffix** at any nesting depth |
| `MCP_TRANSPORT` | `stdio` (default); `http` for Streamable HTTP (+ legacy SSE) |
| `DOKPLOY_TIMEOUT` | Per-request timeout in ms (default `30000`) |
| `DOKPLOY_RETRY_ATTEMPTS` | Retry count on transient failure (default `3`) |
| `DOKPLOY_RETRY_DELAY` | Retry backoff in ms (default `1000`) |

## Optional: CLI

```bash
npm install -g @dokploy/cli
dokploy auth -u https://dokploy.example.com -t <API_KEY>   # or just export DOKPLOY_URL / DOKPLOY_API_KEY
```
