# LEARNINGS.md

## 2026-04-07 — MCP server naming and URL auth error

**Problem:** MCP server was named `nocodb-1` instead of `nocodb`, causing tool name mismatches. Additionally, users setting `NOCODB_URL` without the `/mcp` path got "Protected resource does not match" auth errors.
**Fix:** Renamed MCP server from `nocodb-1` to `nocodb` across all 19 files. Changed `.mcp.json` to append `/mcp` to `${NOCODB_URL}` automatically — users only provide the base instance URL. Updated setup docs accordingly.
**Root cause:** The `-1` suffix didn't match convention. The URL required users to know the internal MCP endpoint path — the plugin should handle that itself.
**Severity:** Critical
