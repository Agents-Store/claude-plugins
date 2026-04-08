---
description: Search across 30+ free community shadcn registries for UI components, blocks, and templates
argument-hint: <what-you-need>
allowed-tools: [Read, Bash, Grep, Glob]
---

# Search Components

Search for shadcn-compatible components across 30+ community registries.

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
7. If MCP servers are available (`shadcn` or `shadcn-community`), use them to search for more specific matches
