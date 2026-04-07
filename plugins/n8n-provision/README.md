# n8n-provision

n8n instance provisioning plugin for the Agents Store. Discover workflows from the official template library (9,166+ templates), GitHub repositories, and community platforms, then analyze, import, and batch-deploy them to provision an n8n instance.

## Relationship to Other n8n Plugins

| Plugin | Role | Focus |
|--------|------|-------|
| `n8n` | ops | Manage existing workflows — create, execute, list, debug via MCP |
| `n8n-dev` | dev | Knowledge for building workflows — patterns, expressions, validation, code nodes |
| **`n8n-provision`** | **provision** | **Discover and import existing workflows to provision an instance** |

## Skills

| Skill | Description |
|-------|-------------|
| `template-discovery` | Search the official n8n template library (9,166+ templates, 31 categories) |
| `community-source-discovery` | Find workflows on GitHub repos and community platforms |
| `workflow-analysis` | Analyze workflow JSON before importing — complexity, credentials, security |
| `single-workflow-import` | Import and deploy one workflow to an n8n instance |
| `batch-provisioning` | Provision an instance with multiple workflows in one session |
| `credential-planning` | Plan credential setup before importing workflows |
| `instance-readiness` | Assess instance health and readiness before provisioning |
| `troubleshoot` | Diagnose and fix common provisioning failures |
| `examples` | End-to-end provisioning scenario walkthroughs |

## Commands

| Command | Description |
|---------|-------------|
| `/n8n-provision:search-templates` | Search the official template library |
| `/n8n-provision:search-community` | Search GitHub and community sources |
| `/n8n-provision:deploy-template` | Deploy an official template to your instance |
| `/n8n-provision:analyze-workflow` | Analyze a workflow before importing |
| `/n8n-provision:provision-instance` | Batch-provision with a workflow suite |

## Agent

**n8n-provisioner** — Autonomous agent that discovers, analyzes, and deploys workflows. Handles multi-source search, batch provisioning, and credential planning.

## CONNECTORS Pattern

This plugin uses the CONNECTORS pattern (`~~capability` placeholders) for tool-name indirection. See `CONNECTORS.md` for the full mapping of capabilities to expected MCP tool providers.

## Workflow Sources

- **Official:** n8n.io template library — 9,166+ templates, free public API
- **GitHub:** Zie619/n8n-workflows (53.5k stars), enescingoz/awesome-n8n-templates (20.9k stars), and 4+ more repos
- **Community:** n8nworkflows.xyz, n8nfind.net, n8nflow.net, n8nbazar.ai, FlowEngine.cloud

## Prerequisites

- n8n MCP server connected (n8n-mcp-external or n8n-native-mcp)
- Web search tools available (Exa, Firecrawl, Jina, or Perplexity) for community source discovery
