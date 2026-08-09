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

## 2026-08-09 — component-registry: Button-as-link pattern reversed by official docs

**Problem:** Skill taught `<Button nativeButton={false} render={<a/>}>` per earlier Base UI behavior.
**Fix:** Official Base UI Button docs now forbid this (role="button" overrides link semantics); replaced with `buttonVariants()` + plain `<a>`. Trigger `render` composition unchanged.
**Root cause:** Upstream guidance changed after Base UI became the default base (July 2026).
**Severity:** Critical

## 2026-08-09 — doc-alignment: Full realignment to shadcn CLI v4.16 / Base UI default / OKLCH theming (v1.2.0)

**Feature:** Plugin-wide alignment with current official docs: removed the nonexistent `--registry` flag everywhere in favor of namespaced addresses (`@ss-components/button-01`); rewrote shadcn studio registry config to the real `@`-prefixed URLs with `{style}/{name}` placeholders plus the new `@shadcn-studio` and `@ss-pages` namespaces and `params`-based premium auth; documented the v4 init flow (templates, `-b base|radix|aria`, 8 style presets, `--pointer`, visual builder at ui.shadcn.com/create, `shadcn apply`); converted all theming content from HSL triples to OKLCH + `@theme inline`; corrected the Jpisnice MCP tool names to the real snake_case set (v2.0.0, `--mode`/`--port` transports); added the Oct 2025/2026 official components (field, item, kbd, spinner, empty, input-group, button-group, questionnaire, Base UI toast, chat suite); refreshed the registry ecosystem to 267 directory entries (@coss replaces @originui, @commercn replaces @commerce-ui, corrected 9 URL templates, added 16 notable 2026 registries, GitHub-repo installs, `registry add`/`validate`).
**Implementation:** Updated all 8 skills, 3 commands, the agent, 6 reference files, README, and plugin.json (1.1.1 → 1.2.0); appended the Button-as-link fix entry above; `.mcp.json` verified current and left untouched.
**Rationale:** The plugin was written against CLI v2/v3-era syntax and pre-July-2026 Radix/HSL conventions; every install command using `--registry` and the studio registry config were broken against CLI v4.16.2, and the tool tables referenced tools that do not exist.

## [2026-08-09] — fact-check: corrections from adversarial doc verification

**Problem:** Three claims refuted against live sources: (1) the Base UI package was still named `@base-ui-components/react` in component-registry and troubleshoot SKILL.md — the package was renamed to `@base-ui/react` (old name deprecated at 1.0.0-rc.0, new name at 1.7.0); (2) 19 of the URL-column entries in component-search/references/community-registries.md were truncated to a bare `/r` base (e.g. `https://animate-ui.com/r`) instead of the official directory's full `/{name}.json` templates, and the install example `@commercn/product-card` referenced a nonexistent item (live registry has product-card-01/02/03); (3) the Jpisnice MCP server was described as exposing 7 tools and being "discovery-only" — v2.0.0 actually registers 10 tools, including the tweakcn theme tools `list_themes`, `get_theme`, and `apply_theme`, the last of which writes theme files to the project.
**Fix:** Renamed the package to `@base-ui/react` in both SKILL.md files; appended `/{name}.json` to all 19 truncated URL templates using the exact values from `https://ui.shadcn.com/r/registries.json`; changed the example to `@commercn/product-card-01`; added the three theme tools to the mcp-tools tool table, reworded the claim to "no component-install tools" with a note that `apply_theme` writes files (supports `dryRun`), and updated the mirrored tool list in component-search/SKILL.md.
**Root cause:** Package renamed upstream again (`@base-ui-components/react` → `@base-ui/react`) after the skill text was written; the curated registry table was transcribed with shortened base URLs instead of copying the directory's exact `{name}.json` templates; the Jpisnice tool inventory was taken from pre-2.0 docs that predate the tweakcn theme tools.
**Severity:** Major
