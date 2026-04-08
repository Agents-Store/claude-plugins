---
name: mcp-tools
description: >
  Set up and use shadcn MCP servers for AI-assisted component discovery and installation. This skill should
  be used when the user asks about "shadcn MCP", "shadcn MCP server", "set up shadcn MCP for Claude",
  "component MCP tools", "Jpisnice shadcn MCP", "shadcn-ui-mcp-server", "AI component installation",
  or needs to configure MCP servers for shadcn/ui component work.
---

Two MCP servers enable AI-assisted shadcn/ui component discovery and installation: the official shadcn MCP and the Jpisnice community MCP server.

## Official shadcn MCP

The official MCP is built into the shadcn CLI (v3.0+).

### Setup

```bash
pnpm dlx shadcn@latest mcp init --client claude
```

This generates the MCP configuration for Claude Code automatically. For other clients:

```bash
# Cursor
pnpm dlx shadcn@latest mcp init --client cursor

# VS Code
pnpm dlx shadcn@latest mcp init --client vscode
```

### What It Enables

- Component resolution from any shadcn-compatible registry
- Theme management and preview
- Component search and installation
- Works with custom registries configured in `components.json`

## Jpisnice Community MCP Server

The `@jpisnice/shadcn-ui-mcp-server` provides more granular tools for component discovery.

### Setup for Claude Code

```bash
claude mcp add shadcn -- bunx -y @jpisnice/shadcn-ui-mcp-server
```

With a GitHub token for higher API rate limits (5000/hour vs 60/hour):

```bash
claude mcp add shadcn -- bunx -y @jpisnice/shadcn-ui-mcp-server --github-api-key ghp_YOUR_TOKEN
```

### Setup for Other Editors

Add to the project's `.mcp.json` or editor settings:

```json
{
  "mcpServers": {
    "shadcn": {
      "command": "bunx",
      "args": ["-y", "@jpisnice/shadcn-ui-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_YOUR_TOKEN"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list-components` | Browse all available components in the registry |
| `get-component-docs` | Get detailed docs, source code, and usage for a component |
| `install-component` | Generate installation command for a component |
| `list-blocks` | Browse pre-built templates (dashboards, forms, etc.) |
| `get-block-docs` | Get documentation for a block implementation |
| `install-blocks` | Generate installation command for blocks |

### Framework Selection

The Jpisnice server supports multiple frameworks:

```bash
# React (default)
bunx -y @jpisnice/shadcn-ui-mcp-server

# Svelte
bunx -y @jpisnice/shadcn-ui-mcp-server --framework svelte

# Vue
bunx -y @jpisnice/shadcn-ui-mcp-server --framework vue

# React Native
bunx -y @jpisnice/shadcn-ui-mcp-server --framework react-native
```

### React UI Library Selection

For React, choose between Radix UI (default) or Base UI primitives:

```bash
bunx -y @jpisnice/shadcn-ui-mcp-server --ui-library base
```

### Transport Modes

| Mode | Use Case | Command |
|------|----------|---------|
| stdio (default) | CLI, Claude Code | `bunx -y @jpisnice/shadcn-ui-mcp-server` |
| SSE | HTTP-based clients, remote servers | Set `MCP_TRANSPORT_MODE=sse` |
| dual | Both stdio and SSE simultaneously | Set `MCP_TRANSPORT_MODE=dual` |

SSE mode configuration:

```bash
MCP_TRANSPORT_MODE=sse MCP_PORT=7423 bunx -y @jpisnice/shadcn-ui-mcp-server
```

## Which MCP Server to Use

| Scenario | Recommendation |
|----------|----------------|
| Quick setup, standard shadcn/ui | Official MCP |
| Detailed component exploration | Jpisnice MCP |
| Custom/private registries | Official MCP |
| Multi-framework projects | Jpisnice MCP |
| shadcn studio premium components | Official MCP (works with registries in components.json) |
| Multi-registry search (30+ community registries) | Both (Official reads components.json registries; Jpisnice searches GitHub) |

Both servers can coexist. The official MCP integrates with `components.json` registries (including shadcn studio), while the Jpisnice server provides richer browsing tools from GitHub source.

## Workflow: AI-Assisted Component Installation

```
1. User describes UI need ("I need a login form")
     ↓
2. AI uses list-components/list-blocks to find relevant components
     ↓
3. AI uses get-component-docs to review options and dependencies
     ↓
4. AI uses install-component to generate the CLI command
     ↓
5. User runs the command (or AI runs via Bash)
     ↓
6. AI customizes the installed component for the user's needs
```

## Multi-Registry Search with MCP

When community registries are configured in `components.json`, the official shadcn MCP automatically discovers and searches them. This enables a combined workflow:

1. **Official MCP** resolves components from all configured registries (standard shadcn/ui + shadcn studio + 30+ community registries)
2. **Jpisnice MCP** provides deeper GitHub-based search across the shadcn ecosystem — component source code, demos, and block implementations

### Recommended Dual Setup for User Projects

```bash
# Official MCP (reads registries from components.json)
pnpm dlx shadcn@latest mcp init --client claude

# Community MCP (GitHub-based search, richer browsing)
claude mcp add shadcn-community -- npx -y @jpisnice/shadcn-ui-mcp-server
```

For a ready-to-use `.mcp.json` template with both servers, see the `component-search` skill's `references/mcp-config-template.json`.

### Adding Community Registries for MCP Search

The official MCP only searches registries listed in `components.json`. To unlock search across 30+ community registries:

1. Add registries to `components.json` (see `component-search` skill for the full list)
2. Or use the `/setup-registries --all` command to add all registries at once

## Rate Limiting

The Jpisnice MCP server uses GitHub's public API. Without a token, you get 60 requests/hour. With a GitHub Personal Access Token, you get 5000 requests/hour.

To create a token:
1. Go to GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens
2. Create a token with no special permissions (public repo access only)
3. Pass it via `--github-api-key` flag or `GITHUB_PERSONAL_ACCESS_TOKEN` env var

## What This Skill Does NOT Cover

- General Next.js MCP devtools -- see `nextjs-dev` plugin's `mcp-tools` skill
- Component installation details -- see `component-registry` skill
- shadcn/ui initialization -- see `setup` skill
- Community registry search and catalog -- see `component-search` skill
