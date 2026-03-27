# dify-ops

Dify self-hosted update operations plugin for the Agents Store marketplace. Helps update Dify Docker deployments by pulling upstream changes, merging into a local dev branch, syncing environment variables, and rebuilding containers.

## Type

Technology (Level 1) -- knowledge-only, no MCP server.

## Skills

| Skill | Description |
|-------|-------------|
| `dify-docker-architecture` | Dify Docker Compose setup -- services, containers, directory layout |
| `update-workflow` | Git workflow for updating Dify -- fetch, merge, conflict handling |
| `env-sync` | .env vs .env.example synchronization -- detect and add new variables |
| `examples` | End-to-end update scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/dify-ops:update [tag]` | Full update workflow -- git pull, merge, env sync, rebuild |
| `/dify-ops:status` | Check current Dify state -- version, containers, env sync status |

## Agent

**dify-updater** -- Handles Dify update operations conversationally, including merge conflict resolution and troubleshooting.

## Prerequisites

- Dify installed from the official GitHub repo (https://github.com/langgenius/dify)
- Local `dev` branch with customizations (forked from `main`)
- Docker and Docker Compose V2 installed
- Git configured with origin pointing to upstream Dify repo

## Workflow

1. User runs `/dify-ops:update` (or `/dify-ops:update 0.15.0` for specific version)
2. Plugin detects working directory (dify root or docker subdirectory)
3. Fetches latest from upstream, merges into dev branch
4. Resolves any merge conflicts interactively
5. Syncs .env with .env.example (adds new variables with defaults)
6. Detects Docker Compose project name from running containers
7. Rebuilds with `docker compose up -d --build`
8. Verifies containers are healthy
