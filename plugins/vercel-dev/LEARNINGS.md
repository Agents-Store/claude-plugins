# LEARNINGS.md — vercel-dev

## 2026-04-02 — plugin config: Add HTTP MCP server for Vercel

**Problem:** Plugin had no MCP server connection — users couldn't use Vercel's official MCP tools (project management, deployments, environment variables) directly through Claude Code.
**Fix:** Created `.mcp.json` with HTTP streamable MCP endpoint `https://mcp.vercel.com`. Added `mcpServers` reference to `plugin.json`.
**Root cause:** Plugin was forked from Vercel's official plugin which handled MCP differently; HTTP MCP endpoint wasn't configured for Agents Store convention.
**Severity:** Major

## 2026-04-06 — deploy command: Ask target instead of defaulting to preview

**Problem:** Running `/deploy` with no arguments silently deployed to preview. User expected to be asked "production or preview?" and was frustrated when a preview deploy failed due to missing env vars — wasted build minutes and time.
**Fix:** Changed the Plan section in `commands/deploy.md` to require asking the user for deployment target when no argument is given, instead of silently defaulting to preview.
**Root cause:** The command description said "Default is preview deployment" and the Plan section only asked for confirmation on production, silently proceeding with preview otherwise. Users don't always know the default.
**Severity:** Major
