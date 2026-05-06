# LEARNINGS.md

## 2026-05-06 — Split env vars by transport (MCP vs CLI/API)

**Problem:** A single `NOCODB_TOKEN` was reused for both the MCP `xc-mcp-token` header and the CLI/REST API token, even though those are distinct tokens minted in different NocoDB UI sections (Integrations → MCP vs Account Settings → API Tokens). Sharing one variable forced users to pick which surface worked at any given time.
**Fix:** Split into two pairs — MCP uses `NOCODB_MCP_URL` + `NOCODB_MCP_TOKEN`, CLI/API uses `NOCODB_URL` + `NOCODB_API_TOKEN`. Updated `.mcp.json`, README, setup, troubleshoot, and cli-reference skills. Bumped to 1.0.6.
**Root cause:** Initial scaffolding conflated the two transports because both happen to authenticate with a NocoDB-issued token string.
**Severity:** Major

## 2026-04-07 — MCP server naming and URL auth error

**Problem:** MCP server was named `nocodb-1` instead of `nocodb`, causing tool name mismatches. Additionally, users setting `NOCODB_URL` without the `/mcp` path got "Protected resource does not match" auth errors.
**Fix:** Renamed MCP server from `nocodb-1` to `nocodb` across all 19 files. Updated docs to clarify that `NOCODB_URL` must be the full MCP endpoint URL including `/mcp/{path-id}` (e.g., `https://host/mcp/ncc17zpg5n7v9vs8`). Auth uses `xc-mcp-token` header — NOT OAuth2.
**Root cause:** The `-1` suffix didn't match convention. Docs showed incomplete URL examples without the path ID suffix, leading users to use just the base URL.
**Severity:** Critical
