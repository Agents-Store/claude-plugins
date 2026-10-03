# Learnings

## 2026-09-26 — plugin: renamed from `document-generator` to `document-generator-ops`

**Problem:** The name carried no process suffix, so it did not say who the plugin is for. It was one of twelve first-generation plugins created before the `{tool}-{process}` convention.
**Fix:** Renamed to `document-generator-ops` — business documents (proposals, invoices, contracts, NDAs) for business users. Directory, `plugin.json` and the marketplace entry changed together; the marketplace `renames` map points `document-generator` at `document-generator-ops`, so installed copies follow the new name (Claude Code 2.1.193+). Major version bump: command and agent namespaces change from `document-generator:` to `document-generator-ops:`. The glob every command uses to find its own scripts (`**/document-generator/scripts/...`) now names the new directory — the old pattern would match nothing after the move. The user-data directory `~/.document-generator/` keeps its name on purpose: renaming it would orphan every existing user's preferences and logos.
**Root cause:** Created before the naming convention existed; never revisited.
**Severity:** Minor

## 2026-09-27 — document-templates: example company name was a real studio

**Problem:** The `companyInfo.name` example in the field table used the author's own studio name.
**Fix:** Replaced with the fictional `Northwind Studio`.
**Root cause:** Example filled in from real data.
**Severity:** Minor

## 2026-10-03 — plugin: current lock, `${CLAUDE_PLUGIN_ROOT}` paths, honest pandoc note (3.1.0)

**Problem:** The lock trailed upstream by two to five minor versions (docx 9.6, pdfkit 0.15, Playwright 1.59); `check_deps.js` reported "Playwright Chromium browser not installed" on every normal install and demanded the unused `pdf-lib`; commands found their scripts with a Glob from the project directory, which never reaches an installed plugin in `~/.claude/plugins/cache`; the docs promised that the pandoc engine gives a DOCX matching the PDF; `rules/CLAUDE.md` (the onboarding, data-collection and output-location rules) was never loaded because Claude Code does not read a plugin's `CLAUDE.md` and has no `rules/` component.
**Fix:** Lock moved to docx 9.8.x, pdfkit 0.20.x, Playwright 1.63.x (`engines.node >= 20`, `pdf-lib` removed, `pdf-parse` pinned `~1.1.4`). `check_deps.js` asks Playwright for its real Chromium path and, failing that, tries a headless launch; it also reports Node < 20 and no longer lists `wkhtmltopdf` (deprecated in pandoc; Typst added to the `convert.sh` chain). Commands, agent and skills use `${CLAUDE_PLUGIN_ROOT}` and call scripts without `cd`. Pandoc is documented as structure-only (it drops CSS; the look comes from `assets/reference.docx`). The rules moved into the `document-rules` skill. `waitUntil: "networkidle"` became `load` plus `document.fonts.ready`; the DOCX logo type is detected from magic bytes instead of always `png`.
**Root cause:** The first generation of the plugin was written against a snapshot and never re-verified; the pandoc claim was never tested, and path variables did not exist yet.
**Severity:** Minor
