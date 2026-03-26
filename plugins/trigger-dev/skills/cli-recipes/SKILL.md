---
name: cli-recipes
description: This skill should be used when the user asks about "trigger.dev CLI", "trigger.dev command line", "npx trigger.dev", "trigger.dev dev server", "trigger.dev deploy command", "trigger.dev mcp install", "trigger.dev profiles", or needs ready-to-use CLI commands and automation recipes for Trigger.dev.
---

# Trigger.dev CLI Recipes

Ready-to-use CLI commands for local development, deployment, MCP setup, and project management.

## Installation

The CLI is bundled with the SDK — no separate install needed:

```bash
# Run directly with npx (recommended)
npx trigger.dev@latest <command>

# Or with other package managers
pnpm dlx trigger.dev@latest <command>
yarn dlx trigger.dev@latest <command>
```

Current version: **4.x** (v4 GA)

## Authentication

### Login to Cloud

```bash
npx trigger.dev@latest login
```

### Login to Self-Hosted

```bash
# With API URL
npx trigger.dev@latest login -a https://trigger.example.com

# With named profile
npx trigger.dev@latest login -a https://trigger.example.com --profile self-hosted
```

### Profile Management

```bash
# List all profiles
npx trigger.dev@latest list-profiles

# Switch profile interactively
npx trigger.dev@latest switch

# Switch to specific profile
npx trigger.dev@latest switch self-hosted

# Remove a profile
npx trigger.dev@latest logout --profile self-hosted

# Check who you're logged in as
npx trigger.dev@latest whoami
```

## MCP Server & Agent Rules

### Install MCP Server

```bash
# Interactive wizard — choose AI tool and scope
npx trigger.dev@latest mcp
```

This installs the official Trigger.dev MCP server for your AI coding tool (Cursor, Claude Code, VSCode Copilot, Windsurf, Cline, Gemini CLI, etc.).

Manual MCP config:

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

Dev-only mode (blocks production access):

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

### Install Agent Rules

```bash
# Interactive — choose AI tool and rule sets
npx trigger.dev@latest install-rules
```

Available rule sets:

| Rule Set | Tokens | Description |
|----------|--------|-------------|
| Basic rules | 1,200 | Core task writing patterns |
| Advanced tasks | 3,000 | Advanced task patterns |
| Scheduled tasks | 780 | Cron/scheduled tasks |
| Configuration | 1,900 | trigger.config.ts setup |
| Realtime | 1,700 | Realtime API and React hooks |

Rules auto-update when you run `npx trigger.dev@latest dev`.

## Local Development

### Start Dev Server

```bash
# Start the dev server
npx trigger.dev@latest dev

# With custom config path (monorepo)
npx trigger.dev@latest dev --config ./packages/jobs/trigger.config.ts

# With specific log level
npx trigger.dev@latest dev --log-level debug

# With specific profile
npx trigger.dev@latest dev --profile self-hosted
```

The dev server watches for file changes in your `dirs` (default: `src/trigger/`), registers tasks with the dev environment, and executes tasks locally.

### Self-Hosted Dev Server

Ensure these env vars are set:

```bash
# .env
TRIGGER_API_URL=https://trigger.your-domain.com
TRIGGER_SECRET_KEY=tr_dev_xxxxxxxxxxxxxx
```

## Project Initialization

```bash
# Interactive init
npx trigger.dev@latest init

# With project ref and API URL (self-hosted)
npx trigger.dev@latest init -p <project-ref> -a https://trigger.example.com

# With specific runtime
npx trigger.dev@latest init --runtime bun
```

Creates: `trigger.config.ts`, `src/trigger/` directory with example task, updates `package.json`.

### Init Options

| Flag | Description |
|------|-------------|
| `-p, --project-ref` | Project ref (proj_xxx) |
| `-a, --api-url` | API URL (for self-hosted) |
| `--runtime` | Runtime: node or bun |
| `--skip-package-install` | Skip SDK install |
| `--override-config` | Override existing config |
| `--javascript` | Use JavaScript instead of TypeScript |

## Deployment

### Deploy to Environments

```bash
# Deploy to production (default)
npx trigger.dev@latest deploy

# Deploy to staging
npx trigger.dev@latest deploy --env staging

# Deploy to preview branch
npx trigger.dev@latest deploy --env preview --branch feature/new-task
```

### Deploy Options

| Flag | Description |
|------|-------------|
| `--env <environment>` | Target: staging, production, preview |
| `--branch <name>` | Branch name (required for preview) |
| `--skip-update-check` | Skip package version check |
| `--config <path>` | Custom trigger.config.ts path |
| `--project-ref <ref>` | Override project ref |
| `--skip-promotion` | Deploy without making it current (canary) |

### Self-Hosted Deploy

For self-hosted, the CLI uses your login profile. No extra flags needed if you're logged in:

```bash
# Already logged in via: login -a <url>
npx trigger.dev@latest deploy --env production
```

For CI/CD, use environment variables:

```bash
TRIGGER_API_URL=https://trigger.example.com \
TRIGGER_ACCESS_TOKEN=tr_pat_xxx \
npx trigger.dev@latest deploy --env production
```

## CI/CD (GitHub Actions)

```yaml
- name: Deploy to production
  run: npx trigger.dev@latest deploy --env production
  env:
    TRIGGER_API_URL: ${{ secrets.TRIGGER_API_URL }}
    TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
```

## Package.json Scripts

```json
{
  "scripts": {
    "trigger:dev": "trigger.dev dev",
    "trigger:deploy:staging": "trigger.dev deploy --env staging",
    "trigger:deploy:prod": "trigger.dev deploy --env production"
  }
}
```

## Self-Hosted Docker Commands (v4)

```bash
# Clone repo and navigate to hosting
git clone --depth=1 https://github.com/triggerdotdev/trigger.dev
cd trigger.dev/hosting/docker

# Start webapp (includes postgres, redis, registry, minio)
cd webapp && docker compose up -d

# Start worker (supervisor)
cd worker && docker compose up -d

# Combined (same machine)
docker compose -f webapp/docker-compose.yml -f worker/docker-compose.yml up -d

# View logs
docker compose logs -f webapp
docker compose logs -f supervisor

# Check status
docker compose ps

# Version lock (in .env)
TRIGGER_IMAGE_TAG=v4.0.0
```

### Registry Login (self-hosted)

Builds run locally — you must login to the built-in registry:

```bash
docker login -u <username> <registry-url>
```

Default: `localhost:5000`, user: `registry-user`, password: `very-secure-indeed` (change in production!).

## Common Issues

| Issue | Solution |
|-------|----------|
| `Cannot find trigger.config.ts` | Run from project root or pass `--config` |
| `Authentication failed` | Check `TRIGGER_SECRET_KEY` or re-login |
| `Connection refused` | Verify `TRIGGER_API_URL` and instance health |
| `Build failed` | Check build extensions in trigger.config.ts |
| `No tasks found` | Ensure task files are in configured `dirs` |
| `Version mismatch` | Update: `npm install @trigger.dev/sdk@latest` |
| Redirected to cloud | Use `login -a <url>` or set `TRIGGER_API_URL` |
| Registry push fails | Login to registry: `docker login -u user registry:5000` |
