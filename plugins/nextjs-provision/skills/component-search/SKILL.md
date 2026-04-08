---
name: component-search
description: >
  Search and install UI components from 30+ free community shadcn registries. This skill should be used when
  the user asks to "search for shadcn components", "find a calendar component", "browse community registries",
  "install from magicui", "what shadcn registries are available", "add animated components", "search for a
  date picker", "find UI blocks for landing page", "install from aceternity", "what community components
  exist", or needs to discover and install components from community registries beyond the standard shadcn/ui
  and shadcn studio registries.
---

## How Community Registries Work

shadcn v4 supports custom registries via the `"registries"` field in `components.json`. Any registry that implements the shadcn registry protocol can be added. Over 170 registries exist — 30+ provide free UI components, blocks, and templates.

The CLI can install from any registry without configuration:

```bash
npx shadcn@latest add @magicui/shimmer-button
```

But the **official shadcn MCP server** only searches registries listed in `components.json`. To enable MCP-assisted search across community registries, they must be added to the config.

## Search Workflow

```
1. User describes what they need ("animated button", "pricing section", "chat component")
     ↓
2. Identify the category: animation, extended UI, blocks, e-commerce, AI, etc.
     ↓
3. Consult references/community-registries.md for matching registries
     ↓
4. Check user's components.json — is the registry already configured?
     ↓
5a. If configured → use MCP tools to search, or install directly via CLI
5b. If not configured → add registry to components.json first
     ↓
6. Install: npx shadcn@latest add @[registry]/[component]
     ↓
7. Verify the component renders correctly
```

## Adding a Registry to components.json

Open `components.json` and add entries to the `"registries"` field:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "registries": {
    "magicui": {
      "url": "https://magicui.design/r"
    },
    "aceternity": {
      "url": "https://ui.aceternity.com/r"
    }
  }
}
```

Merge with existing registries — do not overwrite the `"registries"` object, add to it.

To add all 30+ community registries at once, use the `/setup-registries --all` command.

## Installing from a Community Registry

```bash
# Install a single component
npx shadcn@latest add @magicui/shimmer-button

# Install multiple components from the same registry
npx shadcn@latest add @magicui/shimmer-button @magicui/animated-beam @magicui/globe

# Install from different registries in one command
npx shadcn@latest add @magicui/shimmer-button @aceternity/moving-border

# Force overwrite existing files
npx shadcn@latest add @magicui/shimmer-button --overwrite
```

The CLI auto-resolves registry URLs. Even without `components.json` configuration, the CLI can install from any known registry by name.

## MCP-Assisted Search

Two MCP servers are configured in this plugin's `.mcp.json`:

| Server | What It Searches | Best For |
|--------|-----------------|----------|
| `shadcn` (official) | All registries in `components.json` | Finding components across configured registries |
| `shadcn-community` (Jpisnice) | shadcn/ui GitHub repo | Browsing component source code, demos, block implementations |

### Dual search strategy

1. **Official MCP** searches all configured registries — add community registries to `components.json` to expand its scope
2. **Jpisnice MCP** searches the shadcn/ui GitHub repository for component source, demos, and blocks — useful for understanding how components work before installing

For projects that want both MCPs, copy the template from `references/mcp-config-template.json` to the project's `.mcp.json`.

### Jpisnice MCP rate limits

Without a GitHub token: 60 requests/hour. With a token: 5000/hour.

To add a token:

```bash
claude mcp add shadcn-community -- npx -y @jpisnice/shadcn-ui-mcp-server --github-api-key ghp_YOUR_TOKEN
```

Or set `GITHUB_PERSONAL_ACCESS_TOKEN` in the MCP server's env config. Create a fine-grained token with no special permissions (public repo access only).

## Registry Categories

| Category | Registries | Component Types |
|----------|-----------|-----------------|
| Animation & Motion | @magicui, @aceternity, @animate-ui, @cult-ui, @motion-primitives, @chamaac | Animated buttons, scroll effects, parallax, globe, beams |
| Extended UI | @originui, @diceui, @basecn, @8bitcn, @boldkit, @8starlabs-ui, @cardcn | Extra components, retro/pixel style, card variants, dice rolls |
| Blocks & Sections | @bundui, @blocks-so, @efferd, @doras-ui, @creative-tim | Landing page sections, marketing blocks, dashboards |
| E-Commerce | @commerce-ui | Product cards, cart, checkout, reviews |
| AI Components | @ai-elements, @assistant-ui, @tool-ui, @ai-blocks | Chat bubbles, prompt inputs, AI response streams, LLM UIs |
| File Upload | @better-upload | Upload components, drag-and-drop, progress indicators |
| Other | @arc, @abui, @aevr, @unlumen-ui, @einui, @billingsdk | Specialized UI, billing forms, misc |

See `references/community-registries.md` for the full list with URLs and descriptions.

Full directory (170+ registries): https://ui.shadcn.com/docs/directory

## CLAUDE.md Section for User Projects

When setting up a project with community registries, add the section from `references/claude-md-section.md` to the project's CLAUDE.md. This ensures Claude always searches registries before building components from scratch.

## Verifying a Registry Works

Test that a registry URL is correct by installing a known component:

```bash
# Install a component from the registry
npx shadcn@latest add @magicui/shimmer-button

# If the install succeeds, the registry URL is correct
# If it fails, check the registry's documentation for the correct URL pattern
```

The standard URL convention is `https://domain.com/r/{name}` but some registries may differ. The CLI auto-resolves known registry names — if `@registryname/component` works, the URL is valid.

## What This Skill Does NOT Cover

- Standard shadcn/ui and shadcn studio components — see `component-registry` skill
- Initial shadcn/ui project setup — see `setup` skill
- MCP server configuration details — see `mcp-tools` skill
- Theme customization — see `theme-configuration` skill
