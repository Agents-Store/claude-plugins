---
name: mcp-tools
description: Next.js DevTools MCP server tools and integration patterns. This skill should be used when the user asks about "next-devtools-mcp", "Next.js MCP tools", "MCP server for Next.js", "runtime diagnostics", "Next.js dev server MCP", or needs to set up or use the official Next.js MCP toolchain for AI-assisted development.
---

# Next.js DevTools MCP

`next-devtools-mcp` is Vercel's official MCP server for Next.js development. It provides runtime diagnostics, documentation access, browser automation, and upgrade tools. Next.js 16+ includes a built-in MCP endpoint at `/_next/mcp`.

## Setup

Add to project `.mcp.json`:

```json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    }
  }
}
```

Or install via CLI:

```bash
# Claude Code
claude mcp add next-devtools npx next-devtools-mcp@latest

# Cursor
# Go to Settings → MCP → New MCP Server

# VS Code
code --add-mcp '{"name":"next-devtools","command":"npx","args":["-y","next-devtools-mcp@latest"]}'
```

Requirements:
- Node.js v20.19+
- For runtime tools (`nextjs_index`, `nextjs_call`): Next.js 16+ with dev server running

## Tools Reference

### `init`

Initialize MCP context at the start of every Next.js session.

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| `project_path` | string | No | Current directory |

Call this first in every session. It sets up documentation requirements and lists available tools. Without initialization, the agent may not use official docs for Next.js queries.

### `nextjs_docs`

Search and retrieve official Next.js documentation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | `search` or `get` |
| `query` | string | For `search` | Keyword to search (e.g., `'metadata'`, `'middleware'`) |
| `path` | string | For `get` | Doc path from search results |
| `anchor` | string | No | Section anchor within the page |
| `routerType` | string | No | `app`, `pages`, or `all` (default: `all`) |

Two-step workflow:
1. Search for docs: `{ action: "search", query: "generateMetadata" }`
2. Fetch full content: `{ action: "get", path: "/docs/app/api-reference/functions/generate-metadata" }`

### `nextjs_index`

Discover all running Next.js 16+ dev servers and list their available MCP tools.

No parameters required. Returns JSON with discovered servers (port, PID, URL) and available tools.

Available runtime tools per server:
- `get_errors` — Current build, runtime, and type errors
- `get_logs` — Path to development log file
- `get_page_metadata` — Route and component metadata
- `get_project_metadata` — Project structure and config
- `get_routes` — All filesystem routes grouped by router type
- `get_server_action_by_id` — Look up Server Actions by ID

### `nextjs_call`

Execute a specific tool on a running Next.js dev server.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port` | number | Yes | Dev server port (from `nextjs_index`) |
| `toolName` | string | Yes | Tool name to invoke |
| `args` | object | No | Arguments for the tool |

### `browser_eval`

Automate browser testing with Playwright.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | `start`, `navigate`, `click`, `type`, `screenshot`, `evaluate`, `console_messages`, `close` |

Use for:
- Verifying pages after changes
- Detecting hydration errors visually
- Taking screenshots for comparison
- Capturing browser console errors

### `upgrade_nextjs_16`

Automated upgrade guide for migrating to Next.js 16.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | string | No | Path to Next.js project |

Runs the official Next.js codemod. Requires clean git state. Handles async API changes, config migrations, image defaults, and deprecated API removals.

### `enable_cache_components`

Set up and migrate to Cache Components in Next.js 16.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_path` | string | No | Path to Next.js project |

Runs pre-flight checks, enables configuration, starts dev server, detects errors, and applies automated fixes.

## Typical Workflow

1. **Start session** — Call `init` to set up context
2. **Start dev server** — `npm run dev`
3. **Discover servers** — Call `nextjs_index` to find running instances
4. **Check errors** — Call `nextjs_call` with `get_errors`
5. **Query docs** — Use `nextjs_docs` for best practices
6. **Verify changes** — Use `browser_eval` to screenshot and test

## Architecture

```
Coding Agent
      ↓
  next-devtools-mcp
      ↓
      ├─→ Next.js Dev Server (/_next/mcp) — Runtime diagnostics
      ├─→ Playwright MCP Server — Browser automation
      └─→ Knowledge Base & Tools — Docs, upgrades, setup
```

The MCP server bridges the agent to three systems: the running Next.js app, a Playwright instance, and the Next.js documentation API.

## Knowledge Base Resources

The MCP server provides on-demand knowledge base resources:

- **Cache Components** — 12 sections covering mechanics, public/private caches, invalidation, patterns
- **Next.js 16 migration** — Beta-to-stable migration guide with examples
- **Next.js fundamentals** — `'use client'` patterns and best practices

Resources are loaded on-demand to avoid overwhelming the context window.

## Auto-Initialize Tip

Add to your project `CLAUDE.md` to auto-initialize in every session:

```markdown
**When starting work on this Next.js project, ALWAYS call the `init` tool from
next-devtools-mcp FIRST to set up proper context and establish documentation
requirements. Do this automatically without being asked.**
```
