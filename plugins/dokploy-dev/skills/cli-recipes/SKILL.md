---
name: cli-recipes
description: "This skill should be used when running Dokploy operations from the terminal, deploying via CLI, managing environment variables with env push/pull, or provisioning databases via command line. Triggers: \"dokploy cli\", \"dokploy command\", \"env push\", \"env pull\", \"dokploy deploy cli\"."
---

# Dokploy CLI Recipes

Common CLI commands and workflow patterns for the Dokploy CLI. Use these recipes when operating Dokploy from the terminal instead of (or alongside) MCP tools.

---

## Installation

```bash
npm install -g @dokploy/cli
```

Verify the installation:

```bash
dokploy --version
```

---

## Authentication

```bash
dokploy authenticate
```

When prompted, provide:
- **Server URL** — The Dokploy instance URL (e.g. `https://dokploy.example.com`). Do NOT include the `/api` suffix.
- **API Key** — Generate one from **Settings > API/Tokens** in the Dokploy dashboard.

Verify the connection:

```bash
dokploy verify
```

If verification fails, check the setup skill for troubleshooting authentication issues.

---

## Project Commands

| Command | Description |
|---------|-------------|
| `dokploy project:list` | List all projects on the server |
| `dokploy project:info` | Get details for a specific project |
| `dokploy project:create` | Create a new project |

---

## Application Commands

| Command | Description |
|---------|-------------|
| `dokploy app:create` | Create a new application in a project |
| `dokploy app:deploy` | Trigger a deployment for an application |
| `dokploy app:stop` | Stop a running application |
| `dokploy app:delete` | Delete an application |

---

## Environment Variable Commands

| Command | Description |
|---------|-------------|
| `dokploy env pull <file>` | Pull environment variables from Dokploy to a local file |
| `dokploy env push <file>` | Push environment variables from a local file to Dokploy |
| `dokploy environment:create` | Create a new environment |
| `dokploy environment:delete` | Delete an environment |

### Env push/pull workflow

Pull current env vars, edit locally, then push back:

```bash
dokploy env pull .env.dokploy
# Edit .env.dokploy as needed
dokploy env push .env.dokploy
```

This is the safest way to update environment variables — it avoids typos from manual entry in the dashboard.

---

## Database Commands

All database commands follow this pattern:

```
dokploy database:{type}:{action}
```

### Supported types

| Type | Description |
|------|-------------|
| `postgres` | PostgreSQL |
| `mysql` | MySQL |
| `mariadb` | MariaDB |
| `mongo` | MongoDB |
| `redis` | Redis |
| `libsql` | LibSQL — SQLite-compatible managed service (added in v0.29) |

### Supported actions

| Action | Description |
|--------|-------------|
| `create` | Create a new database service |
| `delete` | Delete a database service |
| `deploy` | Deploy (start) a database container |
| `stop` | Stop a running database container |

### Example: create and deploy PostgreSQL

```bash
dokploy database:postgres:create
dokploy database:postgres:deploy
```

---

## Workflow Recipes

### Recipe 1: Deploy an app from the current directory

```bash
# 1. Authenticate (one-time)
dokploy authenticate

# 2. Create a project
dokploy project:create

# 3. Create an application in the project
dokploy app:create

# 4. Push environment variables
dokploy env push .env

# 5. Deploy
dokploy app:deploy
```

### Recipe 2: Sync environment variables

```bash
# 1. Pull current env vars from Dokploy
dokploy env pull .env.dokploy

# 2. Edit the file locally
# (make changes to .env.dokploy)

# 3. Push updated env vars back
dokploy env push .env.dokploy
```

### Recipe 3: Provision a PostgreSQL database

```bash
# 1. Create a project (or use an existing one)
dokploy project:create

# 2. Create the database
dokploy database:postgres:create

# 3. Deploy (start) the database container
dokploy database:postgres:deploy
```

### Recipe 4: Full-stack deployment (app + database)

```bash
# 1. Create project
dokploy project:create

# 2. Provision database
dokploy database:postgres:create
dokploy database:postgres:deploy

# 3. Create application
dokploy app:create

# 4. Set env vars (including database connection string)
dokploy env push .env

# 5. Deploy application
dokploy app:deploy
```

---

## Useful Flags

| Flag | Commands | Description |
|------|----------|-------------|
| `--help` | All commands | Show help for any command |
| `--json` | List/info commands | Output as JSON for scripting |
| `--project` | app/database commands | Specify project by name or ID |
| `--name` | create commands | Set the resource name inline |
| `--yes` / `-y` | delete commands | Skip confirmation prompt |

---

## CLI vs MCP vs REST API

| Method | Best for |
|--------|----------|
| CLI | Terminal workflows, CI/CD scripts, env var management |
| MCP tools | Claude Code automation, multi-step orchestration |
| REST API | Custom integrations, external scripts, monitoring |

All three methods use the same API key and connect to the same Dokploy instance.
