# nextjs-provision

Next.js provisioning plugin for the Agents Store marketplace. Knowledge base for setting up shadcn/ui and shadcn studio in Next.js projects -- component installation, theme configuration, project scaffolding, MCP server integration, and multi-registry component search across 260+ registries from the official shadcn directory (ui.shadcn.com/r/registries.json).

## Type

Technology (Level 1) with MCP -- two stdio-based MCP servers for component search (official shadcn + Jpisnice community).

## Skills

| Skill | Description |
|-------|-------------|
| `setup` | Initialize shadcn/ui and shadcn studio in a Next.js project |
| `mcp-tools` | Set up shadcn MCP servers (official + Jpisnice community) |
| `component-registry` | Browse, search, install components/blocks from shadcn registries |
| `theme-configuration` | Configure themes, CSS variables, dark mode, custom brand colors |
| `project-scaffolding` | Templates, starter kits, component architecture patterns |
| `troubleshoot` | Debug shadcn setup issues, dependency conflicts, Tailwind config |
| `examples` | End-to-end setup walkthroughs (new project, adding to existing) |
| `component-search` | Search and install components from 260+ registries in the official shadcn directory |

## Commands

| Command | Description |
|---------|-------------|
| `/search-components` | Search across community registries for UI components |
| `/add-registries` | Fetch all 260+ registries from official endpoint and add to components.json |
| `/setup-registries` | Full project setup: registries + MCP + CLAUDE.md + shadcn skill |

## Agent

**nextjs-provisioner** -- Next.js UI provisioner for setting up component libraries, themes, and project architecture with shadcn/ui and shadcn studio.

## Prerequisites

- A Next.js project (13+ with App Router)
- Tailwind CSS 3.x or 4.x configured
- React 18/19; Base UI is the default component base since July 2026 (Radix and React Aria supported via `-b`)
- TypeScript (recommended)
- For shadcn studio premium: EMAIL and LICENSE_KEY in .env

## MCP Server Integration (Optional)

This plugin provides knowledge only -- it does NOT connect to any service. To add AI-assisted component discovery, install one of the shadcn MCP servers at the project level:

### Official shadcn MCP

```bash
pnpm dlx shadcn@latest mcp init --client claude
```

Supported clients: claude, cursor, vscode, codex, opencode.

### Community MCP (Jpisnice)

```bash
claude mcp add shadcn -- bunx -y @jpisnice/shadcn-ui-mcp-server
```

See the `mcp-tools` skill for detailed setup instructions.

## Community Registries

This plugin includes knowledge of the 260+ registries in the official shadcn directory:

- **Animation**: MagicUI, Aceternity UI, Animate UI, Cult UI, Motion Primitives
- **Extended UI**: COSS (@coss, formerly Origin UI), DiceUI, BaseCN, 8bitCN, BoldKit
- **Blocks**: BundUI, Blocks.so, Efferd, Creative Tim
- **E-Commerce**: Commercn (@commercn)
- **AI/Chat**: AI Elements, Assistant UI, Tool UI, AI Blocks
- **File Upload**: Better Upload
- **Editors/AI**: @kibo-ui, @plate (editor), @reui, @kokonutui, @intentui, @tailark and more — 267 total in the directory

Use the `component-search` skill or `/search-components` command to find and install components across all registries.

## Related

- [shadcn/ui](https://ui.shadcn.com/) -- The underlying component system
- [shadcn studio](https://shadcnstudio.com/) -- Premium components, blocks, and themes
- [nextjs-dev](../nextjs-dev/) -- Companion plugin for Next.js development patterns
- [shadcn-ui-mcp-server](https://github.com/Jpisnice/shadcn-ui-mcp-server) -- Community MCP server
