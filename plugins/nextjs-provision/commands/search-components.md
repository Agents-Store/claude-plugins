---
description: Search across 260+ shadcn registries for UI components, blocks, and templates
argument-hint: <what-you-need>
allowed-tools: [Read, Bash, Grep, Glob]
---

# Search Components

Search for shadcn-compatible components across the 260+ registries in the official directory.

## Instructions

1. Read the skill at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/SKILL.md`
2. Read the registry reference at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/community-registries.md`
3. Parse the user's search query from "$ARGUMENTS" (e.g., "animated button", "date range picker", "chat component", "pricing section")
4. Identify the most relevant category: animation, extended UI, blocks, e-commerce, AI, file upload, other
5. Present matching registries and components with install commands:

```
## Results for "$ARGUMENTS"

### Recommended registries:
- **@registryname** — description
  Install: `npx shadcn@latest add @registryname/component`

### Also check:
- **@registryname2** — description
```

6. Check if the user's project has `components.json` — if registries are not configured, suggest running `/setup-registries` first
7. If MCP servers are available, use them for more specific matches:
   - `shadcn` (official) — searches across all registries configured in `components.json`
   - `shadcn-community` (Jpisnice) — use `list_components` / `get_component` / `get_component_demo` / `list_blocks` / `get_block` for GitHub-based browsing
8. Without MCP, suggest the CLI's server-side search as a fallback: `npx shadcn@latest search @registry -q "<term>"`
