# LEARNINGS.md — vercel-dev

## 2026-04-02 — plugin config: Add HTTP MCP server for Vercel

**Problem:** Plugin had no MCP server connection — users couldn't use Vercel's official MCP tools (project management, deployments, environment variables) directly through Claude Code.
**Fix:** Created `.mcp.json` with HTTP streamable MCP endpoint `https://mcp.vercel.com`. Added `mcpServers` reference to `plugin.json`.
**Root cause:** Plugin was forked from Vercel's official plugin which handled MCP differently; HTTP MCP endpoint wasn't configured for Agents Store convention.
**Severity:** Major
