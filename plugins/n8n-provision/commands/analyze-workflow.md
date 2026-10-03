---
description: Analyze a workflow JSON or template before importing
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: <template-id-or-url>
---

# Analyze Workflow

Analyze an n8n workflow before importing — check complexity, credentials, compatibility, and security.

## Arguments
Format: `<template-id-or-url>`
- Numeric ID: treated as an official template ID (fetched via `~~template_get`; when n8n-mcp answers `Template <id> not found`, fetched from `api.n8n.io` — see `template-discovery`)
- URL: treated as a community source (fetched via `~~scrape`)

Parse from "$ARGUMENTS".

## Process

1. **Fetch the workflow:**
   - If numeric: use `~~template_get` with the ID; on "not found" fetch `https://api.n8n.io/api/workflows/templates/<id>` and take `.workflow`
   - Look up the price: only `api.n8n.io` search items carry `price`/`purchaseUrl`. Search the template title (`.name` of the wrapper) at `https://api.n8n.io/api/templates/search?rows=20&search=<url-encoded title>` and match the item on `id` (paid = `purchaseUrl` set or `price` > 0; missing `price` = free; no match = "price unknown")
   - If URL: use `~~scrape` to read the page, extract the workflow JSON

2. **Run analysis** (follow `workflow-analysis` skill):
   - **Node inventory:** List all nodes, mark built-in vs community
   - **Topology:** Linear, branched, looped, error-handled
   - **Credentials:** List all required credential types and services
   - **Security scan:** Check for hardcoded values, open webhooks, code execution nodes
   - **Complexity score:** Simple / Medium / Complex
   - **Compatibility:** Nodes switched off in n8n 2.0, nodes removed in n8n 3.0, AI Agent v1, version requirements

3. **Display analysis report** in structured format:
   ```
   Template: <name> (#<id>)
   Complexity: <Simple|Medium|Complex> (<node-count> nodes)
   Topology: <type>
   Credentials needed: <list>
   Community nodes: <list or "None">
   Security flags: <list or "None">
   Compatibility: <OK or issues>
   Price: <Free | Paid (price, purchaseUrl) | Unknown — no search match>
   ```

4. **Recommend action:** Deploy, deploy with caution, or skip (with reason).

## Example Usage
```
/n8n-provision:analyze-workflow 2947
/n8n-provision:analyze-workflow https://github.com/Zie619/n8n-workflows/blob/main/workflows/Telegram/0001_Telegram_Schedule_Automation_Scheduled.json
```
