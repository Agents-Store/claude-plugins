# LEARNINGS — macstack-dev

Accumulated feedback and fixes. Fixes use: date, type, Problem / Fix / Root cause /
Severity. Enhancements use: date, component, Feature / Implementation / Rationale.

## 2026-08-09 — initial release notes

- **Schema source of truth**: the bundled `macstack.schema.json` is a copy of the
  standard (VK-OPS `docs/macstack/`, branch `feat/macstack-json`). When the standard
  moves to its own repo/Software Directory, update the bundled copy AND this note.
- **Infisical CLI gotcha** (baked into infisical-env skill): the CLI keeps one ACTIVE
  instance; `--domain` is ignored on authenticated reads — always
  `infisical login --domain=…` before pulling from a different self-hosted instance.
- **Env rendering**: values must be written as `KEY='value'` (single quotes, POSIX
  escape for embedded quotes) or multiline PEM/JWT values break `source .env`.
- **Scaffold order is the product**: prototype → stack plugins → dev plugins. Every
  violation observed in testing produced files that contradicted the architecture.

## 2026-08-09 — first real init-project run (macstack-website-directus-nextjs)

- **Finding / Fix**: the audited project's `.mcp.json` contained HARDCODED credentials
  (an xc-mcp-token and a Figma API key). init-project's audit table already reads
  `.mcp.json` — added an explicit rule: flag any literal token/key found there as a
  SECURITY open_question (rotate + move to `${VAR}`). Root cause: real projects drift;
  the audit must treat `.mcp.json` as a secrets-scan surface, not just an MCP inventory.
  Severity: high.
- **Finding**: deep `grep` over `src/` can hang minutes on cloud-synced folders (iCloud
  file materialization). Fix baked into practice: derive entities from schemas/types
  with a timeout; on timeout record collection names as open_questions instead of
  blocking. Severity: medium.
- **Validation**: generated macstack.json passed schema + all integrity rules on the
  first run; legacy stack.json mapped cleanly (layers→software, plugins→context.plugins,
  parent→prototype candidate + open_question).

## 2026-08-09 — the standard moved to GitHub (v1.1.0)

- The canonical home is now **github.com/macstacks/macstack** (schema, examples,
  scripts/lint.py) + **github.com/macstacks/registry** (categories, software
  passports, entity/trigger/agent templates). All skills are GitHub-first with the
  bundled copies as offline fallbacks; the bundled schema's `$id` points at the raw
  URL. When the schema changes upstream, refresh the bundled copies in
  `skills/lint/references/` in the same PR.

## 2026-08-09 — v1.2.0: feedback loop + dual-source env

- **feedback skill/command added** (mirrors plugin-creator's loop, extended with
  routing): plugin problems → plugin skills; schema problems → macstacks/macstack
  (+ MANDATORY mirror sync: the bundled schema copy here and any project mirrors);
  registry problems → macstacks/registry. A fix applied to a mirror gets silently
  overwritten — always fix at the source, then sync mirrors in the same session.
- **infisical-env now collects variables from TWO sources**: macstack.json
  resources.accesses (architecture) ∪ the env tokens required by the project's
  enabled Claude plugins (settings.json enabledPlugins → stack plugin .mcp.json
  ${VAR} + .env.example + settings.local.json env block). .env.prod/.env.dev are
  always created; required-but-empty keys stay visible as KEY='' with a FILL ME
  comment. Cross-check keeps macstack.json the superset registry of tokens.

## 2026-08-21 — lint/references: schema mirror synced to rev 9 (retroactive entry)

**Problem:** the bundled `macstack.schema.json` was synced to upstream rev 9
(`identity.industry`, commit `036314f`) without a LEARNINGS entry, even though the
feedback skill requires one per change. The gap made the mirror's actual revision
invisible from inside the repo.
**Fix:** entry recorded here; the rev-10 sync below follows the rule.
**Root cause:** the sync was a `chore` commit and the rule lives in the `feedback`
skill, which a plain mirror refresh does not invoke.
**Severity:** Minor — but it is why the mirror's revision is only discoverable by a
network `diff`. A rev marker inside the schema would close this properly.

## 2026-08-24 — project-docs / docs-merge / docs-migrate: the `macstack/` folder

**Feature:** the plugin now owns a standardized `macstack/` folder, not just a lone
`macstack.json`. Beside the spec live the documents a project actually accumulates:
`USER-CASES.md` (cases per role, versioned), `BUSINESS-LOGIC.md`, `OPEN-QUESTIONS.md`
(§A owed by the client · §B deferred by us, each with the trigger that makes deferral
unsafe), `DECISIONS.md` plus dated rulings that each record their cost if wrong, an
immutable `inbox/` for client material, `deltas/`, `reviews/`, and an append-only
`log.md`. Incoming client edits go through a gated loop instead of being merged by
hand: intake → delta of contradictions and additions → owner rulings → cases → logic
→ spec → open questions → journal.

**Implementation:** three skills — `project-docs` (the standard: layout, path
resolution, ID spaces, anchors, language rule, invariants), `docs-merge` (the loop,
four human gates, plus a 3b bypass that skips the ceremony when there are no
contradictions), `docs-migrate` (`disable-model-invocation: true`; one-shot relocation
of a grown-organically `docs/`). Three commands: `/docs`, `/docs-merge`,
`/docs-migrate`. Structure is defined once in
`skills/project-docs/references/doc-contracts.json`, read by both the writer and the
linter, so the two cannot drift. `lint` gains rule group 12; `setup` gains a real
resolver (`macstack/macstack.json` → legacy `./macstack.json` → upward search; both
present is an error). Schema rev 10 adds `docs`, `$defs/{docRef,openItemRef,decisionRef}`,
`lifecycle.decisions[]` and `roles[].cases`, all additive with format still `"1.0"`.

**Rationale:** the loop was not invented here — it was reverse-engineered from a live
project that had already grown 25 markdown files in 15 days and was running the cycle
by hand. Three things that project taught, now enforced:

- **Prose does not belong in JSON.** Its `lifecycle.open_questions` had drifted into
  17 prose entries, several over 800 characters, and `needs_from_client` restated five
  of them — a second, uncontrolled copy that had already disagreed with the markdown
  once and needed manual reconciliation. Both are now pointer arrays; the text lives in
  `OPEN-QUESTIONS.md`, and `needs_from_client` is a derived view the linter can check.
- **Anchors, not headings.** Section anchors (`<!-- macstack:section=… -->`) are what
  make `docs.language` implementable: prose and headings translate freely, the linter
  greps the anchor. Fixed English headings would have forced every document into one
  language.
- **Homoglyphs are a real defect class, not a hypothetical.** The project's delta file
  numbered its contradictions with U+041A CYRILLIC CAPITAL KA, so `grep "K-1"` returned
  nothing at all — silently. ID tokens are now ASCII-only by rule, and lint 12.3 checks
  the codepoint rather than the glyph. Dogfooding caught this twice: the first draft of
  `project-docs` illustrated the trap by printing the Cyrillic character, which its own
  rule then flagged. The illustration now names the codepoint instead.

Also fixed in passing: `plugin.json` (1.3.0) and `marketplace.json` (1.2.0) had drifted
apart despite the plugin's own rule requiring parity — both are now 1.4.0;
`coverage-areas.json` was bundled but missing from the README's fallback list; the
`examples` skill still pointed at the pre-GitHub location of the canonical examples.

## 2026-08-24 — lint/references: the schema mirror is AHEAD of upstream (rev 10)

**Known drift, deliberate and temporary.** `skills/lint/references/macstack.schema.json`
carries rev 10 (the `docs` section, `$defs/{docRef,openItemRef,decisionRef}`,
`lifecycle.decisions[]`, `roles[].cases`) while
`github.com/macstacks/macstack@main` is still at rev 9 (`036314f`). The owner chose to
ship the plugin first and land the standard separately.

Nothing breaks while this holds: the schema has no `additionalProperties: false`, so a
`macstack.json` carrying the new fields validates against rev 9 too, and the rev-10
mirror validates every rev-9 file — verified against the four canonical examples with
upstream's own `scripts/lint.py` (0 warnings) plus two live project files.

**To close it**, copy the mirror over the standard and push:

```bash
git clone https://github.com/macstacks/macstack.git && cd macstack
cp <plugins>/macstack-dev/skills/lint/references/macstack.schema.json schema/macstack.schema.json
python3 scripts/lint.py examples/*.macstack.json    # must be OK, 0 warnings
git commit -am "feat(schema): the macstack/ folder — docs section and pointer-form lifecycle (rev 10)"
```

Then verify the mirror matches again, per the rule in `skills/feedback/SKILL.md`:
`curl -fsSL https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json | diff - skills/lint/references/macstack.schema.json`

**Why this entry exists:** the mirror carries no rev marker, so drift is invisible from
inside the repo without a network diff — the same gap the retroactive rev-9 entry above
records. Until a rev marker exists in the schema itself, a LEARNINGS note is the only
thing that makes a known drift discoverable.
