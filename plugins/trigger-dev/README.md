# trigger-dev

Trigger.dev development plugin for Agents Store. Comprehensive knowledge for developers building background tasks, AI agent workflows, and durable execution on self-hosted Trigger.dev v4.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Project initialization (incl. non-interactive `init --yes`), CLI authentication, self-hosted verification, MCP install and `mcp --readonly`, agent skills |
| **task-development** | Writing tasks — retries, queues, concurrency (incl. the `concurrency` option, server ≥ 4.7.0), wait tokens, TTL, metadata, tags, Zod schemas, global hooks |
| **scheduled-tasks** | Declarative (`schedules.task` + `cron`) and imperative schedules |
| **config-and-build** | trigger.config.ts (required `maxDuration`), build extensions (Prisma with `mode`, Playwright, FFmpeg, Python), TTL defaults |
| **ai-agent-patterns** | Prompt chaining, routing, parallelization, orchestrator-workers, evaluator, task-backed AI tools (AI SDK v5+) |
| **ai-chat-agents** | `chat.agent`, sessions, `useTriggerChatTransport` — durable AI chat (server ≥ 4.5.0) |
| **realtime** | React hooks, streaming AI responses, wait tokens, live dashboards |
| **deployment** | Deploy to staging/prod/preview, CI/CD with a pinned CLI, version skew protection, self-hosted Docker (ClickHouse, s2, generated secrets) and Helm |
| **cli-recipes** | CLI commands — dev server, deploy, profiles, env vars, runs, reports, `install-mcp`, `mcp`, agent skills |
| **mcp-patterns** | All 41 MCP tools across 13 categories — tasks, runs, deploys, profiles, query/analytics, reports, dev server, managed prompts, agent chat, session channels, feedback; REST Management API |
| **observability** | TRQL queries (`runs`/`metrics`/`llm_metrics`), built-in + custom dashboards, automatic LLM cost tracking, span details |
| **managed-prompts** | `prompts.define()` and `resolve()`, prompt versioning — promote code versions, create/update/remove dashboard overrides, reactivate historical versions |
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
- Trigger.dev MCP server configured separately (via `npx trigger.dev@latest install-mcp`, or by hand)
- For a read-only agent run the server as `trigger.dev mcp --readonly` (the installer has no such flag)
- Self-hosted Trigger.dev v4.4.4+ instance running (webapp + supervisor). 4.4.4 is the baseline; features from 4.5-4.7 are marked "requires server ≥ 4.x.y" in the skills (chat agents and managed prompts in the SDK: 4.5.0; `concurrency` option: 4.7.0). Keep the CLI and `@trigger.dev/*` packages at the server's version

## Environment Variables

| Variable | Description | Format |
|----------|-------------|--------|
| `TRIGGER_DEV_SECRET_KEY` | Dev environment secret key | `tr_dev_xxx` |
| `TRIGGER_STAGE_SECRET_KEY` | Staging environment secret key | `tr_dev_xxx` (different key) |
| `TRIGGER_PROD_SECRET_KEY` | Production environment secret key | `tr_prod_xxx` |
| `TRIGGER_SECRET_KEY` | The variable the SDK reads: set it to the key of the environment you are targeting (for example the value of `TRIGGER_DEV_SECRET_KEY`) | `tr_dev_xxx` / `tr_prod_xxx` |
| `TRIGGER_API_URL` | Self-hosted instance URL | `https://trigger.example.com` |
| `TRIGGER_PROJECT_REF` | Project ref from dashboard | `proj_xxxxx` |
| `TRIGGER_ACCESS_TOKEN` | CLI token for CI/CD: a "Deploy only" environment API key (preferred) or a personal access token | `tr_pat_xxx` |

Each environment has its own secret key. The three per-environment variables hold all keys side by side; `TRIGGER_SECRET_KEY` (what the SDK reads by default) is set to the one for the current environment, or pass the appropriate key to the SDK via `configure()`. Project ref goes in `trigger.config.ts` (`project` field) or use `TRIGGER_PROJECT_REF` env var.

## Key Technologies

- **Platform**: Trigger.dev v4 self-hosted (Docker or Helm), baseline server 4.4.4; reference CLI/SDK 4.7.2
- **SDK**: `@trigger.dev/sdk` (import from `@trigger.dev/sdk`)
- **CLI**: `npx trigger.dev@latest` (dev, deploy, promote, env, runs, projects, report, mcp, install-mcp, skills, whoami, list-profiles, switch, update)
- **MCP**: Official MCP server — 41 tools; `--readonly` and `--dev-only` are flags of `trigger.dev mcp`; install it via `npx trigger.dev@latest install-mcp`
- **React**: `@trigger.dev/react-hooks` (useRealtimeRun, useRealtimeStream)
- **Agent skills**: `npx trigger.dev@latest skills` (5 official skills; `install-rules` is an alias) or `npx skills add triggerdotdev/skills`
- **TRQL**: SQL-style query language over ClickHouse — tables `runs`, `metrics`, `llm_metrics`

## Sources

Content built from official Trigger.dev documentation plus MCP tool-schema introspection:
- https://trigger.dev/docs — Official documentation
- https://trigger.dev/docs/skills — Official AI skills
- https://trigger.dev/docs/mcp-introduction — MCP install (the page attributes `--readonly` to `install-mcp`; the CLI help shows it only on `mcp`)
- https://trigger.dev/docs/mcp-tools — MCP tools reference (documents fewer tools than the 41 the server exposes; the plugin reference covers all 41)
- https://trigger.dev/docs/observability/query — TRQL
- https://trigger.dev/docs/observability/dashboards — Dashboards
- https://trigger.dev/changelog/v4-4-4 — 11 new MCP tools, TTL defaults, LLM cost tracking
- https://trigger.dev/docs/skills and https://trigger.dev/docs/mcp-agent-rules — Agent skills (formerly agent rules)
- https://trigger.dev/docs/building-with-ai — AI integration guide
- https://trigger.dev/docs/self-hosting/docker and `/self-hosting/kubernetes` — Self-hosting guides
- https://trigger.dev/docs/ai-chat/overview — Chat agents and sessions
- https://trigger.dev/docs/ai/prompts — Managed prompts SDK
- https://trigger.dev/docs/concurrency — Concurrency and named limits
- https://github.com/triggerdotdev/skills — Official skills repository
- MCP tool schemas — introspected from `npx trigger.dev@latest mcp` (41 tools)
- `@trigger.dev/sdk`, `trigger.dev` and `@trigger.dev/build` 4.7.2 packages (docs ship inside `@trigger.dev/sdk`)
