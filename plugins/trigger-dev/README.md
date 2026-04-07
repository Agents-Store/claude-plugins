# trigger-dev

Trigger.dev development plugin for Agents Store. Comprehensive knowledge for developers building background tasks, AI agent workflows, and durable execution on self-hosted Trigger.dev v4.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Project initialization, CLI authentication, self-hosted verification |
| **task-development** | Writing tasks — retries, queues, waits, metadata, tags, Zod schemas |
| **config-and-build** | trigger.config.ts, build extensions (Prisma, Playwright, FFmpeg, Python) |
| **ai-agent-patterns** | Prompt chaining, routing, parallelization, orchestrator-workers, evaluator |
| **realtime** | React hooks, streaming AI responses, wait tokens, live dashboards |
| **deployment** | Deploy to staging/production/preview, CI/CD, self-hosted Docker |
| **cli-recipes** | CLI commands — dev server, deploy, profiles, MCP setup, agent rules |
| **mcp-patterns** | 14+ MCP tools reference, REST Management API endpoints |
| **troubleshoot** | Common errors, self-hosted diagnostics, Docker debugging |
| **examples** | End-to-end scenarios: webhook processor, AI pipeline, cron data sync |

## Agent

**trigger-developer** — Development specialist agent for building with Trigger.dev. Helps write tasks, debug runs, design workflows, configure builds, and deploy to environments.

## Commands

| Command | Description |
|---------|-------------|
| `/trigger-dev:init` | Initialize Trigger.dev in the current project |
| `/trigger-dev:dev` | Start the dev server |
| `/trigger-dev:deploy` | Deploy tasks to an environment |
| `/trigger-dev:create-task` | Create a new task file from template |

## Type

**Technology Plugin (dev)** — No `.mcp.json`. This plugin provides knowledge about Trigger.dev, not the MCP connection itself.

## Prerequisites

- Node.js 18.20+ and TypeScript 5.0.4+
- Trigger.dev MCP server configured separately (via `npx trigger.dev@latest mcp`)
- Self-hosted Trigger.dev v4 instance running (webapp + supervisor)

## Environment Variables

| Variable | Type | Description | Format |
|----------|------|-------------|--------|
| `TRIGGER_SECRET_KEY` | Official | The key the SDK reads at runtime | `tr_dev_xxx` / `tr_prod_xxx` |
| `TRIGGER_DEV_SECRET_KEY` | Convention | Dev environment key | `tr_dev_xxx` |
| `TRIGGER_STAGE_SECRET_KEY` | Convention | Staging environment key | `tr_dev_xxx` (different key) |
| `TRIGGER_PROD_SECRET_KEY` | Convention | Production environment key | `tr_prod_xxx` |
| `TRIGGER_API_URL` | Official | Self-hosted instance URL | `https://trigger.example.com` |
| `TRIGGER_PROJECT_REF` | Convention | Project ref from dashboard | `proj_xxxxx` |
| `TRIGGER_ACCESS_TOKEN` | Official | Personal access token (CI/CD) | `tr_pat_xxx` |

Store per-env keys separately, map the active one to `TRIGGER_SECRET_KEY`. Project ref goes in `trigger.config.ts` (`project` field) — use `TRIGGER_PROJECT_REF` env var for CI/CD.

## Key Technologies

- **Platform**: Trigger.dev v4 GA (self-hosted Docker)
- **SDK**: `@trigger.dev/sdk` (import from `@trigger.dev/sdk`)
- **CLI**: `npx trigger.dev@latest` (dev, deploy, mcp, install-rules)
- **MCP**: Official MCP server via `npx trigger.dev@latest mcp`
- **React**: `@trigger.dev/react-hooks` (useRealtimeRun, useRealtimeStream)
- **Rules**: `npx trigger.dev@latest install-rules` (5 rule sets)
- **Skills**: `npx skills add triggerdotdev/skills` (5 official skills)

## Sources

Content built from official Trigger.dev documentation:
- https://trigger.dev/docs — Official documentation
- https://trigger.dev/docs/skills — Official AI skills
- https://trigger.dev/docs/mcp-tools — MCP tools reference
- https://trigger.dev/docs/mcp-agent-rules — Agent rules
- https://trigger.dev/docs/building-with-ai — AI integration guide
- https://trigger.dev/docs/self-hosting — Self-hosting guide
- https://github.com/triggerdotdev/skills — Official skills repository
