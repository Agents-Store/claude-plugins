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

## 2026-08-24 — lint/references: the schema mirror was AHEAD of upstream · **CLOSED same day**

**Closed 2026-08-24:** rev 10 landed as `macstacks/macstack@65b76c7`, and rev 11
(`cecea1e`, the `tasks` and `changelog` entries) followed the same day. Mirror and
source are identical — verified through the API rather than the CDN-cached raw URL,
for the reason the entry below this one records. The
entry stays because the drift was real while it lasted and the reasoning is what makes
the next one recoverable.

**The drift, as it stood.** `skills/lint/references/macstack.schema.json`
carries rev 10 (the `docs` section, `$defs/{docRef,openItemRef,decisionRef}`,
`lifecycle.decisions[]`, `roles[].cases`) while
`github.com/macstacks/macstack@main` is still at rev 9 (`036314f`). The owner chose to
ship the plugin first and land the standard separately.

Nothing breaks while this holds: the schema has no `additionalProperties: false`, so a
`macstack.json` carrying the new fields validates against rev 9 too, and the rev-10
mirror validates every rev-9 file — verified against the four canonical examples with
upstream's own `scripts/lint.py` (0 warnings) plus two live project files.

**How it was closed** — the same recipe, kept for the next time the mirror leads:

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
thing that makes a known drift discoverable, and the only thing that says when it ended.

## 2026-08-24 — test-cases: TEST-CASES.md derived from the acceptance bullets

**Feature:** the folder gains a seventh document. `TEST-CASES.md` says **how** each
"Готово, если" bullet of `USER-CASES.md` is verified — at least one test per bullet,
each tagged `auto` (naming the test title that proves it) or `manual` (with
preconditions and steps a person can follow). Ids carry their case: `C-06.T3`, so
`grep 'C-06\.'` finds every check for that case. Section order mirrors USER-CASES so
the two read side by side. New skill `test-cases`, new command `/macstack-dev:test-cases`,
new contract entry, `docs.files.test_cases` in the schema, lint rules 12.11 and 12.12.

**Implementation:** derivation is incremental and id-addressed. An existing test keeps
its hand-refined steps — those are the point of the document and are never regenerated
over; a bullet with no test gets one appended; a test whose bullet is gone is struck,
not deleted. The header names the `USER-CASES.md` version it was derived from, and lint
warns when that falls behind. `docs-merge` now re-derives in the same pass that changes
an acceptance bullet, because a changed bullet leaves the coverage table lying.

**Rationale:** the chain already existed in practice but had a hole in the middle.
`USER-CASES.md` says what must be true; `reviews/*-conformance.md` records what was
found the day somebody checked. Nothing said how to check — so each audit re-invented
its own method, and the only record of a check was a dated review that nobody re-runs.
Three rules came out of reading real acceptance bullets rather than imagining them:

- **One case mixes both kinds.** C-06 in the live project asserts both "отметиться без
  геолокации можно всегда" (a machine can decide that) and "предупреждение написано
  спокойно: это не обвинение" (only a person can). Splitting the document by automation
  would tear the case in half, so the tag lives on the test, not on the file.
- **`auto` describes how it is checked today**, not what could be automated one day.
  An aspirational tag is how a coverage table starts lying.
- **A prohibition needs two assertions**, not one: the platform refuses, and the refusal
  explains itself. A silent refusal passes a naive test and fails the case.

The sharpest rule is about what NOT to write: if verifying a bullet needs a fact the
case does not state — a threshold, a deadline, an exact message — the gap is in
`USER-CASES.md`, and it goes to `OPEN-QUESTIONS.md §A` or through `docs-merge` as a
contradiction. A test that invents its own acceptance criterion becomes a second
specification, which is the failure mode this whole folder exists to prevent.

## 2026-08-24 — project-docs / docs-merge / docs-migrate / lint: 15 defects from a dry run

**Problem:** the folder standard was written, reviewed and validated clean — and was
still not followable. An adversarial dry run that *actually executed* the instructions
(scratch project, the real 8-page client PDF through the full loop, lint group 12 walked
by hand, the path resolver tested in three physical scenarios) found 15 defects in ~45
tool calls. None had been visible to a reading review, including a formal validation
pass that reported no findings.

**Fix:** all 15 applied. The four that mattered most:

- **Case-id letters were a closed enum.** `^(X|C|T|O|S|Z)-[0-9]{2}$` with X, S and Z
  reserved leaves exactly C, T and O for every role a project can have — a fourth role
  had no legal id, and nothing said how a letter gets picked. The live project has three
  roles, so the ceiling was invisible. Now `^[A-Z]-[0-9]{2}$`, with the reserved set and
  the assignment rule stated.
- **Lint 12.1 passed vacuously.** It checked "every file named in `docs.files` exists",
  but `docs.files` is author-populated — list nothing and the rule approves an empty
  folder. Now it reads the contract's `documents` map: the checker is driven by the
  standard, not by the thing being checked.
- **Retiring a role produced a guaranteed lint error.** Apply struck the role's cases but
  never its section heading, and 12.4 requires every case-section letter to map to a
  role. Reproduced live.
- **A `versioned: true` document with no journal made 12.5 unevaluable.** Two documents
  carried a version they could never satisfy. They are living documents; the version came
  off rather than the rule being weakened.

The rest: an anchor asserted by one file and undefined by the contract; no documented
path from legacy prose `open_questions` to pointer form (lint warned, nothing remediated);
the layout diagram showing `macstack.json` inside the folder while creation never moved a
legacy root file; "stop" versus "ask which is canonical" for the same error; and prose
placeholders for the decision and open-item spaces, written with a hyphen their own
regexes do not allow — the dry run wrote
`D-1`, then had to self-correct against the pattern.

**Root cause:** every one of these is an instruction that reads correctly and executes
wrongly. A reviewer checks whether a sentence is true; only an executor discovers that a
rule cannot be satisfied, that two files disagree about the same step, or that a
constraint has no legal solution past the third role. The formal validation was not
wrong — it was answering a different question.

**Severity:** Major. Shipping 1.4.0 without this pass would have put a standard in front
of users that breaks on the fourth role and cannot drive its own linter to green.

**How to apply:** for anything whose product is *instructions* — a skill, a runbook, a
convention — one adversarial execution against real material is worth more than any
number of readings. Budget it as part of the work, not as a nicety, and give it the real
input rather than a toy: the defect ceiling only showed up because the live project has
exactly three roles.

## 2026-08-24 — tasks / changelog / status: the forward half of the folder

**Feature:** the folder could describe a project but not run one. Three additions close
that. `TASKS.md` holds milestones with falsifiable `done_when` checks and tasks whose
ids match the commit convention teams already use (`M11-T9`), every one of them
carrying a `tracker` id so the file and the team's own tracker cannot quietly diverge.
`log.md` becomes typed — `intake · merge · work · release` — and the `work` entry is
the development log the folder never had. `CHANGELOG.md` is its curated, client-facing
derivative: what reached the people who use the product, newest first. A new `status`
skill and `/macstack-dev:status` answer "where are we and what do I run next" by
computing the blockers from the artifacts rather than storing a list that goes stale.

**Implementation:** three skills (18 total), three commands, schema rev 11 adding
`docs.files.{tasks,changelog}`, `$defs/{taskRef,milestoneRef}`, `lifecycle.milestones[]`,
and lint rules 12.13–12.16. The tracker rule is deliberately product-agnostic: the
plugin never names a tracker, it reads the binding from `resources.bindings`, discovers
whatever tools the session exposes, and reconciles — reading both sides, showing a diff,
and refusing to pick a winner when both changed.

**Rationale:** an audit of the four things the owner asked for found that only one —
open questions — was genuinely built. The other three were absent in a way that was
worse than obvious:

- **`log.md` looked like a development log and was contractually forbidden from being
  one.** Its entry grammar admitted exactly `intake|merge` and all six required fields
  were client-merge artifacts. The folder appeared to have a log, so nobody noticed
  there was no record of the work.
- **`lifecycle.next_steps` was dead schema** — the only field in `lifecycle` with no
  description, referenced by zero skills, zero commands and zero lint rules. Somebody
  intended a task list, added the field, and never wired it.
- **`OPEN-QUESTIONS.md §B` cannot be a task list**, and reading its two required fields
  says why: both argue for *not* doing the work. It is a good debt register and a bad
  backlog. They stay separate, and an item is PROMOTED across with a strike and a
  pointer, so the argument for having deferred survives beside the decision to stop.
- **The staleness detector was self-defeating.** The only currency check compared
  `lifecycle.updated` against the newest `log.md` entry — and with no client input both
  freeze in agreement. A project could run for months, green.

**What the evidence changed about the design.** A live project already had working
conventions in the wrong containers: 420 lines of `## Recent Changes` inside a 116 KB
`CLAUDE.md`, ordered oldest-first and undated; and a real per-milestone ledger that
lived in a gitignored scratch directory and was **destroyed once by `git clean -fdx`**,
forcing a manual salvage of 26 rulings. Both are now first-class, committed files. Two
habits from that project were kept verbatim because they are better than the obvious
alternative: supersession in place rather than deletion, and §B bucketed by the
*trigger* that makes deferral unsafe rather than by P0/P1.

**Borrowed from a sibling project-runner pack**, with attribution to its ideas rather
than its code: the attention list is computed from predicates over existing artifacts
instead of stored; the status render ends with the exact next command; and `dropped`
is kept distinct from `todo`, because "deliberately not doing this" and "not yet
reached" are different states that a single glyph would hide. Deliberately not borrowed:
its git-tag checkpoint machinery, its weighted numeric quality score (two of four
inputs are subjective, and the critical-issue override is what actually does the work),
and its silence protocol — sensible for autonomous workers, wrong for a folder a human
edits.

**Also fixed, all found by the same audit:** lint 12.1 required every document in the
contract to exist including the ones whose path is a dated pattern, contradicting the
lazy-directory rule; 12.4 validated A-pointers but not B-pointers; 12.5 had to parse
"the last journal row" of a table whose shape was declared nowhere; `log.md` had no
`sections` so 12.2 could never fire on it; and two skills instructed users to write
prose into a JSON field the standard forbids — the plugin was generating its own
warnings.

## 2026-08-24 — feedback: the mirror check reports a false drift right after a push

**Problem:** the skill's own verification for "is the bundled mirror still identical to
the standard" is `curl -fsSL <raw-url> | diff - <bundled>`. Run immediately after
pushing a schema change, it prints a full diff — `raw.githubusercontent.com` is
CDN-cached for a few minutes and serves the previous revision while the commit is
already on `main`. Hit live while landing rev 11: the push reported
`65b76c7..cecea1e`, and the very next `curl | diff` claimed the mirror was ahead by
everything that had just been pushed.

**Fix:** the trap is now named in the skill, with the uncached alternative
(`gh api …/contents/<path>?ref=main`) beside it, and an explicit instruction not to
"repair" the mirror on that evidence.

**Root cause:** a verification that is correct at steady state and wrong for a few
minutes in exactly the situation it is prescribed for — right after a change.

**Severity:** Major. The failure mode is not a missed check but an inverted one: the
obvious response to that diff is to copy upstream back over the mirror, which silently
reverts the change that was just published. The instruction was wrong in the direction
that destroys work.
