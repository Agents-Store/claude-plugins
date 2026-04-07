# LEARNINGS.md

## 2026-04-07 — MCP server naming and URL auth error

**Problem:** MCP server was named `nocodb-1` instead of `nocodb`, causing tool name mismatches. Additionally, users setting `NOCODB_URL` without the `/mcp` path got "Protected resource does not match" auth errors.
**Fix:** Renamed MCP server from `nocodb-1` to `nocodb` across all 19 files (`.mcp.json`, skills, commands, agents, README). Updated setup skill to clarify that `NOCODB_URL` must include `/mcp` path. Added troubleshooting entry for the "Protected resource" error.
**Root cause:** The `-1` suffix was likely added to avoid naming conflicts but doesn't match the standard convention. The URL guidance was ambiguous — example showed `/mcp/your-path` but didn't emphasize `/mcp` is mandatory.
**Severity:** Critical
