# LEARNINGS.md

## 2026-04-07 — MCP server naming and URL auth error

**Problem:** MCP server was named `nocodb-1` instead of `nocodb`, causing tool name mismatches. Additionally, users setting `NOCODB_URL` without the `/mcp` path got "Protected resource does not match" auth errors.
**Fix:** Renamed MCP server from `nocodb-1` to `nocodb` across all 19 files. Updated docs to clarify that `NOCODB_URL` must be the full MCP endpoint URL including `/mcp/{path-id}` (e.g., `https://host/mcp/ncc17zpg5n7v9vs8`). Auth uses `xc-mcp-token` header — NOT OAuth2.
**Root cause:** The `-1` suffix didn't match convention. Docs showed incomplete URL examples without the path ID suffix, leading users to use just the base URL.
**Severity:** Critical
