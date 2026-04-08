# LEARNINGS.md — nextjs-provision

Accumulated fixes, discoveries, and improvements for the nextjs-provision plugin.

## 2026-03-28 — component-registry: Add shadcn v4 Button link pattern

**Problem:** shadcn v4 uses `@base-ui/react` instead of Radix. The `asChild` prop no longer exists on Button. Using `render={<a />}` without `nativeButton={false}` causes a Base UI console warning. No documentation in the skill covered this pattern.
**Fix:** Added "shadcn v4 Button as Link" section to component-registry SKILL.md with correct `render` + `nativeButton={false}` pattern and a note about the removed `asChild` prop.
**Root cause:** Skill was written for shadcn v3 (Radix-based). shadcn v4 migrated to @base-ui/react with a different composition API.
**Severity:** Major

## 2026-03-30 — component-registry: Expand render prop guidance to all trigger components

**Problem:** The `asChild` → `render` migration guidance only covered Button as `<a>`. SheetTrigger, DialogTrigger, and other compound trigger components also need `render` prop composition, but no examples existed. Building a mobile nav with SheetTrigger wrapping a Button caused a TypeScript error on `asChild`.
**Fix:** Renamed section to "shadcn v4: `render` Prop Instead of `asChild`". Added explicit note that `asChild` doesn't exist on ANY shadcn v4 component. Added SheetTrigger + Button composition example alongside the existing Button-as-link pattern.
**Root cause:** Previous fix (2026-03-28) only addressed the Button-specific case. The `render` prop pattern applies to all `@base-ui/react` components, not just Button.
**Severity:** Major

## 2026-04-08 — Enhancement: Add multi-registry component search (v1.1.0)

**Feature:** Added `component-search` skill with full reference of 30+ free community registries, MCP config templates, CLAUDE.md section template, and two commands (`search-components`, `setup-registries`). Extended `setup`, `mcp-tools`, and `component-registry` skills with community registry sections. Added `.mcp.json` with official shadcn MCP and Jpisnice community MCP servers.
**Implementation:** New skill (component-search) + 4 reference files, 2 new commands, extended 3 existing skills, updated agent, added .mcp.json
**Rationale:** Plugin only covered standard shadcn/ui and shadcn studio registries. Users had no guidance on discovering and installing components from the 30+ free community registries (MagicUI, Aceternity, etc.) available for shadcn v4.

## 2026-04-08 — component-search: Replace hardcoded registries with dynamic fetch

**Problem:** The community-registries.md reference and setup instructions used a hardcoded list of 30 registries. This becomes stale as registries are added/removed.
**Fix:** Added dynamic fetch from `https://ui.shadcn.com/r/registries.json` (official endpoint, 180+ registries, always current). Created `/add-registries` command that fetches and populates components.json automatically. Updated component-search skill, setup skill, and setup-registries command to use dynamic source. Kept category guide as curated reference.
**Root cause:** Original implementation used a static list instead of the official API endpoint.
**Severity:** Major
