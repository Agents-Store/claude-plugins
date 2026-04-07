---
description: Deploy an official n8n template to your instance
allowed-tools: ["Bash", "Read"]
argument-hint: <template-id> [--name <custom-name>] [--auto-fix]
---

# Deploy Template

Deploy an official n8n template to the connected n8n instance.

## Arguments
Format: `<template-id> [--name <custom-name>] [--auto-fix]`
- template-id: Numeric template ID from the n8n library (required)
- --name: Custom workflow name (default: use template name)
- --auto-fix: Enable auto-fix for minor validation issues

Parse from "$ARGUMENTS".

## Process

1. **Get template details** via `~~template_get` with the template ID at full detail level.

2. **Analyze the template:**
   - List all nodes and their types
   - Identify required credentials (services that need authentication)
   - Check for community nodes
   - Report complexity (node count, branching)

3. **Show analysis summary** and ask for confirmation before deploying.

4. **Deploy** via `~~template_deploy`:
   - Apply custom name if provided
   - Enable auto-fix if `--auto-fix` flag set
   - Workflow is imported as **inactive** by default

5. **Post-deploy report:**
   - Workflow ID and name
   - Credential setup checklist (list each credential type needed)
   - "Activate with `/n8n:activate-workflow <id>` after configuring credentials"

## Example Usage
```
/n8n-provision:deploy-template 2947
/n8n-provision:deploy-template 1234 --name "My Slack Notifier"
/n8n-provision:deploy-template 5678 --auto-fix
```
