# dify-ops

Dify self-hosted update operations plugin for the Agents Store marketplace. Helps update Dify Docker deployments safely: pre-flight against the target release (including the bundled Weaviate migration path), back up the volumes with the stack down, merge a release tag into a local dev branch, sync environment variables, pull images and verify.

Written against the Dify 1.17.x layout (generated `docker-compose.yaml`, split `envs/` configuration). Dify releases every one to five weeks; the plugin reads the target release's own notes before it changes anything.

## Type

Technology (Level 1) -- knowledge-only, no MCP server.

## Skills

| Skill | Description |
|-------|-------------|
| `dify-docker-architecture` | Dify Docker Compose setup -- services, containers, directory layout, `.env` and `envs/` |
| `update-workflow` | Update workflow -- target tag, Weaviate migration gate, backup, merge, conflict handling, rollback |
| `env-sync` | `.env` vs `.env.example` and `envs/` synchronization -- detect new and changed variables, mask secrets |
| `examples` | End-to-end update scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/dify-ops:update [tag\|main] [--yes] [--weaviate-staged]` | Full update workflow -- pre-flight, plan, backup, merge, env sync, pull and start, verify. Default target: the latest stable tag |
| `/dify-ops:status` | Check current Dify state -- running version vs latest stable tag, containers, env sync status |

## Agent

**dify-updater** -- Handles Dify update operations conversationally, including merge conflict resolution and troubleshooting.

## Prerequisites

- Dify installed from the official GitHub repo (https://github.com/langgenius/dify)
- Local `dev` branch with customizations (forked from `main`); an official `git clone --branch <tag>` has no `dev` branch, the update creates it
- Docker with Docker Compose >= 2.24.0 (`docker compose version`)
- Git configured with origin pointing to upstream Dify repo
- `gh` (optional) to read the release notes of the versions between yours and the target

## Workflow

1. User runs `/dify-ops:update` (or `/dify-ops:update 1.17.1` for a specific version, `main` only on request)
2. Plugin detects working directory (dify root or docker subdirectory)
3. Pre-flight, read-only: git state, Docker Compose version, Docker project name, target tag, release notes, **Weaviate migration gate**
4. Prints the eight-block plan (TARGET, PRECHECK, CHANGE, BACKUP, IMPACT, VALIDATE, ROLLBACK, APPLY) and waits for confirmation
5. Backs up: copies `docker-compose.yaml` and `.env`, stops the stack, `docker compose down`, archives `volumes/` outside the repo
6. Merges the tag into `dev` and resolves any merge conflicts interactively
7. Syncs `.env` with `.env.example` and the `envs/` templates (adds new variables, masks secrets)
8. Runs `docker compose pull` and `docker compose up -d`
9. Verifies containers are healthy and asks for a test retrieval against a knowledge base

## Weaviate gate

From Dify 1.17.1 the bundled Weaviate server moves from 1.27.0 to 1.39.2, and an existing data volume cannot cross 12 minor versions in one step -- a plain pull and restart can silently and permanently break vector search. When the update crosses 1.17.1 on a bundled Weaviate that holds data, `/dify-ops:update` stops before any change and points to the official runbook (https://docs.dify.ai/en/self-host/deploy/troubleshooting/weaviate-server-migration-path). After following it, re-run with `--weaviate-staged`. Fresh installs, external Weaviate and other vector stores are not affected.

## Customizing

`docker/docker-compose.yaml` is generated and replaced by every release. Keep customizations in `.env` (host ports are `EXPOSE_NGINX_PORT` and `EXPOSE_NGINX_SSL_PORT`), in `envs/*.env` copied from the `*.env.example` templates, and in `docker/docker-compose.override.yaml`, which Compose reads automatically and upstream git ignores.
