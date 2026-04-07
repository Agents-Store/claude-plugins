---
description: Search the official n8n template library for ready-made workflows
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: <query> [--category <name>] [--nodes <nodeTypes>] [--mode <keyword|by_nodes|by_task>]
---

# Search Templates

Search the n8n.io official template library (9,166+ templates) for workflows matching a query.

## Arguments
Format: `<query> [--category <name>] [--nodes <nodeTypes>] [--mode <keyword|by_nodes|by_task>]`
- query: Search text (required)
- --category: Filter by category name (e.g., marketing, devops, AI)
- --nodes: Search by node types used (comma-separated, e.g., Slack,GitHub)
- --mode: Search mode — keyword (default), by_nodes, by_task

Parse from "$ARGUMENTS".

## Process

1. **Determine search mode** based on arguments:
   - Default or `--mode keyword`: use `~~template_search` with keyword mode
   - `--nodes` provided or `--mode by_nodes`: use `~~template_search` with by_nodes mode
   - `--mode by_task`: use `~~template_search` with by_task mode (natural language)

2. **Execute search** via `~~template_search` with the query and any filters.

3. **Display results** in a table:
   - Template ID, name, node count, total views, description (truncated)
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
/n8n-provision:search-templates "send email when form submitted" --mode by_task
```
