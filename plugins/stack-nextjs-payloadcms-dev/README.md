# stack-nextjs-payloadcms-dev

Stack plugin for building projects where **one Next.js application is the entire system**: frontend, admin panel, API, business logic, and background workflows. Payload CMS v3 is embedded in the Next.js App Router; all backend logic runs on stack primitives — Server Actions, Payload hooks, and the Payload Jobs Queue. PostgreSQL, Docker deployment.

Individual tool knowledge lives in the `payloadcms-dev` and `nextjs-dev` technology plugins — this plugin covers **how the pieces compose** into one architecture.

## Skills

| Skill | Purpose |
|---|---|
| `init-project` | Bootstrap or attach: create-payload-app, env, tsconfig alias, route groups, MCP wiring, verification |
| `architecture` | The canonical layout and the decision matrix: where every kind of logic lives |
| `backend-logic` | Server Actions + hooks + jobs composition; enforce-in-hooks, pre-check-in-actions |
| `payload-to-nextjs` | Read paths: query layer, DTOs, caching, and the admin-edit revalidation bridge |
| `auth-and-access` | One identity system: sessions in RSC, roles module, row-filtered access, tenant scoping |
| `background-job` | Jobs Queue as the workflow engine: tasks, workflows, cron, runner topologies |
| `full-feature` | Nine-step end-to-end recipe + fill-in template |
| `examples` | Worked scenarios: leave-request approval workflow, content publishing with revalidation |

## Agent

`stack-orchestrator` — coordinates cross-layer features, places logic via the decision matrix, debugs queue/cache/access issues spanning layers.

## MCP Servers

`.mcp.json` declares two first-party servers:

- **payload** (HTTP) — the project itself via [`@payloadcms/plugin-mcp`](https://payloadcms.com/docs/plugins/mcp): `${PAYLOAD_MCP_URL}` (default `http://localhost:3000/api/mcp`) with `Bearer ${PAYLOAD_MCP_API_KEY}`. Create the key in admin → MCP → API Keys and enable per-collection capabilities on it.
- **next-devtools** (stdio, `npx next-devtools-mcp`) — runtime introspection of the running `next dev` server (Next 16+): errors, logs, page metadata.

## Prerequisites

- Node >= 20.9, pnpm, PostgreSQL
- Payload v3 with Next.js 16.2.6+ (or 15.2.9+/15.3.9+/15.4.11+ on older payload 3.x)
- Env vars from `templates/.env.example`: `DATABASE_URI`, `PAYLOAD_SECRET`, `NEXT_PUBLIC_SERVER_URL`, `ENABLE_JOBS`, `PAYLOAD_MCP_URL`, `PAYLOAD_MCP_API_KEY`

## Installation

```
/plugin install stack-nextjs-payloadcms-dev@agents-store-claude-plugins
```

Then follow the `init-project` skill: copy `templates/.env.example` to the project, fill values, wire the MCP servers, and verify with `/mcp`.

## Templates

- `templates/.env.example` — full env catalogue for the stack
- `templates/CLAUDE.md.template` — project CLAUDE.md preloaded with stack rules and layout
