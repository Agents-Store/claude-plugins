# Learnings

## 2026-09-26 — CONNECTORS.md: reference to a renamed plugin

**Problem:** CONNECTORS.md pointed at the `deep-research` plugin for its fallback pattern; that plugin is now `deep-research-ops`.
**Fix:** Reference updated. Patch bump.
**Root cause:** Cross-plugin reference by name; the rename happened in another plugin.
**Severity:** Minor

## 2026-10-03 — n8n-provisioner agent, template-discovery, single-workflow-import: MCP tools cut off, template fallback, stale API shapes

**Problem:** The agent had a `tools:` allowlist (Read, Write, Edit, Grep, Glob, Bash), which removes every MCP tool, so it could not call n8n-mcp at all. `get_template` and `n8n_deploy_template` read the local n8n-mcp database (about 2,350 of 12,900 templates), so valid library templates such as 2947 answered "not found". TEMPLATE_API.md described the public API wrongly (category IDs, response keys, flat/wrapped endpoints swapped), the skills sent parameters the tools do not have (a detail-level argument, `id` instead of `templateId`, a tag list on deploy, an `active` flag on create), called a security audit a health check, and pointed at the retired `n8n` plugin, a missing GitHub repo and dead community sites.
**Fix:** Removed the allowlist. Template search/get fall back from n8n-mcp to `api.n8n.io` (curl); templates not in the local database are imported through `n8n_create_workflow` with only `name, nodes, connections, settings`. API shapes, parameter names, deploy options, tags (`addTag`), health (`n8n_health_check`) versus security audit (`n8n_audit_instance`), the n8n 2.x publish model, API-key wording, community-node installation, node deprecations (2.0 and 3.0), GitHub and community source data were rewritten from live checks. Minor bump.
**Root cause:** The plugin was written against n8n 1.x and a template database snapshot, with tool shapes recalled rather than read from `tools_documentation`; the agent allowlist was copied from a template without MCP in mind.
**Severity:** Critical
