# nextjs-provision

Next.js provisioning plugin for the Agents Store marketplace. Knowledge base for setting up shadcn/ui and shadcn studio in Next.js projects -- component installation, theme configuration, project scaffolding, and MCP server integration.

## Type

Technology (Level 1) -- knowledge-only, no MCP server bundled.

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

## Agent

**nextjs-provisioner** -- Next.js UI provisioner for setting up component libraries, themes, and project architecture with shadcn/ui and shadcn studio.

## Prerequisites

- A Next.js project (13+ with App Router)
- Tailwind CSS 3.x or 4.x configured
- TypeScript (recommended)
- For shadcn studio premium: EMAIL and LICENSE_KEY in .env

## MCP Server Integration (Optional)

This plugin provides knowledge only -- it does NOT connect to any service. To add AI-assisted component discovery, install one of the shadcn MCP servers at the project level:

### Official shadcn MCP

```bash
pnpm dlx shadcn@latest mcp init --client claude
```

### Community MCP (Jpisnice)

```bash
claude mcp add shadcn -- bunx -y @jpisnice/shadcn-ui-mcp-server
```

See the `mcp-tools` skill for detailed setup instructions.

## Related

- [shadcn/ui](https://ui.shadcn.com/) -- The underlying component system
- [shadcn studio](https://shadcnstudio.com/) -- Premium components, blocks, and themes
- [nextjs-dev](../nextjs-dev/) -- Companion plugin for Next.js development patterns
- [shadcn-ui-mcp-server](https://github.com/Jpisnice/shadcn-ui-mcp-server) -- Community MCP server
