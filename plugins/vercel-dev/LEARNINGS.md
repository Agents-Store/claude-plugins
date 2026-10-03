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

## 2026-10-03 — re-vendor: 0.51.0 → 0.53.0 (e8a2e71), same recipe

**Problem:** Upstream moved 23 commits, deleted the `nextjs`, `next-cache-components`, `next-upgrade`, `next-forge`, `shadcn` and `turbopack` skills and added 32 `.vercel.approvers` files. Every fork patch had to survive the sync.
**Fix:** `rsync -a --delete` of a clean upstream checkout at `e8a2e71` (upstream `main` had already moved 5 commits past it; the vendor stays on the 0.53.0 bump) into `plugins/vercel-dev/`, excluding `.git`, `.plugin/`, `.cursor-plugin/`, `.kimi-plugin/`, `CLAUDE.md`, `.claude/projects/`, `.claude-plugin/` (the fork keeps only its own `plugin.json`), `.mcp.json`, `.gitignore`, `LEARNINGS.md`, `skills/*/evals/`, `skills/deployments-cicd/references/cli-deploys.md` and every `.vercel.approvers`; then `rmdir` the emptied skill directories and drop `skills/next-upgrade/evals/` with its skill. Patches re-applied as separate commits: manifest path (`git apply` of the 0.51 diff), telemetry opt-in (sources and tests by `git apply`, compiled hooks rebuilt with `bun run build:hooks`, never merged as text), `/deploy` template (then `bun run build:from-skills`), CLI-deploys link, placeholders. Verify with the six-command chain and `unshare -rn bun test` (no network namespace proves no test reaches the telemetry bridge).
**Root cause:** Vendored plugin with local patches; the vendor commit is pure upstream, every fork change is its own commit so the next sync can replay them.
**Severity:** Minor

## 2026-10-03 — deployments-cicd: link as a table row, 3 bytes of headroom

**Problem:** Upstream 0.53.0 added a Live status row and left 22 bytes of the 12000-byte injection budget; the fork's 70-byte link line to `cli-deploys.md` pushed `tests/cli-explain.test.ts` over.
**Fix:** The link is a row of the references table and the table is condensed in one hunk (link text is the file name, "Post PR preview URLs"); the skill injects 11997 of 12000 bytes. Anything added to `SKILL.md` on the next sync needs the same trade; fork content stays in `references/`.
**Root cause:** Upstream sizes the skill body to its budget.
**Severity:** Minor

## 2026-10-03 — commands/: only commands, and stale claims in cli-deploys.md

**Problem:** `claude plugin validate --strict` failed on `commands/_conventions.md` (no frontmatter; every `.md` in `commands/` is a command). `cli-deploys.md` also said `vercel env add <name> preview` needs a Git branch (CLI 62.2.0: optional, with `--value` and `--yes`), that `output: 'standalone'` "causes 404" (no primary source; Vercel's KB blames the Framework Preset or Output Directory), and omitted the Deploy Hooks limits.
**Fix:** The guide moved to `references/command-conventions.md` (a dotfile rename would be picked up as a command by upstream's `_`-prefix-only filters) and `scripts/validate.ts` hints point there. The env, `standalone` and Deploy Hooks text follows `vercel env add --help` (62.2.0), the Vercel KB and `vercel.com/docs/deploy-hooks`. The `env add` claim was read from `--help`, not run against a project without Git integration.
**Root cause:** Fork prose written once from observation and never re-checked against the CLI or docs.
**Severity:** Minor
