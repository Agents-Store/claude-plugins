# trigger-dev

Trigger.dev development plugin for Agents Store. Comprehensive knowledge for developers building background tasks, AI agent workflows, and durable execution on self-hosted Trigger.dev v4.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Project initialization, CLI authentication, self-hosted verification, `install-mcp` |
| **task-development** | Writing tasks — retries, queues, waits, TTL, metadata, tags, Zod schemas |
| **config-and-build** | trigger.config.ts, build extensions (Prisma, Playwright, FFmpeg, Python), TTL defaults |
| **ai-agent-patterns** | Prompt chaining, routing, parallelization, orchestrator-workers, evaluator |
| **realtime** | React hooks, streaming AI responses, wait tokens, live dashboards |
| **deployment** | Deploy to staging/production/preview, CI/CD, self-hosted Docker |
| **cli-recipes** | CLI commands — dev server, deploy, profiles, `install-mcp`, agent rules |
| **mcp-patterns** | All 33 MCP tools across 9 categories — tasks, runs, deploys, profiles, query/analytics, dev server, managed prompts; REST Management API |
| **observability** | TRQL queries (`runs`/`metrics`/`llm_metrics`), built-in + custom dashboards, automatic LLM cost tracking, span details |
| **managed-prompts** | Prompt versioning — promote code versions, create/update/remove dashboard overrides, reactivate historical versions |
| **troubleshoot** | Common errors, self-hosted diagnostics, Docker debugging, TRQL limits |
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
- Trigger.dev MCP server configured separately (via `npx trigger.dev@latest install-mcp`)
- Self-hosted Trigger.dev v4.4.4+ instance running (webapp + supervisor)

## Environment Variables

| Variable | Description | Format |
|----------|-------------|--------|
| `TRIGGER_DEV_SECRET_KEY` | Dev environment secret key | `tr_dev_xxx` |
| `TRIGGER_STAGE_SECRET_KEY` | Staging environment secret key | `tr_dev_xxx` (different key) |
| `TRIGGER_PROD_SECRET_KEY` | Production environment secret key | `tr_prod_xxx` |
| `TRIGGER_API_URL` | Self-hosted instance URL | `https://trigger.example.com` |
| `TRIGGER_PROJECT_REF` | Project ref from dashboard | `proj_xxxxx` |
| `TRIGGER_ACCESS_TOKEN` | Personal access token (CI/CD) | `tr_pat_xxx` |

Each environment has its own secret key — pass the appropriate one to the SDK via `configure()`. Project ref goes in `trigger.config.ts` (`project` field) or use `TRIGGER_PROJECT_REF` env var.

## Key Technologies

- **Platform**: Trigger.dev v4.4.4 (self-hosted Docker)
- **SDK**: `@trigger.dev/sdk` (import from `@trigger.dev/sdk`)
- **CLI**: `npx trigger.dev@latest` (dev, deploy, install-mcp, install-rules, whoami, list-profiles, switch)
- **MCP**: Official MCP server — 33 tools; install via `npx trigger.dev@latest install-mcp`
- **React**: `@trigger.dev/react-hooks` (useRealtimeRun, useRealtimeStream)
- **Rules**: `npx trigger.dev@latest install-rules` (5 rule sets)
- **Skills**: `npx skills add triggerdotdev/skills` (5 official skills)
- **TRQL**: SQL-style query language over ClickHouse — tables `runs`, `metrics`, `llm_metrics`

## Sources

Content built from official Trigger.dev documentation plus MCP tool-schema introspection:
- https://trigger.dev/docs — Official documentation
- https://trigger.dev/docs/skills — Official AI skills
- https://trigger.dev/docs/mcp-introduction — `install-mcp` + flags
- https://trigger.dev/docs/mcp-tools — MCP tools reference (24 of 33 tools; Managed Prompts pending)
- https://trigger.dev/docs/observability/query — TRQL
- https://trigger.dev/docs/observability/dashboards — Dashboards
- https://trigger.dev/changelog/v4-4-4 — 11 new MCP tools, TTL defaults, LLM cost tracking
- https://trigger.dev/docs/mcp-agent-rules — Agent rules
- https://trigger.dev/docs/building-with-ai — AI integration guide
- https://trigger.dev/docs/self-hosting — Self-hosting guide
- https://github.com/triggerdotdev/skills — Official skills repository
- Managed Prompts MCP tool schemas — introspected from `npx trigger.dev@latest mcp` (the `/docs/prompts` page is not yet published)
