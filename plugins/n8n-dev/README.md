# n8n-dev

n8n workflow automation development plugin for Agents Store. Comprehensive knowledge base for building, debugging, and managing n8n workflows.

## Skills (13)

### Core Workflow Development
| Skill | Description |
|-------|-------------|
| **n8n-mcp-tools-expert** | External MCP tools guide — node search, validation, workflow CRUD, templates, credentials, audit |
| **n8n-native-mcp** | Native MCP tools guide — SDK-based workflow creation, execution, publishing |
| **n8n-workflow-patterns** | 5 proven architectural patterns (webhook, HTTP API, database, AI agent, scheduled) |
| **n8n-node-configuration** | Operation-aware node configuration with property dependencies |
| **n8n-validation-expert** | Validation error interpretation and fixing |

### Code & Expressions
| Skill | Description |
|-------|-------------|
| **n8n-expression-syntax** | Expression patterns, `{{}}` syntax, `$json`/`$node` variables |
| **n8n-code-javascript** | JavaScript Code node — `$input`, `$helpers`, error patterns |
| **n8n-code-python** | Python Code node — `_input`, standard library, limitations |

### API, CLI & Operations
| Skill | Description |
|-------|-------------|
| **api-reference** | REST API reference — 37 endpoints, curl examples, OpenAPI spec |
| **cli-recipes** | CLI commands — execute, export/import, license, user management |
| **setup** | MCP connection configuration and verification |
| **troubleshoot** | Common errors, diagnostics, and solutions |
| **examples** | End-to-end scenario walkthroughs |

## Agent

**n8n-developer** — Specialist agent for workflow building, debugging, and n8n operations.

## Prerequisites

This plugin provides knowledge only — no MCP servers are bundled. Configure n8n MCP servers at the project level:

### Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `N8N_API_URL` | External MCP | n8n instance URL |
| `N8N_API_KEY` | External MCP | API authentication key |
| `N8N_MCP_TOKEN` | Native MCP | MCP server token |

### MCP Servers

**External MCP** (recommended for development):
```json
{
  "n8n-mcp-external": {
    "command": "npx",
    "args": ["n8n-mcp"],
    "env": {
      "MCP_MODE": "stdio",
      "N8N_API_URL": "${N8N_API_URL}",
      "N8N_API_KEY": "${N8N_API_KEY}"
    }
  }
}
```

**Native MCP** (for execution and SDK workflows):
```json
{
  "n8n-native-mcp": {
    "type": "http",
    "url": "${N8N_API_URL}/mcp-server/http",
    "headers": {
      "Authorization": "Bearer ${N8N_MCP_TOKEN}"
    }
  }
}
```

## Credits

Core workflow development skills adapted from [n8n-skills](https://github.com/czlonkowski/n8n-skills) by Romuald Czlonkowski (MIT License).
