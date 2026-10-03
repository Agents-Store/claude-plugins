# nextjs-provision

Next.js provisioning plugin for the Agents Store marketplace. Knowledge base for setting up shadcn/ui and shadcn studio in Next.js projects -- component installation, theme configuration, project scaffolding, MCP server integration, and multi-registry component search across the 400+ registries (418 on 2026-10-02, with health status) of the official shadcn directory (ui.shadcn.com/r/registries.json).

## Type

Technology (Level 1) with MCP -- one stdio-based MCP server for component search: the official shadcn MCP (`npx shadcn@latest mcp`).

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Initialize shadcn/ui and shadcn studio in a Next.js project |
| `mcp-tools` | Set up and use the official shadcn MCP server |
| `component-registry` | Browse, search, install components/blocks from shadcn registries |
| `theme-configuration` | Configure themes, CSS variables, dark mode, custom brand colors |
| `project-scaffolding` | Templates, starter kits, component architecture patterns |
| `troubleshoot` | Debug shadcn setup issues, dependency conflicts, Tailwind config |
| `examples` | End-to-end setup walkthroughs (new project, adding to existing) |
| `component-search` | Search and install components from the 400+ registries in the official shadcn directory (health-aware) |

## Commands

| Command | Description |
|---------|-------------|
| `/search-components` | Search across community registries for UI components |
| `/add-registries` | Fetch the registries from the official endpoint (skipping unavailable/hidden ones) and add to components.json |
| `/setup-registries` | Full project setup: registries + MCP + CLAUDE.md + shadcn skill |

## Agent

**nextjs-provisioner** -- Next.js UI provisioner for setting up component libraries, themes, and project architecture with shadcn/ui and shadcn studio.

## Prerequisites

- A Next.js project (13+ with App Router)
- Tailwind CSS 3.x or 4.x configured (the `cn` package that `init` installs since shadcn CLI 4.21 supports Tailwind v4 only; v3 projects stay on `tailwind-merge` v2)
- React 18/19; Base UI is the default component base since July 2026 (Radix and React Aria supported via `-b`)
- TypeScript (recommended)
- For shadcn studio premium: EMAIL and LICENSE_KEY in .env

## MCP Server

The plugin's `.mcp.json` declares one server, the official shadcn MCP (`npx shadcn@latest mcp`). It searches the registries listed in the project's `components.json` and exposes seven tools: `get_project_registries`, `list_items_in_registries`, `search_items_in_registries`, `view_items_in_registries`, `get_item_examples_from_registries`, `get_add_command_for_items`, `get_audit_checklist` (named `mcp__plugin_nextjs-provision_shadcn__<tool>` through this plugin).

To use it in a project without the plugin:

```bash
pnpm dlx shadcn@latest mcp init --client claude
```

Supported clients: claude, cursor, vscode, codex, opencode.

The community server `@jpisnice/shadcn-ui-mcp-server` shipped up to 1.2.x was removed in 1.3.0 (it returns Radix code on Base UI projects and fails `get_component_metadata`). See the `mcp-tools` skill.

## Community Registries

This plugin includes knowledge of the registries in the official shadcn directory (`unavailable` and hidden ones excluded, `degraded` ones flagged):

- **Animation**: MagicUI, Aceternity UI (degraded), Animate UI, Cult UI, Motion Primitives
- **Extended UI**: COSS (@coss, formerly Origin UI), DiceUI, BaseCN, 8bitCN, BoldKit
- **Blocks**: BundUI, Blocks.so, Efferd (degraded)
- **E-Commerce**: Commercn (@commercn)
- **AI/Chat**: AI Elements, Assistant UI, Tool UI
- **File Upload**: Better Upload
- **Editors/AI**: @kibo-ui, @plate (editor), @reui, @kokonutui, @intentui, @tailark (degraded) and more — 418 in the directory on 2026-10-02

Use the `component-search` skill or `/search-components` command to find and install components across all registries.

## Related

- [shadcn/ui](https://ui.shadcn.com/) -- The underlying component system
- [shadcn studio](https://shadcnstudio.com/) -- Premium components, blocks, and themes
- [nextjs-dev](../nextjs-dev/) -- Companion plugin for Next.js development patterns
