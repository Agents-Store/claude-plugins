# Connectors

## How tool references work

Plugin files use `~~capability` as a placeholder for whatever tool handles that action. For example, `~~template_search` means "use any available n8n template search tool" — the agent tries providers in fallback order until one succeeds.

This plugin is **tool-agnostic** — it describes workflows in terms of actions (`~~template_search`, `~~template_deploy`, `~~search`) rather than specific tool names. The user's environment pre-configures MCP servers, but any server providing these capabilities works. The plugin declares no MCP server of its own: the tool names below are the bare names of the servers the user connected (`mcp__n8n-mcp-external__…`, `mcp__n8n-native-mcp__…`).

## FALLBACK Rule

Every action goes through ALL available providers for that category, one by one:
1. Try provider 1 — if it works, use the result
2. If error, "not found", empty result, rate limit, or timeout — try provider 2
3. Continue until one succeeds or all are exhausted
4. Only report "not found" when ALL providers failed

**Error from a provider = skip it, try the next one. Never stop at first failure.**

## Template library: two providers, different sizes

The official library at n8n.io holds about 12,900 templates (`totalWorkflows` of `api.n8n.io`). The template database **inside n8n-mcp holds about 2,350** of them (roughly 18%). `get_template`, `search_templates` and `n8n_deploy_template` all read that local database, so a template that exists on n8n.io can answer `Template <id> not found` — for example `get_template({templateId: 2947})`. That answer means "not in the local database", not "no such template".

| Provider | Covers | Reach it with |
|----------|--------|---------------|
| 1. n8n-mcp-external (local database) | about 2,350 templates, fast, metadata filters | `search_templates`, `get_template`, `n8n_deploy_template` |
| 2. Public template API `api.n8n.io` (full library) | about 12,900 templates, no authentication | Bash `curl` — see `skills/template-discovery/references/TEMPLATE_API.md` |

The deploy tool has no API fallback of its own. When provider 1 answers "not found", fetch the workflow from `api.n8n.io`, keep only `name`, `nodes`, `connections` and `settings`, and create it with `~~workflow_create` (see `single-workflow-import`, Path 1b).

## n8n Instance Connectors

These connectors interact with the user's n8n instance. Most have a single primary provider — the indirection preserves flexibility if the user has different MCP server names.

| Category | Placeholder | Expected Providers | Notes |
|----------|-------------|-------------------|-------|
| Template search | `~~template_search` | 1. n8n-mcp-external `search_templates` (local database); 2. Bash `curl` to `api.n8n.io/api/templates/search` | 5 modes in provider 1: keyword, by_nodes, by_task, by_metadata, patterns. Fall through to provider 2 on zero results or no relevant match (keyword mode is loose) |
| Template details | `~~template_get` | 1. n8n-mcp-external `get_template` (`templateId`, `mode`: `nodes_only` / `structure` / `full`); 2. Bash `curl` to `api.n8n.io/api/workflows/templates/<id>` | "Template … not found" = go to provider 2 |
| Template deploy | `~~template_deploy` | 1. n8n-mcp-external `n8n_deploy_template` (`templateId`, `name`, `autoFix`, `autoUpgradeVersions`, `stripCredentials`); 2. fetch via `~~template_get` provider 2, then `~~workflow_create` | Provider 1 reads the local database too. The new workflow is never published |
| Workflow create | `~~workflow_create` | n8n-mcp-external `n8n_create_workflow` (`name`, `nodes`, `connections`, `settings`, `projectId`, `parentFolderId`) | The only provider that takes workflow **JSON**. Native `create_workflow_from_code` takes TypeScript SDK code, not JSON |
| Workflow validate | `~~workflow_validate` | Before import (JSON in hand): n8n-mcp-external `validate_workflow({workflow: {nodes, connections}})`. After import (workflow on the instance): `n8n_validate_workflow({id})` | Native `validate_workflow` checks SDK code, not JSON — not a provider here. Always validate before deploying |
| Workflow autofix | `~~workflow_autofix` | n8n-mcp-external `n8n_autofix_workflow({id})` | Preview first (`applyFixes: false`, the default), apply only after review. Run it on the imported workflow: library templates often carry nodes that n8n 3.0 removes |
| Workflow list | `~~workflow_list` | n8n-mcp-external `n8n_list_workflows`, n8n-native-mcp `search_workflows` | Inventory + conflict detection. Filter by tag with `tags: [...]` |
| Workflow edit | `~~workflow_update` | n8n-mcp-external `n8n_update_partial_workflow` | Operations used here: `addTag`, `moveToFolder`, `activateWorkflow` |
| Workflow publish | `~~workflow_publish` | n8n-mcp-external `n8n_update_partial_workflow` with operation `activateWorkflow` (publishes on n8n 2.x), n8n-native-mcp `publish_workflow` | Only on explicit user request. Needs the `workflow:activate` scope and the `workflow:publish` permission, otherwise `PUBLISH_FORBIDDEN` (n8n 2.39+) |
| Credential manage | `~~credential_manage` | n8n-mcp-external `n8n_manage_credentials` (actions `list`, `get`, `getSchema`, `create`, `update`, `delete`), n8n-native-mcp `list_credentials` (read-only) | List existing, read schemas, create non-OAuth credentials. OAuth2 needs a browser consent |
| Folders and tags | `~~workflow_organize` | n8n-mcp-external `n8n_manage_folders`, `n8n_list_catalog({kind: "tags" \| "projects"})` | Folders need n8n 2.19+ and a registered (free) Community licence; folder placement is write-only |
| Instance health | `~~instance_health` | n8n-mcp-external `n8n_health_check` (`mode`: `status` / `diagnostic`) | Pre-flight check. Returns `status`, `instanceId`, `features`, `mcpVersion`, `performance.responseTimeMs` — not uptime, queue or database metrics, and usually no n8n version |
| Instance security audit | `~~instance_audit` | n8n-mcp-external `n8n_audit_instance` | **Security** audit (credentials, database, nodes, instance, filesystem, plus hardcoded secrets, unauthenticated webhooks, error handling, data retention). Not a health check |
| Data tables | `~~datatable_manage` | n8n-mcp-external `n8n_manage_datatable` | Templates that use Data Tables need the table to exist before import |

## Web Discovery Connectors

These connectors search the web for n8n workflows beyond the official template library. They follow the same fallback pattern as `deep-research-ops`.

| Category | Placeholder | Included Providers | Other Options |
|----------|-------------|-------------------|---------------|
| Web search | `~~search` | Exa, Perplexity, Jina, Firecrawl | Tavily, Brave Search |
| Scrape / read page | `~~scrape` | Jina, Firecrawl | Browserbase |

## General workflow

```
DISCOVERING WORKFLOWS:

Step 1: TEMPLATE SEARCH — search the official n8n library
  → Use ~~template_search with the user's query (local database first, then api.n8n.io)
  → Review results, check relevance, quality and price (skip paid templates unless the user agrees)

Step 2: COMMUNITY SEARCH — if official library insufficient
  → Use ~~search on every available provider, targeting GitHub repos and community sites
  → First success = take the URLs

Step 3: FETCH DETAILS — read workflow content
  → For official templates: use ~~template_get (local database first, then api.n8n.io)
  → For community sources: use ~~scrape to read the page/raw JSON

IMPORTING WORKFLOWS:

Step 4: VALIDATE — check workflow before import
  → Use ~~workflow_validate on the workflow JSON (validate_workflow, not n8n_validate_workflow)
  → Fix any errors flagged

Step 5: DEPLOY — import to the n8n instance
  → Template in the local database: use ~~template_deploy (handles auto-fix)
  → Template only on api.n8n.io, or community JSON: use ~~workflow_create
  → Run ~~workflow_autofix in preview mode on the new workflow, apply after review
  → Verify with ~~workflow_list

PUBLISHING (only when the user asks):

Step 6: PUBLISH — make the workflow live
  → Credentials linked, manual test passed, then ~~workflow_publish
```
