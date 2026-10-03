---
description: Search across the shadcn registry directory (400+ registries) for UI components, blocks, and templates
argument-hint: <what-you-need>
allowed-tools: [Read, Bash, Grep, Glob, mcp__plugin_nextjs-provision_shadcn__search_items_in_registries, mcp__plugin_nextjs-provision_shadcn__view_items_in_registries, mcp__plugin_nextjs-provision_shadcn__get_add_command_for_items]
---

# Search Components

Search for shadcn-compatible components across the registries in the official directory (418 on 2026-10-02).

## Instructions

1. Read the skill at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/SKILL.md`
2. Read the registry reference at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/community-registries.md`
3. Parse the user's search query from "$ARGUMENTS" (e.g., "animated button", "date range picker", "chat component", "pricing section")
4. Identify the most relevant category: animation, extended UI, blocks, e-commerce, AI, file upload, other
5. Present matching registries and components with install commands. Check each registry's `health.status` in `https://ui.shadcn.com/r/registries.json`: never recommend an `unavailable` or hidden one, and flag `degraded` ones:

```
## Results for "$ARGUMENTS"

### Recommended registries:
- **@registryname** — description
  Install: `npx shadcn@latest add @registryname/component`

### Also check:
- **@registryname2** — description
```

6. Check if the user's project has `components.json` — if registries are not configured, suggest running `/setup-registries` first
7. If the official `shadcn` MCP server is available, use it for more specific matches — it searches all registries configured in `components.json`:
   - `mcp__plugin_nextjs-provision_shadcn__search_items_in_registries` — fuzzy search (its printed `Add command` is broken in shadcn 4.21.1 — do not copy it)
   - `mcp__plugin_nextjs-provision_shadcn__view_items_in_registries` — read an item's files before installing
   - `mcp__plugin_nextjs-provision_shadcn__get_add_command_for_items` — the correct `npx shadcn@latest add @registry/item` command
8. Without the MCP, use the CLI: `npx shadcn@latest search @registry -q "<term>"` and `npx shadcn@latest view @registry/item`
