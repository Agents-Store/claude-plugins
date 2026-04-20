# LEARNINGS

## 2026-04-20 — nocobase-dev: Add dev-instance MCP server and env vars for NocoBase sandbox

**Feature:** Introduced a dedicated NocoBase **dev instance** (separate from production) for building and testing new tables, fields, menus, pages, blocks, workflows, and dev/test apps. The dev instance is exposed through both the HTTP API and a new `nocobase-dev` HTTP MCP server at `${NOCOBASE_DEV_URL}/api/mcp` that uses the full `nc-mcp` toolset (~146 tools).
**Implementation:** Added `nocobase-dev` to `.mcp.json`. Added `NOCOBASE_DEV_URL` and `NOCOBASE_DEV_API_KEY` to `templates/.env.example`. Updated `init-project` (dev-vs-prod NocoBase section, env-var rows, verification steps for MCP + HTTP API), `nocobase-to-n8n` (dev-vs-prod usage guidance), `full-feature` (build-on-dev-first rule), `stack-orchestrator` agent (dev-vs-prod decision rule), `README.md` (new MCP row and env-var notes), and `templates/CLAUDE.md.template` (dev-instance row, rule, and data-flow entry). Bumped plugin to 1.2.0.
**Rationale:** Production NocoBase held live data, leaving no safe surface for schema/UX experimentation. A dedicated dev instance lets authors iterate on collections, menus, and pages without risk — and its MCP+API access unlocks Claude-driven authoring and dev-app testing without touching prod.

## 2026-04-08 — postgresql-api: Add PostgreSQL MCP and PostgREST API support

**Feature:** Added direct PostgreSQL access via PostgreSQL MCP (27 tools from Supabase Toolbox v0.31.0) and PostgREST API (v14.8) for REST CRUD operations
**Implementation:** Created `postgresql-api` skill with full tool reference and API guide. Added `postgresql-mcp` to `.mcp.json`. Added 4 env vars (POSTGRESQL_MCP_URL, POSTGRESQL_MCP_TOKEN, POSTGRESQL_API_URL, POSTGRESQL_API_TOKEN). Updated init-project, full-feature, CLAUDE.md.template, stack-orchestrator agent, and README.md with PostgreSQL MCP and PostgREST integration points.
**Rationale:** The stack previously accessed PostgreSQL only indirectly via NocoDB MCP. Direct access enables complex SQL queries (JOINs, CTEs), database administration, performance analysis, and REST CRUD from n8n/Trigger.dev workflows without MCP.
