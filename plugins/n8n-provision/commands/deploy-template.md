---
description: Deploy an official n8n template to your instance
allowed-tools: ["Bash", "Read"]
argument-hint: <template-id> [--name <custom-name>] [--no-auto-fix] [--keep-versions]
---

# Deploy Template

Deploy an official n8n template to the connected n8n instance. The workflow arrives as an unpublished draft.

## Arguments
Format: `<template-id> [--name <custom-name>] [--no-auto-fix] [--keep-versions]`
- template-id: Numeric template ID from the n8n library (required)
- --name: Custom workflow name (default: use template name)
- --no-auto-fix: Turn auto-fix off (`autoFix: false`). Auto-fix is **on** by default; it repairs expression format and `typeVersion` problems
- --keep-versions: Keep the template's node versions (`autoUpgradeVersions: false`). By default nodes are upgraded to the newest supported `typeVersion`

Parse from "$ARGUMENTS".

## Process

1. **Get template details** via `~~template_get` with the template ID at full detail level.
   - n8n-mcp `get_template` reads a local database of about 2,350 of the 12,900 library templates. If it answers `Template <id> not found`, fetch the template from the public API instead: `curl -s https://api.n8n.io/api/workflows/templates/<id>` (the workflow JSON is `.workflow`). HTTP 404 there means the template does not exist.

2. **Analyze the template:**
   - List all nodes and their types
   - Identify required credentials (services that need authentication)
   - Check for community nodes and for nodes that n8n 3.0 removes (see `workflow-analysis`)
   - Check the price **by ID lookup**: neither `get_template` nor the by-ID `api.n8n.io` endpoints carry `price`/`purchaseUrl`, only search items do. Fetch the title (`curl -s https://api.n8n.io/api/workflows/templates/<id>`, field `.name`), search it (`curl -s "https://api.n8n.io/api/templates/search?rows=20&search=<url-encoded title>"`) and match the item on `id`. `purchaseUrl` non-null or `price` > 0 = paid (a missing `price` = free) — stop and ask the user. If no search item matches the ID, say so and ask before importing; do not assume free
   - Report complexity (node count, branching)

3. **Show analysis summary** and ask for confirmation before deploying.

4. **Deploy:**
   - Template found in the local database: `~~template_deploy` (`n8n_deploy_template`). Apply the custom name if provided; pass `autoFix: false` for `--no-auto-fix` and `autoUpgradeVersions: false` for `--keep-versions`
   - Template fetched from `api.n8n.io`: validate with `~~workflow_validate`, then `~~workflow_create` with only `name`, `nodes`, `connections` and `settings` (see `single-workflow-import`, Path 1b). Unless `--no-auto-fix` is set, preview `~~workflow_autofix` and apply it after review
   - The workflow is always created **unpublished**

5. **Post-deploy report:**
   - Workflow ID and name
   - Credential setup checklist (list each credential type needed — `requiredCredentials` in the deploy result, or collected from the node `credentials` blocks)
   - Auto-fix result (`autoFixStatus`, `fixesApplied`)
   - "The workflow is a draft. Link credentials and run a manual test, then publish it — in the editor (Publish button), with `publish_workflow` in the native MCP, or with `n8n_update_partial_workflow` and operation `activateWorkflow`. Over the REST API: `POST /api/v1/workflows/<id>/publish`. Publishing needs the `workflow:activate` scope and the `workflow:publish` permission."

Do not publish unless the user asks.

## Example Usage
```
/n8n-provision:deploy-template 2947
/n8n-provision:deploy-template 1234 --name "My Slack Notifier"
/n8n-provision:deploy-template 5678 --keep-versions
```
