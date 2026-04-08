---
description: Add community shadcn registries to components.json and optionally configure MCP servers
argument-hint: [--all | --category <name> | <registry-name>]
allowed-tools: [Read, Write, Edit, Bash]
---

# Setup Registries

Add community shadcn registries to the project's `components.json` for MCP-assisted search and CLI installation.

## Instructions

1. Read the skill at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/SKILL.md`
2. Read the registry reference at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/community-registries.md`

3. Parse arguments from "$ARGUMENTS":
   - `--all` — add all 30+ registries
   - `--category animation` — add only animation registries
   - `--category extended` — add only extended UI registries
   - `--category blocks` — add only blocks & sections registries
   - `--category ai` — add only AI component registries
   - `--category ecommerce` — add only e-commerce registries
   - `<registry-name>` — add a specific registry (e.g., `magicui`)
   - (no args) — show available categories and let user pick

4. Verify `components.json` exists in the project root. If not:
   - Ask the user if they want to initialize shadcn/ui first
   - Run `npx shadcn@latest init` if approved

5. Read the current `components.json` and check existing registries

6. Add the selected registries to the `"registries"` field — merge, do not overwrite existing entries

7. Offer to configure MCP servers:
   - Show the template from `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/mcp-config-template.json`
   - If the user accepts, create or update the project's `.mcp.json`

8. Offer to install the official shadcn skill:
   ```bash
   pnpm dlx skills add shadcn/ui
   ```

9. Offer to add the CLAUDE.md section from `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/claude-md-section.md`

10. Test by installing one component from a newly added registry to verify it works
