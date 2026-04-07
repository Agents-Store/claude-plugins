---
description: Analyze a workflow JSON or template before importing
allowed-tools: ["Bash", "Read", "Grep"]
argument-hint: <template-id-or-url>
---

# Analyze Workflow

Analyze an n8n workflow before importing — check complexity, credentials, compatibility, and security.

## Arguments
Format: `<template-id-or-url>`
- Numeric ID: treated as an official template ID (fetched via `~~template_get`)
- URL: treated as a community source (fetched via `~~scrape`)

Parse from "$ARGUMENTS".

## Process

1. **Fetch the workflow:**
   - If numeric: use `~~template_get` with the ID
   - If URL: use `~~scrape` to read the page, extract the workflow JSON

2. **Run analysis** (follow `workflow-analysis` skill):
   - **Node inventory:** List all nodes, mark built-in vs community
   - **Topology:** Linear, branched, looped, error-handled
   - **Credentials:** List all required credential types and services
   - **Security scan:** Check for hardcoded values, open webhooks, code execution nodes
   - **Complexity score:** Simple / Medium / Complex
   - **Compatibility:** Deprecated nodes, version requirements

3. **Display analysis report** in structured format:
   ```
   Template: <name> (#<id>)
   Complexity: <Simple|Medium|Complex> (<node-count> nodes)
   Topology: <type>
   Credentials needed: <list>
   Community nodes: <list or "None">
   Security flags: <list or "None">
   Compatibility: <OK or issues>
   ```

4. **Recommend action:** Deploy, deploy with caution, or skip (with reason).

## Example Usage
```
/n8n-provision:analyze-workflow 2947
/n8n-provision:analyze-workflow https://github.com/Zie619/n8n-workflows/blob/main/workflows/1234.json
```
