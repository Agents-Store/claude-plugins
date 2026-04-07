# Connectors

## How tool references work

Plugin files use `~~capability` as a placeholder for whatever tool handles that action. For example, `~~template_search` means "use any available n8n template search tool" — the agent tries providers in fallback order until one succeeds.

This plugin is **tool-agnostic** — it describes workflows in terms of actions (`~~template_search`, `~~template_deploy`, `~~search`) rather than specific tool names. The user's environment pre-configures MCP servers, but any server providing these capabilities works.

## FALLBACK Rule

Every action goes through ALL available providers for that category, one by one:
1. Try provider 1 — if it works, use the result
2. If error, empty result, rate limit, or timeout — try provider 2
3. Continue until one succeeds or all are exhausted
4. Only report "not found" when ALL providers failed

**Error from a provider = skip it, try the next one. Never stop at first failure.**

## n8n Instance Connectors

These connectors interact with the user's n8n instance. Most have a single primary provider — the indirection preserves flexibility if the user has different MCP server names.

| Category | Placeholder | Expected Providers | Notes |
|----------|-------------|-------------------|-------|
| Template search | `~~template_search` | n8n-mcp-external `search_templates` | 5 search modes: keyword, by_nodes, by_task, by_metadata, patterns |
| Template details | `~~template_get` | n8n-mcp-external `get_template` | 3 detail levels |
| Template deploy | `~~template_deploy` | n8n-mcp-external `n8n_deploy_template` | Auto-fix + credential stripping |
| Workflow create | `~~workflow_create` | n8n-mcp-external `n8n_create_workflow`, n8n-native-mcp `create_workflow_from_code` | Use for community JSON not from template library |
| Workflow validate | `~~workflow_validate` | n8n-mcp-external `n8n_validate_workflow`, n8n-native-mcp `validate_workflow` | Always validate before deploying |
| Workflow list | `~~workflow_list` | n8n-mcp-external `n8n_list_workflows`, n8n-native-mcp `search_workflows` | Inventory + conflict detection |
| Credential manage | `~~credential_manage` | n8n-mcp-external `n8n_manage_credentials` | List existing, check schemas |
| Instance audit | `~~instance_audit` | n8n-mcp-external `n8n_audit_instance` | Health check before provisioning |

## Web Discovery Connectors

These connectors search the web for n8n workflows beyond the official template library. They follow the same fallback pattern as `deep-research`.

| Category | Placeholder | Included Providers | Other Options |
|----------|-------------|-------------------|---------------|
| Web search | `~~search` | Exa, Perplexity, Jina, Firecrawl | Tavily, Brave Search |
| Scrape / read page | `~~scrape` | Jina, Firecrawl | Browserbase |

## General workflow

```
DISCOVERING WORKFLOWS:

Step 1: TEMPLATE SEARCH — search the official n8n library
  → Use ~~template_search with the user's query
  → Review results, check relevance and quality

Step 2: COMMUNITY SEARCH — if official library insufficient
  → Use ~~search on every available provider, targeting GitHub repos and community sites
  → First success = take the URLs

Step 3: FETCH DETAILS — read workflow content
  → For official templates: use ~~template_get
  → For community sources: use ~~scrape to read the page/raw JSON

IMPORTING WORKFLOWS:

Step 4: VALIDATE — check workflow before import
  → Use ~~workflow_validate on the workflow JSON
  → Fix any errors flagged

Step 5: DEPLOY — import to the n8n instance
  → For official templates: use ~~template_deploy (handles auto-fix)
  → For community JSON: use ~~workflow_create
  → Verify with ~~workflow_list
```
