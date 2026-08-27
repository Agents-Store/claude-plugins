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

## 2026-08-24 — project-docs, sync-spec, screens: fold the folder into four, invert the direction

**Feature:** The `macstack/` folder was twelve files and five directories at its root with no
signal about which of them a human may edit. It is now six entries: `README.md`,
`macstack.json`, and four folders — `client/` (what a human writes and a client reads),
`generated/`, `inbox/`, `history/`. Two authored client documents were added:
`ROLES-AND-TASKS.md` in the format trigger → task → workflow, and `SCREENS.md`, whose last
column is what must NOT be visible on that screen.

**Implementation:** `doc-contracts.json` gained the four `dirs`, new paths for every document,
a `table` anchor and per-document `table_columns`; the schema gained `docs.dirs` and the
`roles_tasks` / `screens` keys. New: `skills/sync-spec` (+ command), `render-docs/references/
seed.py`, `docs-migrate/references/restructure.py`. Lint rules 12.21–12.23. `ROLES.md` stopped
being generated.

**Rationale:** The owner's complaint — "too many folders, too many files, badly sorted" — is the
same one Martin Fowler makes about spec-kit: a specification spread over many files becomes more
tedious to review than the code it describes. So the fix had to REDUCE the count, not re-sort it.
The second half is the inversion: a client cannot correct a generated file, and the client is the
one who knows whether a task belongs to a role or whether a number may appear on a screen. The
client documents are now the source; `sync-spec` reconciles the spec's business half against
their tables.

**Two things measured while building it.** Tables are read by POSITION, never by header text —
otherwise a project writing its documents in German would need a second parser. And `sync-spec`
refuses to create or delete: an id is referenced by workflows, tests and prose, so a machine that
invents one orphans a reference on the next rename. A rename therefore shows up as one addition
and one removal, and the report says so instead of guessing.

## 2026-08-24 — plan-changes: the missing link between a requirement and a code change

**Feature:** `/macstack-dev:plan-changes`. Finds the user cases nobody scheduled and no audit
confirmed, emits task skeletons pointing back at the case, and the agent fills `files` and
`acceptance` by reading the code. The handoff is a planning session reading a task that names
its requirement — not a prompt that repeats the requirement and records nothing.

**Implementation:** `skills/plan-changes/` with `references/uncovered.py` + command. The script
reads three inputs: USER-CASES, TASKS, and the newest `reviews/*-conformance.md`.

**Rationale:** The owner's process is client mess → readable document → filled by the client →
machine spec → detailed change plan → agent codes. Five links; four existed. Between "the spec
is updated" and "the agent starts" there was nothing, so each planning session re-explained the
requirement from scratch and no record survived of which change answered which requirement.

**Measured while building it.** The first version reported "63 cases with no plan" on a project
where 35 were already audited as implemented. True and useless: a work list nobody believes is
a work list nobody reads. Reading the audit's per-case verdict cut it to 8 — exactly the eight
cases added in user-cases v1.8, which is the right answer. The lesson generalises: a gap report
that ignores what has already been verified reports the size of the document, not the size of
the work.

## 2026-08-25 — the whole plugin: the table was the machine interface, and prose followed it there

**Problem:** The owner's complaint was that the plugin had become hard to work with and
its documents hard to read. Measured on the live project rather than argued about:
**56 tables across 20 documents**, cells up to **1353 characters**, one client-facing
document at **six columns by thirty-seven rows of 600–880 characters a row**. Sixty-three
of sixty-three cases printed twice — once as index rows, once as headings, with zero
divergence. Thirty-three decisions in three places. Two client documents in English under
`docs.language: ru`. Three documents empty of substance. And 17 commands, several of
which nobody could tell apart.

**Root cause — and it is not "somebody wrote a wide table".** v1 made the table the
machine interface *on purpose*: `table_rule` reads "Columns are identified by POSITION,
never by header text", because a heading follows `docs.language` and matching on its text
would break the moment a project wrote its documents in German. That reasoning was
correct. The consequence was not foreseen: once the grid is where the machine looks, every
piece of prose that needs to be machine-adjacent gets written into a cell. The document
degrades one paragraph at a time, and each individual paragraph looks reasonable when it
is added.

**Fix:** Anchor + YAML block instead of column position. An entity is a heading carrying
its id, its machine fields are one fenced `yaml` block, its prose is in anchored sections.
Same language independence — anchors and YAML keys are ASCII and never translated — with
nothing pulling prose into a grid. Tables go back to short values and are held to a budget
lint measures: 4 columns, 80 characters, 3 rows, no `<br>`, no bold past 40 characters.

**Severity:** Critical.

**The generalizable half:** a format decision propagates into content. Choosing where the
machine reads decides where humans write, and the second consequence arrives months after
the first and looks like a discipline problem rather than a design one.

## 2026-08-25 — migrate.py: four defects a dry run found that no reading would have

**Problem:** The v1→v2 converter passed review and then, run against a copy of the live
project, produced four wrong outputs — each of which read as correct in the code.

1. A pipe inside a code span split a row. `` `app | migrate | postgres` `` parsed as three
   cells, silently truncating the milestone that contained it. The row still looked like a
   row afterwards.
2. Bold inside a cell was banned outright, which failed a legitimate two-column priority
   legend (`| **критично** | без этого пилот не запускается |`). Bold on a short cell is a
   term; bold in a long one is prose in a grid. The rule needed a length, not a token.
3. The screens table's "who sees it" cell said **`все без входа`** — Russian prose, not
   ids. Splitting it on whitespace produced three role ids that exist nowhere. **A
   fabricated id is worse than an empty field**, because every cross-reference check
   downstream believes it and reports green.
4. Triggers were given slugs derived from their English titles while the spec already held
   their real ids.

**Fix:** code spans masked before splitting; the bold rule gated on cell length; role ids
taken only from the ones the spec declares, with anything else preserved verbatim in a
`_TODO —` marker; names matched against the spec before slugging.

**Severity:** Major — 3 and 1 are silent, which is the class that matters.

**This is the second time this lesson has been paid for.** The 2026-08-24 entry says a
reviewer checks whether a sentence is true and only an executor discovers that a rule
cannot be satisfied. The same holds for a converter: reading it confirms the transformation
is described correctly, and only running it on real material shows what the material
actually contains. Budget the run.

## 2026-08-25 — client-package: a positional id is not an address

**Problem:** v1 numbered acceptance bullets positionally *within each package*: `C-04.2`
meant "the second bullet in this file". Its own docstring defended this — safe because
`handoffs/` is immutable and `log.md` records which version went out. It is not safe. The
moment a bullet is inserted above another, the client's next package renumbers everything
below it, and a client quoting `C-04.2` from memory or from an earlier email points at a
different sentence. The immutability of the handoff protects the old comment; it does
nothing for the conversation that continues afterwards.

**Fix:** ids allocated from the document's own order (`C-04.a3`, `coach-today.f2`),
identical across rebuilds, verified by diffing the id set of two runs.

**Also fixed here:** the SKILL promised the package carried four documents and named why —
"handing over three of them and keeping the fourth back is how a client reviews a product
they have not seen". Its builder opened two. The gap survived three releases because the
sentence explaining the rule and the code implementing it were in different files and only
one of them was ever reread.

**Severity:** Major.

## 2026-08-25 — README, sync/, ROLES.md: what an inventory drifts into when nothing checks it

**Problem:** Nineteen structural defects found by auditing the plugin against itself.
The sharpest four:

- `README.md` was declared `generated` in the contract, `render-docs` promised to build it,
  the `/render` command named it — and no generator existed. Lint rule 12.18 ("re-render
  every generated document and compare") was therefore **unsatisfiable for that document
  across three releases**, which means it was either not firing or permanently red, and
  nobody could tell which.
- `skills/sync/` was an empty directory with no `SKILL.md`, while `/macstack-dev:sync`
  existed and carried its instructions inline.
- `ROLES.md`, deleted in v1.8, still lived in `plugin.json`, `commands/render.md` and
  `render-docs/SKILL.md`.
- The README listed 18 skills of 22 and 13 commands of 17; `plugin.json` and
  `marketplace.json` disagreed on keywords, 27 against 14, in a plugin whose own rules
  require parity.

**Fix:** all nineteen. The generators now exist for every document the contract calls
generated; the README is verified against `ls skills/` and `ls commands/` rather than
maintained by hand.

**Root cause:** every one of these is a claim about the plugin's own contents that nothing
checked. The plugin lints the projects it manages and lints nothing about itself.

**Severity:** Major.

**Idea worth building:** the check is three lines of Python — does every skill directory
hold a `SKILL.md` whose `name` matches it, does every path referenced in a skill exist,
does every document the contract calls `generated` have a generator, do the two manifests
agree. It belongs in `/macstack-dev:feedback` or in CI.

## 2026-08-27 — documents/lint: a format change carried only as far as the reader

**Problem:** v3 — pure markdown, no yaml, no tables — was implemented in the parser and
then abandoned. Six scripts still imported the v2 parser, which against a v3 document
filters by `Block.kind` and finds nothing. It returns **empty, not an error.** So
`/review` would have built a package with zero items, `/plan` would have called all 78
cases unplanned, `/sync` would have called every entity deleted, and `/start` would have
seeded yaml into a folder whose own rules forbid it. Nothing failed. Everything passed.

The same defect class then recurred five more times in one week: the port agents
reintroduced it twice; repointing the case pointers made 35 rules run over an empty list
and all 35 passed; rule 12.18 kept a stale copy of the render job list; rule 12.2 had no
implementation at all; rule 12.36 was documented in SKILL.md for three releases with no
code behind it; and the client package's own JS collected zero answers because it still
queried `tr[data-id]` after the switch to cards.

**Fix:** all six consumers ported. Rule 12.0 added as the guard: for every entity kind
the contract declares in a document, the loader must return at least one. Rules 12.36 and
12.38 implemented. A three-line cross-check now compares `@rule(...)` in the code against
the rule list in SKILL.md; before it, they differed by two.

**Root cause:** every parser here returns empty on a shape it does not recognise, and
empty is indistinguishable from "checked, and it was fine". A format change that cannot
break compilation must be made to break a rule instead.

**Generalisation worth keeping:** a check that can return "nothing to check" must be able
to say which of the two it means. Where it cannot, it is decoration — and decoration that
prints green is worse than no check, because it is believed.

**Severity:** Critical

## 2026-08-27 — client-package/commands: the loop existed, the command did not

**Problem:** the closed client loop was built and working — the page collects answers,
`read_answers` writes them into the ledger, the next package pre-fills them. But it was
explained to the owner as `package.py macstack --read answers.json`. The owner's reply:
"я тебя просил сделать понятные команды в плагине macstack-dev." Correct. A plugin whose
capability is reachable only by knowing a script path and its flags does not have that
capability in any sense that matters.

Alongside it, three documents stated things that were no longer true: `README.md`
described the v2 shape the owner had rejected, `client-package/SKILL.md` described
positional bullet numbers and told the reader to append to `history/log.md` (archived),
and the marketplace description advertised yaml blocks to buyers.

**Fix:** `/macstack-dev:review --read <file>` documented as the path, and it accepts text
pasted into the chat — written to `inbox/` first, so the correction has a traceable
source. `/macstack-dev:inbox` renamed `/macstack-dev:intake`: there are three sources and
"inbox" named one. README, SKILL and both manifests rewritten to v3; version 3.0.0.

**Root cause:** the work was measured by whether the code ran, not by whether a person
could reach it. Those are different questions, and only the second one is delivery.

**Severity:** Major

## 2026-08-27 — planning: a queue with an unfinishable item in it is not a queue

**Problem:** `TASKS.md` was allowed to hold a task that cannot be finished without an
answer from the client. The mechanism for it was deliberate — a `blocked` status and a
`blocked_by` field carrying `A<n>` ids, and `uncovered.py --emit` filled `blocked_by`
from the case's open items on purpose. The owner: *«в файле TASKS должны быть задачи
которые уже квалифицированы и не требуют уточнения у клиента… это надо что бы выполнять
TASKS и не было блокеров, не ждать ответа от клиента»*.

They are right, and the failure is one a status field cannot reach. A person opens the
file, takes the top item and starts. `blocked_by` is discovered two hours in, if it is
read at all — by then the branch is open and the work is half-done. Measured on
`ohawo-payload-nextjs` the same day: `M15-T7` sat as `backlog` next to twelve runnable
tasks, and its own text named `A20` and `A26`. Nothing on the row said so. Worse, this
project's `TASKS.md` uses the five Plane statuses (`backlog · todo · in_progress · done ·
cancelled`) and has **no `blocked` value at all**, so the escape hatch the standard
provided did not exist there — a project can adopt a tracker's vocabulary and silently
lose the one status the rule depended on.

**Fix:** a requirement that depends on an unanswered client question does not become a
task. `uncovered.py` splits the fourth state in two — *not planned and not checked* stays
the work, *awaiting the client* is reported separately, gets its own section naming the
`§A` ids, and **`--emit` withholds its skeleton and prints how many it withheld**. The
skeleton no longer carries `blocked_by` at all. `planning/SKILL.md` opens with the rule,
adds it as a fourth refusal, and routes such work to `§A`; `commands/plan.md` mirrors it;
`i18n.py` gains `cases_await` in all four languages. `blocked_by` survives for INTERNAL
blockers — another task, a fired `§B` trigger — because those a team can clear itself.

What keeps the work visible is the `§A` item's own *where the answer goes* line: it
already names the screens and behaviour the answer unlocks, so absence from `TASKS.md` is
not cancellation.

**Root cause:** the rule was written as a property of a ROW (`status: blocked`) when it
is a property of the FILE. `TASKS.md` is read as a queue — top item, start working — and
a queue is trusted or it is not used. Any design that makes the reader check a field
before trusting the list has already lost the property the list was for. Same class as
the positional-id defect of 2026-08-25: correct data, reachable only by somebody who
knew to look.

**Severity:** Major

## 2026-08-27 — uncovered.py: the document moved to v3, the reader did not

**Problem:** `/macstack-dev:plan` reported **8 cases with no plan** on a project whose
`TASKS.md` holds thirteen tasks — and all eight were already planned, by name. Had the
report been believed, it would have produced eight duplicate tasks pointing at cases that
already had one.

Cause: `uncovered.py` reads `TASKS.md` through `mdblocks.entities(blocks, 'task')`, which
needs the v2 shape — a `<!-- macstack:task=M15-T1 -->` anchor plus a fenced yaml block.
This project's file is already v3: `### M15-T1 · Название` with bullets. `entities()`
found nothing and returned an empty list **silently**, so every case looked unplanned.
The script's own docstring even records the decision — *"`TASKS.md` … still read through
`mdblocks` — they carry their own migration later"* — but nothing checked whether a given
file had migrated ahead of the reader.

Same failure class as the v3 port of `USER-CASES.md` two days earlier, which reported all
78 cases unplanned for exactly the same reason. It was fixed there and not generalised.

**Fix:** read `TASKS.md` through `v3.load` first and fall back to `mdblocks` only when v3
finds no task ids — the reverse order would keep the silent-empty path alive. The v3
shape carries the case link in the `Закрывает` / *Closes* bullet, which lands in
`fields['closes']`, so it is mapped onto `spec` for everything downstream. Verified on
the live corpus: `12 planned · 46 audited done · 20 partial · 0 unplanned`, and the four
numbers now sum to 78, which they did not before.

Also: a case whose only task was **withdrawn** still counts as planned — withdrawal is a
decision, and its reason is written in the struck task — but it is now printed in its own
`planned once, then withdrawn` section. Counting it silently would let cancelled work
vanish; counting it as unplanned would re-propose exactly what a human just withdrew.

**Root cause:** an empty result from a parser was treated as "nothing there" instead of
"I could not read this". A reader that cannot tell those two apart turns a format
migration into a wrong number, and the wrong number is confident. Where a probe can come
back empty for two different reasons, it must say which — the same rule lint 12.0 already
states for conventions that match zero files.

**Severity:** Major


## 2026-08-27 — client-package, one session on OHAWO: six defects, and five of them were silent

The session set out to build one review package and ended with six fixes. Every one of the
first five had the same shape: **the page told the client something the code did not do**,
and nothing in a test, a log or an exit code said so. That shape is the finding.

**1 · "Marked yellow: changed since the last package" marked nothing.** `since` is the
previous package's DATE, ledger rows are dated by day, and a package is rebuilt on the same
day the documents were edited — so `>` dropped every change made that day. Measured: 16
entities had genuinely moved (8 new, 8 with new text), `0 of 209` were marked, and the page
went on promising yellow. Fixed by comparing `>=`. A day is the whole precision available,
so an error is unavoidable; the error was chosen toward OVER-marking. A spurious mark costs
the client a second look at something already seen (2 of 18 on the same measurement); a
missed one costs an edit the client never reads, which is the entire reason the mark exists.
**Severity: Major.**

**2 · The scaffolder's own prompt was shipped to the client as content.** `seed.py` writes
each unfilled procedure as an italic hint. Until somebody writes the procedure, that hint is
the whole body — so an untouched `HANDBOOK.md` became a section of 41 headings each reading
*"describe the steps of this procedure"*, an instruction addressed to US, with no answer
field under any of them. `_is_stub` now drops an entity that holds nothing but its hint, and
only where the entity has no id, so no case, screen or question can pass through it. The
condition is deliberately narrow — an italic line among real text is the author's emphasis
and stays, because silently deleting words the client wrote is worse than a visible stub.
Nothing to remember and re-enable: `collect` already drops a section with no entities, so it
returns by itself the day the first procedure is written. Proven by mutation both ways.
**Severity: Major.**

**3 · An unknown flag was ignored in silence.** zsh does not word-split an unquoted
parameter, so a whole argument set reached the parser as one string, no flag was recognised,
and the command built the DEFAULT package under the DEFAULT slug and journalled it as a
completed round — moving the "changed since" baseline for the next one. The empty package is
visible; the moved baseline is not. Flag names are now checked against a whitelist and an
unknown one is refused, the way section names already were. **Severity: Major.**

**4 · §B reached the client only by accident of punctuation.** The questions section filtered
on "has an id", and §B — the work the team deferred — failed that test only because its
headings use `B1 — …` while §A uses `A1 · …`, and the id parser does not know the dash. The
first §B item ever typed with a middle dot would have gone to the client as a question about
our own backlog. It now selects on the pointer the contract already defines,
`lifecycle.needs_from_client`, which is the actual semantics: §A is what the client owes.
**Severity: Major.**

**5 · A one-section package spoke the whole package's language.** Splitting the package
(`--only` / `--skip`, added this session) made the questions a document of their own, and its
opening line still read *"each block is one claim about the platform — mark it right, not so
or a question"*, with the answer field labelled *"a comment, if you have one"*. Against
"give us your company's invoicing details" that is nonsense, and it is the first line the
reader sees. A section may now carry its own `howto_<section>` and field label; one without
falls back to the shared text. The same package also showed `USER-CASES.md`'s version — a
version that would not move when the questions themselves were rewritten. **Severity: Minor.**

**6 · The build output was the least clear thing in the loop.** Two consecutive `if artifact:`
blocks printed the same instruction in English and then in Russian, the header line was
English and the "next steps" block was Russian regardless of `docs.language`, and nothing
anywhere said the one thing that matters: `-artifact.html` is a body, not a page — it has no
`<html>` and no `<body>`, a browser will not render it, and it must never be sent to a
client. The output is now single-language, states what each file is and is not, prints the
exact `file_path` for the Artifact tool, and prints the command that records the returned URL
(`--record-url … --handoff …`) instead of leaving somebody to hand-edit a 200-line JSONL —
which happened three times in this one session, each time with a throwaway script nobody
reviewed. **Severity: Minor, and it is the one the user reported.**

**Root cause, common to 1, 2, 4 and 6:** the package is a document that makes CLAIMS about
itself — "yellow means changed", "these are the steps", "these are your questions", "here is
what to do next". Nothing checked a claim against what the code produced, so each stayed
wrong for as long as nobody read the output beside the input. Where a generated page asserts
something about its own contents, that assertion needs a test, or it is a comment that
happens to be printed.

**Residual:** the `--read` path has still never run on real client answers — 13 `handoff`
rows in the OHAWO ledger and 0 `comment` rows. Everything about pre-filling a previous
verdict is therefore argued and not measured.

## 2026-08-27 — тесты плагина ходили в чужой рабочий проект по абсолютному пути

**Проблема.** `skills/documents/references/tests/test_v3_writer.py` искал документы по
пути, вписанному в код: `/Users/<имя>/…/ohawo-payload-nextjs/macstack/client`. Имя
пользователя и название клиентского проекта — в публичном репозитории.

Ломалось это двумя способами сразу, оба замерены:

- **На той машине** — 15 тестов, один красный. Числа переписи сняты с живых документов
  2026-08-26, а документы законно растут: триггеров стало 61 против 57, вопросов 28
  против 26, экранов 39 против 37. Тест, который краснеет от нормальной работы, читать
  перестают, и тогда он не защищает ничего.
- **На любой другой** — каталога нет, `glob` пуст, `DOCS` пуст, и **двенадцать тестов из
  пятнадцати просто не создаются**: они порождаются по документам. Прогон печатает
  `Ran 3 tests ... OK`.

Второе хуже первого. Тест не падал у чужого — он молча переставал существовать, и
результат выглядел как успех.

**Фикс.** Свой корпус в `tests/corpus/`: выдуманный прокат велосипедов, шесть
документов, минимальные, но настоящей формы — со всеми тремя видами привязки
указателя, ради которых перепись и написана (тождество, контейнер, отсутствие).
Перепись перебазирована на него. Пустой корпус теперь **останавливает прогон** с кодом 1
вместо трёх зелёных тестов. `MACSTACK_FIXTURE` сохранён — по нему тесты гоняются против
настоящего проекта, — но перепись там пропускается: она описывает свой корпус, и красить
её на чужом было бы шумом, а не сигналом. Плюс `assert` при загрузке: состав `corpus/` и
состав `CENSUS` не могут разойтись молча.

**Корневая причина.** Та же, что и у всей записи выше про `client-package`: пустой
результат чтения принят за «там ничего нет» вместо «я не смог это прочитать». Разница
только в том, что здесь это случилось с самим набором тестов, поэтому обнаружить было
нечем — сломанный детектор не сообщает о своей поломке.

**Тяжесть:** Major — на любой машине, кроме одной, набор тестов был декоративным.

## 2026-08-27 — кнопка «Собрать мои ответы» не работала НИ РАЗУ, и это объясняет пустой журнал

**Проблема.** Скрипт пакета читал две константы — `PKG_DATE` и `COUNTED`, — которых
сборщик никогда не выводил в страницу. Первая же строка `save()` собирает JSON с
`date: PKG_DATE`, поэтому нажатие давало `ReferenceError: PKG_DATE is not defined` и
умирало ДО того, как что-либо попадало в поле. Третьим было то, что элемента
`id="cnt"`, в который скрипт пишет число собранных ответов, в разметке не существовало
вовсе.

Итог: обратная половина клиентской петли не работала ни в одном пакете, который этот
плагин когда-либо выпустил.

**Почему не заметили.** Исключение в обработчике клика ничего не показывает тому, кто
нажал: поле просто остаётся пустым. И в журнале OHAWO это выглядело как «клиент не
отвечает» — тринадцать строк `handoff` и ноль строк `comment`. Запись выше по файлу
называет ноль ответов «остаточным риском: путь `--read` не измерен». Настоящее
объяснение было проще и хуже: возвращать ответы было нечем, и мы приняли сломанный
механизм за молчание заказчика.

**Фикс.** Константы объявляются перед скриптом (`PKG_DATE`, `COUNTED`, плюс `EMPTY` для
случая «ничего не отмечено» и `COPIED` — только после подтверждённого копирования).
Элемент `#cnt` добавлен в разметку и в стили. Обработчик вешается из скрипта, а не
атрибутом `onclick`: инлайновый атрибут запрещён политикой безопасности строже той, при
которой сам скрипт ещё выполняется, и кнопка тогда молчит опять. Копирование пробует
`execCommand`, затем `navigator.clipboard`, и в обоих случаях текст виден и выделен —
сообщение не обещает, что скопировано, пока это не подтвердилось.

**Проверено настоящим браузером, в обе стороны.** До: `PKG_DATE is not defined`, поле
пусто. После: 0 ошибок, поле заполнено, подпись «Собрано ответов: 3». И впервые
пройдена вся петля целиком — то, что выдала кнопка, скормлено `--read --dry`, который
разобрал три ответа с верными вердиктами и комментарием.

**Корневая причина.** Единственный кусок этого продукта, который ИСПОЛНЯЕТСЯ у
читателя, а не только читается, был единственным, который никто ни разу не исполнил.
Все проверки пакета работали с его текстом: считали пункты, искали утечки, сверяли
разметку. Ни одна не открыла страницу и не нажала кнопку. Сборка HTML, содержащего
скрипт, требует прогона в браузере — иначе проверяется вёрстка, а не работа.

**Тяжесть:** Critical — механизм, ради которого пакет и существует.

## 2026-08-27 — у `client-package` не было ни одного теста, и прогона тоже не было

**Проблема.** Кнопка чинится одной правкой (запись выше), но гарантии, что она не
сломается снова, не появляется: у `client-package` проверок не существовало вовсе. А
два тестовых файла, которые в плагине были, нигде не упоминались — ни в README, ни в
одном скилле. Проверка, которую никто не запускает, ничем не отличается от её
отсутствия.

**Фикс — четырнадцать тестов и общий прогон.** Класс дефекта («скрипт читает то, чего
страница не объявляет») ловится статически и целиком, без зависимостей:

- каждая ЗАГЛАВНАЯ константа, которую читает скрипт, должна быть объявлена в нём же —
  это ровно `PKG_DATE`. Проверяется соглашение, а не список известных имён: список
  пришлось бы помнить, и следующая забытая константа прошла бы так же молча;
- каждый `getElementById('x')` должен находить `id="x"` в разметке — это `#cnt`;
- обработчик вешается из скрипта, а инлайнового `onclick` в разметке нет;
- селектор `collect()` совпадает с тем, что пишет разметка — прошлый раз они разошлись
  при переходе на карточки, и пакет собирал ноль ответов;
- скрипт синтаксически валиден (`node --check`, пропускается без node — единственная
  проверка с посторонним исполнителем, и потому единственная необязательная);
- тело артефакта не содержит `<html>`/`<body>`, файл содержит, а кнопка и скрипт есть в
  обоих;
- `--only` + `--skip` дают в сумме целый пакет; §B не уходит клиенту; заготовка
  генератора не считается содержимым; неизвестный ключ и неизвестный раздел отвергаются;
- формат, который печатает кнопка, разбирается `read_answers` — обе половины петли
  связаны проверкой, а не намерением.

**Все восемь доказаны мутацией**: убрать объявление `PKG_DATE`, убрать `#cnt`, вернуть
`onclick`, разойтись селектором, сломать синтаксис — каждая правка красит ровно свой
тест и только его. Прогон `run-tests.sh` тоже проверен поломкой: на сломанном
`package.py` он возвращает 1.

**Три бага в самом прогоне, каждый пойман на себе же** — и все три того же класса, что
и правленые сегодня: `mapfile` (bash 4+, macOS даёт 3.2); `for f in $(find …)`, который
разбил путь к плагину по пробелу в «CONTEXT PACKS» на два несуществующих файла; и
`while` в конвейере — он идёт в подоболочке, и счётчик падений наружу не возвращался,
то есть прогон рапортовал бы успех при упавших тестах.

**Корневая причина.** Единственный кусок продукта, который ИСПОЛНЯЕТСЯ у читателя, был
единственным, который никто ни разу не исполнил. Всё, что проверялось, проверялось
чтением текста страницы.

**Тяжесть:** Major — без этого починка кнопки держится на том, что её больше никто не
тронет.
