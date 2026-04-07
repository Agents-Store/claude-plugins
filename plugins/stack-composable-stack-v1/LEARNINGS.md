# LEARNINGS

## 2026-04-08 — postgresql-api: Add PostgreSQL MCP and PostgREST API support

**Feature:** Added direct PostgreSQL access via PostgreSQL MCP (27 tools from Supabase Toolbox v0.31.0) and PostgREST API (v14.8) for REST CRUD operations
**Implementation:** Created `postgresql-api` skill with full tool reference and API guide. Added `postgresql-mcp` to `.mcp.json`. Added 4 env vars (POSTGRESQL_MCP_URL, POSTGRESQL_MCP_TOKEN, POSTGRESQL_API_URL, POSTGRESQL_API_TOKEN). Updated init-project, full-feature, CLAUDE.md.template, stack-orchestrator agent, and README.md with PostgreSQL MCP and PostgREST integration points.
**Rationale:** The stack previously accessed PostgreSQL only indirectly via NocoDB MCP. Direct access enables complex SQL queries (JOINs, CTEs), database administration, performance analysis, and REST CRUD from n8n/Trigger.dev workflows without MCP.
