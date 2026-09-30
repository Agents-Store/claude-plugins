# LEARNINGS.md — vercel-dev

## 2026-04-02 — plugin config: Add HTTP MCP server for Vercel

**Problem:** Plugin had no MCP server connection — users couldn't use Vercel's official MCP tools (project management, deployments, environment variables) directly through Claude Code.
**Fix:** Created `.mcp.json` with HTTP streamable MCP endpoint `https://mcp.vercel.com`. Added `mcpServers` reference to `plugin.json`.
**Root cause:** Plugin was forked from Vercel's official plugin which handled MCP differently; HTTP MCP endpoint wasn't configured for Agents Store convention.
**Severity:** Major

## 2026-04-06 — deploy command: Ask target instead of defaulting to preview

**Problem:** Running `/deploy` with no arguments silently deployed to preview. User expected to be asked "production or preview?" and was frustrated when a preview deploy failed due to missing env vars — wasted build minutes and time.
**Fix:** Changed the Plan section in `commands/deploy.md` to require asking the user for deployment target when no argument is given, instead of silently defaulting to preview.
**Root cause:** The command description said "Default is preview deployment" and the Plan section only asked for confirmation on production, silently proceeding with preview otherwise. Users don't always know the default.
**Severity:** Major

## 2026-09-30 — test suite: Inherited suite was broken; synced to upstream 0.51.0

**Problem:** `bun test` failed 216 of ~1790 tests and one file killed the runner. Clean upstream v0.25.0 fails the same tests; its CI only looked green because `tests/validate.test.ts` imported `scripts/validate.ts`, whose module body ran `main()` → `process.exit(0)` mid-run (exit 0, no summary).
**Fix:** Vendored upstream `c632a50` (0.51.0, 1056/1056 green) and re-applied the fork patches as separate commits. Verify the suite the way upstream CI does: `bun install --frozen-lockfile && bun run build && bun run typecheck && bun run validate && bun run build:from-skills:check && bun test` — the summary line must print.
**Root cause:** Upstream bug fixed there by `if (import.meta.main) main()`; the fork never re-synced.
**Severity:** Major

## 2026-09-30 — deploy command: Edits belong in `deploy.md.tmpl`, not `deploy.md`

**Problem:** The 2026-04-06 and CLI-troubleshooting changes were written into `commands/deploy.md`, which `build-from-skills` regenerates from `commands/deploy.md.tmpl` — every build or test run silently reverted them.
**Fix:** The additions now live in the template; `deploy.md` is regenerated. Any `commands/*.md` or `agents/*.md` with a sibling `.tmpl` is generated — edit the template. Sections of `skills/deployments-cicd/SKILL.md` are pulled into `/deploy` and `deployment-expert` via `{{include:skill:…}}`, so text added at the end of an included section leaks into them.
**Root cause:** The generated file carries no "do not edit" marker.
**Severity:** Major

## 2026-09-30 — telemetry: Kept opt-in after the 0.51.0 sync

**Problem:** Upstream 0.51.0 sends a daily DAU ping and skill events to telemetry.vercel.com by default (opt-out `VERCEL_PLUGIN_TELEMETRY=off`); the fork never sent anything without opt-in.
**Fix:** `isDauTelemetryEnabled` in `hooks/src/telemetry.mts` — the one gate every telemetry path uses — returns true only for `VERCEL_PLUGIN_TELEMETRY=on`. Re-apply this patch on every upstream sync.
**Root cause:** Upstream policy change between 0.25 and 0.51.
**Severity:** Major

## 2026-09-30 — deployments-cicd: 12000-byte injection budget

**Problem:** Restoring the fork's CLI-troubleshooting and deploy-hooks sections inline pushed the skill past the injection budget (`tests/cli-explain.test.ts`, `usedBytes <= budgetBytes`); upstream leaves ~80 bytes of headroom.
**Fix:** Both sections live in `skills/deployments-cicd/references/cli-deploys.md`, linked by one line at the end of Best Practices (11988 bytes injected). Add fork content to `references/`, never inline.
**Root cause:** Upstream sizes the skill body to its budget.
**Severity:** Minor
