# n8n-provision

n8n instance provisioning plugin for the Agents Store. Discover workflows from the official template library (12,900+ templates), GitHub repositories, and community platforms, then analyze, import, and batch-deploy them to provision an n8n instance. Written for n8n 2.x (workflows are published, not activated; imported workflows stay drafts until the user publishes them).

## Relationship to Other n8n Plugins

| Plugin | Role | Focus |
|--------|------|-------|
| `n8n-dev` | dev | Knowledge for building and operating workflows — n8n 2.x patterns, expressions, validation, code nodes, MCP tools (external and native), REST API, CLI |
| **`n8n-provision`** | **provision** | **Discover and import existing workflows to provision an instance** |

The earlier `n8n` plugin was retired; `n8n-dev` replaces it.

## Skills

| Skill | Description |
|-------|-------------|
| `template-discovery` | Search the official n8n template library (12,900+ templates; n8n-mcp covers about 2,350 of them, `api.n8n.io` all) |
| `community-source-discovery` | Find workflows on GitHub repos and community platforms |
| `workflow-analysis` | Analyze workflow JSON before importing — complexity, credentials, security, nodes removed in n8n 2.0 and 3.0 |
| `single-workflow-import` | Import and deploy one workflow to an n8n instance |
| `batch-provisioning` | Provision an instance with multiple workflows in one session |
| `credential-planning` | Plan credential setup before importing workflows |
| `instance-readiness` | Assess instance health, capabilities and security before provisioning |
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

**n8n-provisioner** — Autonomous agent that discovers, analyzes, and deploys workflows. Handles multi-source search, batch provisioning, and credential planning. It declares no `tools:` allowlist, so it inherits every tool of the session, including the MCP tools of the n8n servers you connected.

## CONNECTORS Pattern

This plugin uses the CONNECTORS pattern (`~~capability` placeholders) for tool-name indirection. See `CONNECTORS.md` for the full mapping of capabilities to expected MCP tool providers. The plugin declares no MCP server of its own: connect `n8n-mcp-external` and/or `n8n-native-mcp` yourself.

## Workflow Sources

- **Official:** n8n.io template library — 12,900+ templates, free public API at `api.n8n.io`. The template database inside n8n-mcp holds about 2,350 of them (roughly 18%); templates it lacks (`Template <id> not found`) are fetched from `api.n8n.io` instead
- **GitHub:** Zie619/n8n-workflows (about 56.9k stars), enescingoz/awesome-n8n-templates (about 25.7k stars), and 4+ more repos
- **Community:** n8nworkflows.xyz, n8nflow.net, n8nfind.net (search only), n8nbasket.com (paid)

## Prerequisites

- n8n MCP server connected. Importing JSON workflows (templates from `api.n8n.io`, community JSON) and the credential, health, audit and autofix tools need `n8n-mcp-external` configured with `N8N_API_URL` and `N8N_API_KEY`; the native `n8n-native-mcp` server takes TypeScript SDK code, not JSON, and covers listing, credentials (read-only) and publishing
- An n8n API key from Settings > n8n API (a Label and an Expiration are required; an expired key answers 401)
- Web search tools available (Exa, Firecrawl, Jina, or Perplexity) for community source discovery
- `curl` available to the agent for the `api.n8n.io` template fallback
