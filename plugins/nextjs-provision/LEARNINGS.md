# LEARNINGS.md — nextjs-provision

Accumulated fixes, discoveries, and improvements for the nextjs-provision plugin.

## 2026-03-28 — component-registry: Add shadcn v4 Button link pattern

**Problem:** shadcn v4 uses `@base-ui/react` instead of Radix. The `asChild` prop no longer exists on Button. Using `render={<a />}` without `nativeButton={false}` causes a Base UI console warning. No documentation in the skill covered this pattern.
**Fix:** Added "shadcn v4 Button as Link" section to component-registry SKILL.md with correct `render` + `nativeButton={false}` pattern and a note about the removed `asChild` prop.
**Root cause:** Skill was written for shadcn v3 (Radix-based). shadcn v4 migrated to @base-ui/react with a different composition API.
**Severity:** Major
