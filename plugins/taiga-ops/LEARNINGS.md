# taiga-ops — Learnings

Accumulated fixes and discoveries for the `taiga-ops` plugin. Newest first.

<!-- Format:
## [DATE] — [skill-name]: Brief description

**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## 2026-10-03 — troubleshoot, setup, README: live link to the community MCP server; Cloud limits; archived projects

**Problem:** The docs pointed at `greddy7574/taiga-mcp-server` (GitHub 404) and quoted an unverified "~33 tools". Nothing said that Taiga Cloud now enforces plan limits, or that a write to an archived project fails with `403 "Archived element"`.
**Fix:** Link is now `greddy7574/taigaMcpServer` (HTTP 200, same npm package `taiga-mcp-server`), plus `madebyclowd/taiga-mcp-server`; the tool count is gone. `setup` and README describe the Cloud plan limits (since 2025-10-15) versus self-hosted; `troubleshoot` gained the `"Archived element"` 403 and how to check `archived_code` on `GET /projects/{id}`. README notes that Tenzu (formerly Taiga Next) is a separate product.
**Root cause:** The author repo was renamed after the plugin was written; the 6.10.0 archiving feature (2026-04-20) and the Cloud plans (2025-10-15) postdate it. `archived_code` and the error text were checked against `taigaio/taiga-back` `main` (`taiga/projects/api.py`, `models.py`, `serializers.py`); how a project is archived through the API was not verified and is deliberately not documented.
**Severity:** Minor
