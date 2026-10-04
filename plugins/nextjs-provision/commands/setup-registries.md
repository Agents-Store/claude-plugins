---
description: Set up community shadcn registries, the shadcn MCP server, and CLAUDE.md section for a project
argument-hint: [--mcp | --claudemd | --skill]
allowed-tools: [Read, Write, Edit, Bash, WebFetch]
---

# Setup Registries

Full project setup for shadcn community registry search — registries, MCP, CLAUDE.md section, and official skill.

## Instructions

1. Read the skill at `${CLAUDE_PLUGIN_ROOT}/skills/component-search/SKILL.md`

2. Verify `components.json` exists in the project root. If not:
   - Ask the user if they want to initialize shadcn/ui first
   - Run `npx shadcn@latest init` if approved

3. Parse arguments from "$ARGUMENTS":
   - (no args) — full setup: registries + MCP + CLAUDE.md + skill
   - `--mcp` — only configure the shadcn MCP server
   - `--claudemd` — only add CLAUDE.md section
   - `--skill` — only install official shadcn skill

4. **Add registries** — Run `/add-registries` to fetch the registries from `https://ui.shadcn.com/r/registries.json` (it skips `unavailable` and hidden ones) and add them to `components.json`

4b. **shadcn studio registries** — If the project uses shadcn studio, write the `@`-prefixed studio registries (not legacy `ss-*` keys):
   ```jsonc
   "registries": {
     "@shadcn-studio": "https://shadcnstudio.com/r/{style}/{name}.json",
     "@ss-components": "https://shadcnstudio.com/r/components/{style}/{name}.json",
     "@ss-blocks": "https://shadcnstudio.com/r/blocks/{style}/{name}.json",
     "@ss-pages": "https://shadcnstudio.com/r/pages/{style}/{name}.json",
     "@ss-themes": "https://shadcnstudio.com/r/themes/{name}.json"
   }
   ```
   For premium, convert entries to objects with `"params": { "email": "${EMAIL}", "license_key": "${LICENSE_KEY}" }`.

5. **Configure the MCP server** — Show the template from `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/mcp-config-template.json` (the official `shadcn` server) and create/update the project's `.mcp.json`; or run `pnpm dlx shadcn@latest mcp init --client claude`

6. **Install the official shadcn skill**:
   ```bash
   pnpm dlx skills add shadcn/ui
   ```

7. **Add CLAUDE.md section** — Append the content from `${CLAUDE_PLUGIN_ROOT}/skills/component-search/references/claude-md-section.md` to the project's CLAUDE.md

8. Test by installing one component from a community registry to verify it works
