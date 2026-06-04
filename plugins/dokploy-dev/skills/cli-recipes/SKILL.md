---
name: cli-recipes
description: "This skill should be used when running Dokploy operations from the terminal with the @dokploy/cli — authenticating, creating projects/apps, deploying, managing environment variables, or provisioning databases via command line. Triggers: \"dokploy cli\", \"dokploy command\", \"dokploy authenticate\", \"dokploy app deploy\", \"env push\", \"env pull\", \"deploy dokploy from terminal\"."
---

# Dokploy CLI Recipes

Common commands and workflows for the official Dokploy CLI (`@dokploy/cli`). Use these when operating Dokploy from a terminal or CI, alongside the MCP tools.

> **Syntax note (v0.29+):** the CLI uses **space-separated** subcommands — `dokploy app create`, `dokploy database postgresql create` — NOT colon-separated (`app:create`). Run `dokploy --help` to see the command groups and `dokploy <group> --help` for the exact subcommands and flags in your installed version.

> **The CLI does NOT read logs or debug.** Its command groups are authentication, project, app, database, and environment — all provisioning/deploy actions. There is **no `dokploy logs` / `debug` / `status` command.** For reading logs and diagnosing failures use the MCP/API path instead: `/dokploy-dev:logs`, `/dokploy-dev:compose-logs`, `/dokploy-dev:debug`, or the `read-logs` skill.

---

## Installation

```bash
npm install -g @dokploy/cli
dokploy --version
```

---

## Authentication

```bash
dokploy authenticate     # interactive: prompts for server URL + access token
dokploy verify           # confirm the saved token is valid
```

- **Server URL** — the Dokploy base URL, e.g. `https://dokploy.example.com` (do NOT include `/api`).
- **Access token** — generate in the dashboard under **Settings > Profile** (or **Settings > API/Tokens**); tokens don't expire by default.
- `authenticate` writes a local **`config.json`** holding the token + server URL — that's what subsequent commands use.

**Relationship to the plugin env vars:** the MCP server, REST `curl` calls, and this plugin use the `DOKPLOY_URL` + `DOKPLOY_API_KEY` environment variables. The CLI uses its own `config.json` from `dokploy authenticate`. The **same access token** works for all three — set it once in each place.

---

## Project Commands

| Command | Description |
|---------|-------------|
| `dokploy project list` | List all projects |
| `dokploy project info` | Show details for a project |
| `dokploy project create` | Create a new project |

## Application Commands

| Command | Description |
|---------|-------------|
| `dokploy app create` | Create a new application in a project |
| `dokploy app deploy` | Trigger a deployment |
| `dokploy app stop` | Stop a running application |
| `dokploy app delete` | Delete an application |

## Environment Variable Commands

| Command | Description |
|---------|-------------|
| `dokploy env pull <file>` | Pull env vars from Dokploy into a local file |
| `dokploy env push <file>` | Push env vars from a local file to Dokploy |

(Run `dokploy env --help` / `dokploy environment --help` for the exact form in your version.)

### Env push/pull workflow

```bash
dokploy env pull .env.dokploy   # download current env
# edit .env.dokploy locally
dokploy env push .env.dokploy   # upload — avoids dashboard typos
```

## Database Commands

Pattern: `dokploy database <type> <action>`.

```bash
dokploy database postgresql create
dokploy database postgresql deploy
```

| Part | Values |
|------|--------|
| `<type>` | `postgresql`, `mysql`, `mariadb`, `mongo`, `redis` (run `dokploy database --help` for exact tokens) |
| `<action>` | `create`, `delete`, `deploy`, `stop` |

> **LibSQL is not available in the CLI** (only 5 DB types here). Provision LibSQL via MCP (`mcp__dokploy__libsql-create` → `libsql-deploy`) or the REST API.

---

## Workflow Recipes

### Deploy an app

```bash
dokploy authenticate          # one-time
dokploy project create
dokploy app create
dokploy env push .env
dokploy app deploy
```

### Provision a PostgreSQL database

```bash
dokploy project create        # or reuse an existing project
dokploy database postgresql create
dokploy database postgresql deploy
```

### Full-stack (app + database)

```bash
dokploy project create
dokploy database postgresql create && dokploy database postgresql deploy
dokploy app create
dokploy env push .env         # include the DB connection string
dokploy app deploy
```

After `dokploy app deploy`, the CLI can't show logs — switch to `/dokploy-dev:logs <app>` (or `/dokploy-dev:compose-logs`, `/dokploy-dev:debug`) to watch the deploy and diagnose failures.

---

## Useful Flags

| Flag | Commands | Description |
|------|----------|-------------|
| `--help` | all | Show help for any command/group |
| `--json` | list/info | Machine-readable output for scripting |

(Flag availability varies by version — confirm with `--help`.)

---

## CLI vs MCP vs REST API

| Method | Best for | Logs/debug? |
|--------|----------|-------------|
| CLI | Terminal/CI provisioning + deploys, env var sync | ❌ no log/debug commands |
| MCP tools | Claude Code automation, multi-step orchestration, **reading logs & debugging** | ✅ `*-readLogs`, `ai-analyzeLogs`, docker introspection |
| REST API | Custom integrations, external scripts, monitoring | ✅ `GET /api/*.readLogs` |

All three use the same access token against the same Dokploy instance.
