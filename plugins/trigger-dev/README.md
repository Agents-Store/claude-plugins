# trigger-dev

Trigger.dev development plugin for Agents Store. Knowledge plugin for developers building background tasks and workflows with Trigger.dev v4.

Designed for **self-hosted** Trigger.dev v4 instances.

## Skills

| Skill | Description |
|-------|-------------|
| **setup** | Verify MCP connection, self-hosted instance health |
| **mcp-patterns** | All 14 MCP tools — parameters, patterns, best practices |
| **task-development** | Writing tasks, cron jobs, queues, build extensions, trigger.config.ts |
| **task-execution** | Triggering tasks, monitoring runs, debugging failures |
| **deployment** | Deploy to staging/production/preview, CI/CD patterns |
| **ai-agent-patterns** | Prompt chaining, routing, parallelization, human-in-the-loop, realtime |
| **sdk-patterns** | @trigger.dev/sdk v3 — task, schedules, wait, queue, React hooks |
| **cli-recipes** | CLI commands — dev server, deploy, init, self-hosted Docker |
| **api-reference** | REST Management API endpoints with curl examples |
| **examples** | End-to-end MCP workflow examples and code templates |
| **troubleshoot** | Common errors, self-hosted diagnostics, Docker debugging |

## Agent

**trigger-developer** — Developer specialist agent for building with Trigger.dev. Helps write tasks, debug runs, design workflows, and deploy to environments.

## Type

**Technology Plugin (dev)** — No `.mcp.json`. This plugin provides knowledge about Trigger.dev, not the MCP connection itself.

## Prerequisites

- Trigger.dev MCP server configured (via Stack Plugin or user settings)
- Self-hosted Trigger.dev instance running
- Valid `TRIGGER_SECRET_KEY` with appropriate permissions

## Key Technologies

- **Platform**: Trigger.dev v4 GA (self-hosted Docker or Kubernetes)
- **SDK**: `@trigger.dev/sdk` v4.x (npm), import from `@trigger.dev/sdk/v3`
- **CLI**: `npx trigger.dev@latest` (dev, deploy, mcp, install-rules, switch, login)
- **Official MCP**: `npx trigger.dev@latest mcp` (stdio MCP server with dev-only mode)
- **Agent Rules**: `npx trigger.dev@latest install-rules` (Cursor, Claude Code, VSCode, etc.)
- **API**: REST Management API + SDK programmatic access
- **MCP Tools**: `tds-*` prefix (14 tools)
- **React Hooks**: `@trigger.dev/react-hooks` (useRealtimeRun, useRealtimeBatch)

## Sources Used

Plugin content verified against:
- https://trigger.dev/docs/self-hosting/docker — v4 self-hosting guide
- https://trigger.dev/launchweek/2/official-mcp-server — Official MCP server announcement
- https://trigger.dev/launchweek/2/trigger-v4-ga — v4 GA release
- https://trigger.dev/docs/apikeys — Authentication docs
- https://trigger.dev/docs/management/overview — Management API
- https://trigger.dev/docs/cli-dev-commands — CLI dev reference
- https://trigger.dev/docs/cli-deploy-commands — CLI deploy reference
- https://trigger.dev/docs/cli-init-commands — CLI init reference
- https://www.npmjs.com/package/trigger.dev — CLI npm package (v4.4.2)
