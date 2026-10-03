---
description: Search the official n8n template library for ready-made workflows
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: <query> [--category <name>] [--nodes <nodeTypes>] [--mode <keyword|by_nodes|by_task|by_metadata>]
---

# Search Templates

Search the n8n.io official template library (12,900+ templates) for workflows matching a query. n8n-mcp searches a local database of about 2,350 of them; when it returns nothing, the search continues against the public API at `api.n8n.io`.

## Arguments
Format: `<query> [--category <name>] [--nodes <nodeTypes>] [--mode <keyword|by_nodes|by_task|by_metadata>]`
- query: Search text (required)
- --category: Filter by category name (e.g., marketing, devops, AI). n8n-mcp: `by_metadata` with `category`; `api.n8n.io`: `category=<name>`
- --nodes: Search by node types used (comma-separated, e.g., Slack,GitHub; expanded to full types such as `n8n-nodes-base.slack`)
- --mode: Search mode — keyword (default), by_nodes, by_task (the closest value of the `task` list: ai_automation, data_sync, webhook_processing, email_automation, slack_integration, data_transformation, file_processing, scheduling, api_integration, database_operations), by_metadata (complexity, setup time, required service)

Parse from "$ARGUMENTS".

## Process

1. **Determine search mode** based on arguments:
   - Default or `--mode keyword`: use `~~template_search` with keyword mode
   - `--nodes` provided or `--mode by_nodes`: use `~~template_search` with by_nodes mode
   - `--mode by_task`: map the request to one `task` value and use `~~template_search` with by_task mode — free text is not accepted there; use keyword mode for free text
   - `--mode by_metadata` or `--category`: use `~~template_search` with by_metadata mode (`category`, `complexity`, `requiredService`)

2. **Execute search** via `~~template_search` with the query and any filters. If the n8n-mcp result is empty, repeat the search on `api.n8n.io` (`curl -s 'https://api.n8n.io/api/templates/search?rows=20&search=<query>'`; results are under `workflows`).

3. **Display results** in a table:
   - Template ID, name, node count, views, price (flag paid templates), description (truncated)
   - Sort by relevance (default from API)
   - Show total results count and current page

4. **Suggest next steps:**
   - "Use `/n8n-provision:deploy-template <id>` to deploy a template"
   - "Use `/n8n-provision:analyze-workflow <id>` to analyze before importing"

## Example Usage
```
/n8n-provision:search-templates "slack notifications"
/n8n-provision:search-templates "CRM sync" --category sales
/n8n-provision:search-templates --nodes Slack,GitHub,Webhook
/n8n-provision:search-templates "send email when form submitted" --mode by_task   # mapped to the email_automation task
```
