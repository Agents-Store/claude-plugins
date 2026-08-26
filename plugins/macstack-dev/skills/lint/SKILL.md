---
name: lint
description: This skill should be used when the user asks to "validate macstack.json", "lint macstack", "check the stack spec", "verify macstack.json integrity", "check the documents", "where are we", "what should I do next", "project status" — and after any skill of this plugin writes or edits macstack.json or a document under macstack/. Validates the spec against the JSON Schema and the referential-integrity rules, checks the document folder, and reports the same findings read-only as a status dashboard.
---

# Check the spec, the folder, and where the project stands

Three passes over the spec and the folder, and one read-only view of the result.

A file that fails lint must not be scaffolded from.

Resolve the path first: `macstack/macstack.json` (canonical) → `./macstack.json`
(legacy fallback). Both present is a setup error — stop instead of picking one
silently.

**Prefer the reference linter** — it implements passes 1 and 2 and is maintained with
the standard:

```bash
MACSTACK_JSON="macstack/macstack.json"; [ -f "$MACSTACK_JSON" ] || MACSTACK_JSON="macstack.json"
curl -fsSL https://raw.githubusercontent.com/macstacks/macstack/main/scripts/lint.py \
  -o "${CLAUDE_PLUGIN_DATA}/lint.py" 2>/dev/null || true   # cache; keep the old copy offline
python3 "${CLAUDE_PLUGIN_DATA}/lint.py" "$MACSTACK_JSON" \
  --schema https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json \
  --categories https://raw.githubusercontent.com/macstacks/registry/main/software-categories.json \
  --coverage-areas https://raw.githubusercontent.com/macstacks/registry/main/coverage-areas.json
```

Pass 3 is this plugin's own and has no upstream equivalent — run it either way.

Offline fallback: run all three passes manually with the bundled copies.

## Pass 1 — JSON Schema

Fetch the live schema first (it may be newer than the bundled copy); cache it in
`${CLAUDE_PLUGIN_DATA}`; offline → bundled
`${CLAUDE_PLUGIN_ROOT}/skills/lint/references/macstack.schema.json`.

```bash
python3 - <<'PY'
import json, jsonschema, urllib.request, os
URL = "https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json"
try:
    schema = json.load(urllib.request.urlopen(URL, timeout=15))
except Exception:
    schema = json.load(open("<PLUGIN_ROOT>/skills/lint/references/macstack.schema.json"))
path = "macstack/macstack.json" if os.path.exists("macstack/macstack.json") else "macstack.json"
jsonschema.validate(json.load(open(path)), schema)
print("schema: VALID")
PY
```

**Compare revisions before trusting a difference.** Both copies carry a `$comment`
starting `rev <n>`. If the fetched one is older than the bundled one, the bundled copy
is ahead of the canon on purpose and must not be overwritten — and a `curl` against
`raw.githubusercontent.com` immediately after a push serves the PREVIOUS revision from
the CDN, which prints a full, entirely false diff. Use
`gh api repos/macstacks/macstack/contents/<path>?ref=main` when the answer matters.

No `jsonschema` lib → fall back to structural checks (required: macstack, name,
version, description; the known enums) — and tell the user that full validation was
skipped.

## Pass 2 — Referential integrity (errors)

1. `results[].produced_by[*]` ∈ processes; `processes[].produces[*]` ∈ results —
   result-first: a process with no result is "coding for coding's sake".
2. `results[].goal` ∈ goals.
3. `tasks[].workflow`, `workflows[].software`, `entities[].stores[].software`,
   `interfaces[].software|related[*]`, `connections.mcp[].software` resolve
   (own ids, ids inherited from the prototype, or cross-stack).
4. `entities[].master` appears in stores exactly once with the master role.
5. **Triggers**: `workflows[].triggers[*]` ∈ triggers; `triggers[].software` ∈
   software, `instance` ∈ its instances.
6. **Instances**: `stores[].instance`, `mcp[].instance` ∈ the instances of the
   matching software; `interfaces[].instances[*]` ∈ the instances of its software.
7. `software[]`: category ∈ the registry
   (`references/software-categories.json`), type filled, layers ⊆
   {data, logic, interface, infrastructure} without duplicates, `agentic.rating`
   consistent (3×true=full, 2=good, 1=basic, only partial=partial, nothing=none).
8. **Cross-stack**: the `<stack-id>:` prefix is declared in `stacks.root.id` /
   `stacks.substacks[].id` / `stacks.links[].id`; `role: substack` → `root` present.
9. **Agents**: `stack_agents[].access[*]` ∈ mcp|software|interfaces;
   `delegates_to` only downward (control_plane → orchestrator → worker);
   `context_packs[*]` ∈ context.packs; `managed_agents[].tools.*` resolve;
   `invocations[*].interface|workflow|trigger` resolve.
10. **Env**: `resources.accesses[].env` holds NAMES, not values (a string that looks
    like a secret/token is an error); slugs are kebab-case; `prototype` has no cycles.
11. **Plugin coverage**: `context.plugins.*[].covers[*]` ∈ the coverage registry
    (`references/coverage-areas.json`); `scope[*]` resolves to a declared id in
    software / entities / workflows / triggers / interfaces / connections.mcp.

## Pass 3 — The `macstack/` folder (rule group 12)

Active only when macstack.json has a `docs` section, or a `macstack/` folder exists
on disk. Errors block scaffolding exactly like Pass 2; lint red on a document that
reads fine usually means stripped anchors (see `troubleshoot`).

**Run it — this pass is a program now:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/lint/references/lint_folder.py" macstack \
  [--rule 12.3 ...] [--warnings] [--json]
```

Exit 0 clean, 1 errors, 2 could not load. Rules live in `references/lint_folder.py`
and the `references/rules_*.py` modules beside it, which register themselves on import.

Until v3 this pass was prose and nothing executed it, which is why 12.21 demanded a
fenced `yaml` block from documents that contain none and never once said so, and why
12.18 was unsatisfiable for `README.md` across three releases with no way to tell
whether it was failing or simply not running. **A rule nobody can run is not a rule.**
If you add one here, add it there in the same change.

Read the shape from
`${CLAUDE_PLUGIN_ROOT}/skills/documents/references/doc-contracts.json` — every rule
below is checked against that file, never against memory.

### Layout and identity

12.0 **A declared entity kind is actually found** — for every entity kind the
     contract declares in a document, the loader returns at least one. This rule
     protects the other thirty-eight from the failure that keeps recurring here: a
     filter that matches nothing returns an empty list, thirty-five rules run over it,
     and every one of them passes. A green report and a broken folder look identical.
     It has fired for real: after the schema gave cases their own records and the
     pointers were repointed from `roles[].cases` to `cases[id=…]`, the kind filter
     still matched the old collection and silently returned zero.
     Any rule that can return "nothing to check" must be able to tell that apart from
     "checked, and it was fine" — otherwise it is decoration.

12.1 **Layout** — `docs.root` resolves and holds exactly SIX entries: `README.md`,
     `macstack.json` and the four folders `client/`, `generated/`, `inbox/`,
     `history/`. Dot-files do not count — `.DS_Store` and friends are the operating
     system's litter, not the project's documents, and failing a folder for them
     teaches people to ignore the rule. A seventh real entry is an error, not a
     preference. Every document in the contract whose `path` is a FIXED NAME exists at
     that path. Documents whose `path` carries a `<placeholder>` (`delta`, `rulings`,
     `review`) are dated instances, not required files — their directories are created
     lazily and their absence in a fresh folder is correct.
     **`docs.files` must name every fixed-path document.** Checking only that the
     entries present resolve is a rule that passes in a vacuum: `docs.files` is
     authored, so naming nothing at all used to approve an empty folder.
     Exactly one `macstack.json` in the repo.
12.2 **Headers and pointers** — each document carries its `<!-- macstack:doc= -->`
     header, and every entity heading carries a `<!-- macstack:ref= -->` pointer unless
     its contract puts it in the reserved `none` class. The per-kind anchors of v1 and
     v2 (`macstack:case=`, `macstack:screen=`) are gone: there is one pointer form, and
     what it means is decided by the binding its contract declares — see 12.28 and 12.29.
12.3 **ID integrity** — unique per space; ASCII-only inside an ID token — the homoglyph
     rule: a Cyrillic capital KA (U+041A) renders exactly like `K` (U+004B), greps as
     absent and silently breaks every cross-reference check, so compare codepoints
     rather than glyphs; no gaps in D-numbering; A/B numbers never reused after a
     strike.
12.4 **Cross-file refs** — every `D<n>` cited anywhere resolves in `DECISIONS.md`;
     every `A<n>` **and every `B<n>`** in `lifecycle.*` resolves to a live item; every
     `roles[].cases` prefix yields ≥1 case heading; every case-section letter maps to
     exactly one role; every `<case>.T<n>` carries a case that still exists; every
     `covers` in `TEST-CASES.md` names an acceptance id that still exists; every
     `blocked_by` in `TASKS.md` resolves to a live task or open item; every `screens`
     entry in a case resolves to a screen in `UX-UI.md`; every `triggers` entry
     resolves to a trigger in `AUTOMATION.md`.
12.5 **Checked copies** — `open_questions[].summary` equals the first sentence of its
     markdown item; for every versioned document, `docs.files.<key>.version` equals the
     version in the document's own header. Two places now, not three: the journal row
     was the third, and client documents no longer carry a journal (12.33).
     The old three-way check passed on a document declaring `version=3.0` in its header
     and "Версия 1.8" in its body, because the journal matcher only recognised one row
     shape and the v3 rows were invisible to it. A comparison that cannot see one of its
     operands reports agreement.
12.6 **`needs_from_client` is a view** — contains no closed items, omits no open §A
     client item.

### Shape (v3)

12.21 **Entities parse** — every entity heading matches its contract's `id_pattern`,
      carries every `bullets_required` label for its kind and no label the contract
      does not declare for it, and carries every `prose_required` block — with the
      conditional sets applied by the entity's own values. `bullets_conditional` reads
      "required unless": a screen must name its roles unless it declares itself public.
      `prose_required_except_prefix` reads by id: a `Z-` prohibition needs no acceptance
      list, because it states what must be refused and the refusal is the behaviour.
      `bullets_forbidden` is the mirror image: a case may not carry a `role` bullet,
      because the role is already the pointer one line above, and a second copy of a
      fact is the hand-maintained duplicate 12.27 exists to stop.
      Two formats died to get here. v1 read table columns BY POSITION — deliberately,
      because a header follows `docs.language` — and every paragraph that needed to sit
      near the machine moved into a cell. v2 replaced the grid with an anchor plus a
      fenced yaml block, and left markdown, yaml and tables stirred together in one
      file. v3 keeps the language independence and drops the machine syntax entirely.

12.28 **Every pointer resolves** — every `<!-- macstack:ref=P -->` resolves to a live
      path in `macstack.json`. `coll[]` is the whole collection; `a[].b[]` is the union
      of `b` over every `a`. Name the file, the line and the first segment that failed.

12.29 **The pointer binds the way its contract declares** — and this is the rule that
      looks simpler than it is. `identity`: the last `[id=…]` equals the heading id.
      `member`: the heading id satisfies the glob at the pointed path. `container`: the
      pointed entry exists and the heading id is unique in the document. `none`: no
      pointer at all, and the id prefix is one the contract reserves.
      Measured on a live project: AUTOMATION.md is 49 headings, 49 pointers and 49 id
      matches; UX-UI.md is 37 screens onto 9 `interfaces[]` entries; USER-CASES.md is 78
      headings, 51 pointers, 3 distinct targets and **zero** id matches, because
      `roles[].cases` holds the glob `"C-*"`. Assume identity is the only binding and
      one of two things follows: somebody invents 28 spec entries that nothing else
      references in order to satisfy the linter, or the rule is downgraded to a warning
      and stops catching the genuinely broken pointer in the document where it was true.

12.30 **A client document is headings and bullets, and nothing else** — zero fenced
      blocks, zero table rows, zero HTML other than the two macstack comments, no
      heading deeper than `####`. Applies to every document whose audience is `client`
      **or `both`**. There is no budget here and no exemption; 12.24's budget survives
      only where the reader is a machine or a programmer.
      `both` is not a loophole: OPEN-QUESTIONS.md is `both` because §A is owed by the
      client and §B is the team's, and classifying it that way quietly exempted it from
      every rule protecting the client's reading. It carried a journal for weeks.

12.31 **Every bullet label is declared** — `- **X:**` reverses through
      `fields.*.label`, `label_by_kind` or `label_aliases` for the document's language.
      An undeclared label is prose that happens to be bold, and the parser leaves it as
      prose rather than inventing a field from it — but the linter says so, because the
      alternative is a key in the model that nothing reads.
      This fired 103 times on first run against a corpus everyone believed was clean:
      the shipped table said "что требуется от человека" while all 33 live bullets say
      "что от человека требуется" — the same words, transposed.

12.33 **A client document carries no journal** — no `## История изменений` section and
      no `- **Версия N · date**` row. History lives in `history/`, and the client sees
      it per statement in the review package rather than as a wall of versions at the
      bottom of every document.

12.34 **Pointer uniqueness** — no two headings share an `identity` pointer. A
      `container` pointer may repeat; that is what makes it a container.

12.32 **Acceptance ids are stable** (warning) — a case's acceptance bullet count is
      not below what it was at the last tag unless the document version was bumped.
      The ids are positional within their entity, so inserting a bullet above an
      existing one moves every id below it — and a client quoting `C-04.a2` from an
      email last month then lands on a different sentence. When there is no tag to
      compare against, the rule reports nothing and says so rather than guessing.

12.35 **`generated/` carries everything `client/` says** — every id appearing in a
      client document also appears in `generated/REQUIREMENTS.md`, and the acceptance
      bullet counts match. This is what makes "absolutely all of it, in machine form"
      a check instead of a promise. While `REQUIREMENTS.md` does not exist, the rule
      emits one finding saying so — not one per id.

12.36 **A document that moved has a row in the ledger** — an authored client
      document declaring a version in its header has at least one row in
      `history/ledger.jsonl` that names it. The ledger is what lets the review package
      show a client, per statement, what moved since they last read it and what they
      said about it; an edit with no row means the next package presents a changed
      sentence as if it had always said that.
      What this checks and what it does not: it compares the document against the
      ledger at file granularity, not edit by edit — proving that EVERY individual
      edit was recorded would need the git history, and a rule that claims more than
      it measures is worse than no rule. Generated documents are exempt: their edits
      belong to their generator, and 12.18 covers those.

12.37 **The first bullet is not the heading again** — an entity whose opening bullet
      restates its own title makes the client read the same sentence twice. Twenty-two
      of thirty-six blocks in one live document did exactly that.

12.38 **`client/` holds documents, and nothing else** — any file there that is not one
      of the six is incoming material: a client's own draft, a screenshot, a `.docx`
      saved beside the documents. Its place is `inbox/`, where it is immutable and has
      a manifest row, and from there `/macstack-dev:intake` merges it.
      Leaving it in `client/` creates a seventh document that no renderer, no package
      and no spec knows about — and a month later nobody can say whether it is a
      source of truth or somebody's draft.

12.39 **A workflow's `source` path still exists** — `workflows[].source` says where the
      workflow lives in code. Rename or delete the file and the field stays behind, and
      the next audit reports green against a path that is gone. An empty `source` is not
      an error — the workflow may not be written yet; a filled-in wrong one is.
      The field exists because names do not bridge the two sides: measured on a live
      project, code names a workflow for its domain and the spec for its step, and only
      3 of 17 match. A link that cannot be derived has to be stored, and a stored link
      has to be checked — otherwise it is worse than none, because it is believed.

12.24 **Tables stay inside the budget** — in `history/` and `generated/` only; in
      `client/` a table is an error outright (12.30). At most 4 columns, at most 80
      characters a cell, at least 3 rows, and no `<br>`, bold, code fence or pipe
      inside a cell. Report the file, the table's anchor or heading, the column
      count and the longest cell verbatim, because "this table is too wide" is not
      actionable and "cell 4 of row 12 is 876 characters" is.
      The budget exists because every oversized table measured in the field started as
      a reasonable one and grew a paragraph at a time.
12.25 **The document is written in its declared language** — measure the ratio of
      letters from the wrong alphabet outside code spans, YAML blocks, anchors and ID
      tokens against `docs.files.<key>.language` or `docs.language`. Past 15% it is an
      ERROR for a document whose `audience` is `client`, a WARNING otherwise, and **not
      measured at all for a `generated` document**. The severity split is the whole point:
      the rule exists so the client can read the documents written for them. An internal
      journal drifting into English costs nothing; a client document doing it costs the
      review. A generated document is exempt because its body is identifiers — software
      ids, entity names, workflow names — which the language rule forbids translating, so
      measuring it would demand the one thing the standard prohibits.
      Terminology is excluded by the measurement, not by an exception list: it sits in
      code spans, YAML blocks and ID tokens, all of which are stripped before counting.
      Anything a renderer emits that IS an identifier must be backticked for the same
      reason — an unquoted workflow name put a generated index at 45% foreign when every
      Russian word in it was Russian.
      A live project ran `docs.language: ru` with one client document 100% English and
      another at 21% Cyrillic — Russian headings over an English body copied out of the
      spec. Both read as finished documents and neither was one.
12.27 **No hand-written index** — an authored document contains no index, summary or
      coverage table of the entities below it. It is a second copy that drifts the
      first time somebody edits one and not the other: a live `USER-CASES.md` printed
      all 63 of its cases twice, once as index rows and once as headings, with zero
      divergence — 15% of the file existing only to be kept in sync by hand. Indexes
      live in `generated/INDEX.md`.

### Content and truth

12.7 **Inbox hygiene** — ASCII-only filenames; every inbox file has an entry in
     `inbox/README.md`; no content-modifying commit has touched an inbox path after
     its add commit.
12.8 **No rotting pointers** — no `path.ext:NNN` line-number citation anywhere under
     `macstack/`; no link resolving outside the repo root.
12.9 **No secrets anywhere under `macstack/`** — extends rule 10 past
     `resources.accesses`.
12.10 **No parallel spec** — a delta older than 30 days with neither an applied
      banner nor a superseded note.
12.11 **Every acceptance bullet is verified** — each acceptance bullet in
      `USER-CASES.md` is covered by at least one test in `TEST-CASES.md`, matched by
      the bullet's id. An uncovered bullet is an unverified promise; that is the whole
      point of the document.
12.12 **Test cases are well formed** — every test declares `covers` and `kind`; a
      `manual` test also declares preconditions and steps; an `auto` test names the
      test title that proves it (a bare filename is not evidence, and a `file.ts:NNN`
      pointer is already banned by 12.8); a struck test states why.
12.13 **The journal is typed** — every `log.md` entry declares a `kind` and carries
      that kind's required fields and sections per the contract. There is one shape,
      keyed by kind: v1 declared a flat six-field requirement AND a per-kind table that
      disagreed with it, so a `work` entry was contractually required to carry a
      `delta`.
12.14 **Every task is tracked in both places** — every task in `TASKS.md` declares a
      `tracker` id. The file is the source of truth for what the work IS; the team's
      tracker is where the conversation about it happens, and a task in only one of
      them is a task half the team cannot see. Also: `status` declared and one of the
      five; a struck task states why.
12.15 **A release is paired** — every `release` entry in `log.md` has a `CHANGELOG.md`
      entry with the same id, and every `CHANGELOG.md` entry has its `release` entry in
      the log. `CHANGELOG.md` is ordered newest first.
12.16 **Milestones are falsifiable** — every milestone declares a non-empty
      `done_when`, and a milestone marked `done` has every check recorded as met. A
      milestone whose tasks are all `done` but whose checks are not recorded is not
      done — it is unverified.
12.26 **A finished task left a trace** — every task at `done ✓` is named by a `work`
      entry in `log.md`. Without this the closing half of the loop is unenforced: a
      task can be marked done, the documents never re-checked, and every staleness
      rule below stays quiet because nothing recorded that anything happened.
12.17 **Documents have a shelf life** — every document with a `docs.files` entry
      carries `reviewed`, the date it was last checked AGAINST THE CODE. Past
      `freshness_days` (default 30) it is a WARNING; past twice that, an ERROR. A
      `reviews/<date>-*-conformance.md` dated later than `reviewed` counts as the check
      and moves the date forward. This is the one rule aimed at the failure the whole
      folder exists to prevent: a document that reads perfectly and describes a system
      that no longer exists. Everything else here checks shape; this checks that truth
      has been looked at recently.
12.18 **A generated document equals its source** — for every document whose contract
      carries `generated`, re-render and compare. A difference is an ERROR and is
      exactly one of two things: somebody edited the rendered file by hand, or the
      source moved and nobody re-rendered. Both are the same defect from the reader's
      side — the document lies — so both are reported the same way, naming which. The
      remedy is a re-render, never a hand fix.
      This now includes `README.md` and `generated/INDEX.md`. v1 declared `README.md`
      generated and shipped no generator for it, which made this rule unsatisfiable for
      that document across three releases.
12.19 **The journal is not empty** — a document whose contract declares a `journal`
      section has at least one row in it, and no row is dated later than the document's
      `updated`.
12.20 **Every handoff is recorded** — each file in `handoffs/` has a `handoff` entry in
      `log.md` naming it, and each `handoff` entry names a file that exists. The mirror
      of 12.7 for the outbound direction: when the client's edits come back, the only
      way to know WHICH version they reviewed is that entry. An artifact handoff also
      records its URL and version label.
12.22 **The spec agrees with the client's documents** — `sync` reports no disagreement
      between `client/AUTOMATION.md` and the business half of `macstack.json`: same
      roles, same human tasks, same gates, same triggers. A spec that disagrees with the
      document the client signed off on is the failure the whole folder exists to
      prevent. Additions and removals are ERRORS here even though `sync` will not apply
      them: they mean a human still owes an id.
12.23 **Every screen is declared** — every `interfaces[]` entry a person opens (`web`,
      `admin_ui`, `dashboard`, `approval_center`, `form`) has an entity in
      `client/UX-UI.md`, and every screen's `path` belongs to a declared interface. The
      `forbidden` section is non-empty wherever the project declares a prohibition
      touching that role — an empty one there is a promise nobody checked.

## Warnings (non-blocking)

- A goal with no result ("a goal with no path to it"); a result with no goal when
  goals are non-empty.
- A trigger referenced by no workflow and no agent.
- `TEST-CASES.md` derived from an older version of a source document than the current
  one (name both versions) — the coverage count is stale by definition.
- A `Z-` prohibition whose tests assert the refusal but not that the refusal explains
  itself.
- An `X-` cross-cutting case whose tests name no roles to run as.
- A case with no `experience` section (outside the `Z-` space) — the UX bar for that
  case was never stated, so `UX-UI.md` has nothing to answer.
- A screen in `UX-UI.md` that no case names in its `screens` key.
- Software without an agentic passport; a required key missing from `.env`.
- **Coverage gap**: a non-empty tooling-backed section — software, entities, workflows,
  triggers, interfaces, connections — that no plugin `covers`. Say which. Do NOT
  gap-check goals, results, processes, roles or integrations: those are authored by the
  architect, not taught by a plugin, and demanding a plugin for them only produces fake
  entries.
- **Plugin without `covers`** (including the legacy bare-slug form): an agent cannot
  route to it, so it will be either ignored or loaded blindly.
- **Ambiguous coverage**: an area claimed by 2+ plugins where none narrows it with
  `scope`.
- **Unprocessed source**: a file in `inbox/` with no `merge` entry naming it.
- `lifecycle.updated` older than the newest `log.md` entry (name the date).
- **The project has gone quiet**: a task sitting in `doing` while `log.md` has had no
  `work` entry for 14 days. The older staleness check compares `lifecycle.updated`
  against the newest log entry, and with no client input both freeze in agreement — a
  project can run for months with a perfectly green lint and no record of the work.
  This is the rule that notices.
- An §A open item past its age budget (warn 14 days, error 45), or with no `asked_on`
  date — a question nobody has actually put to the client is not blocked, it is
  forgotten.
- An §A item that one or more tasks name in `blocked_by` — say how many. That count is
  the argument for chasing the client today rather than next month.
- A task with no `spec` pointer, or whose `acceptance` names no test. Without `spec`,
  `update` cannot tell which documents a finished task touched.
- A `BL-<n>` promoted to a task without the original being struck with a pointer.
- Legacy free-text entries in `lifecycle.next_steps`.
- A `roles[]` entry with no `cases`; a `sees`/`can` longer than one sentence.
- A `-conformance.md` review with no `-business.md` twin of the same date and slug.
- A delta aged 14–30 days with no applied banner.
- `docs.language` absent while the documents are visibly not English.
- An `inbox/` file heavier than 5 MB.

## Judgment checks (documents)

| Check | What it flags |
|---|---|
| Duplicate content | The same fact stated in both `OVERVIEW.md` and `USER-CASES.md` |
| Superseded documents | A document contradicted by a newer source with no note pointing to it |
| Cross-role contradictions | Two role sections disagreeing on the same behaviour |
| Coverage gaps | An entity or workflow in the spec that no case touches |
| Prose that wants a section | A YAML value carrying a sentence where a section exists for it |

## Output

`ERRORS` as a list (the file is not scaffold-ready) → `WARNINGS` → one
`OK: schema + N integrity rules` line. With a prototype set — resolve and merge first,
lint the merged document.

When rule group 12 is active, append a documents block:

```
Documents: 🟢 OK | 🟡 N warnings | 🔴 N errors
1. <next step>
2. <next step>
```

🔴 on any 12.x error, 🟡 on a documents warning with zero errors, 🟢 otherwise.
Number the next steps in the same order as ERRORS/WARNINGS above (fix errors first).

## Status mode — the same findings, read-only

`/macstack-dev:check` with no argument runs everything above and then renders one
screen. **It writes nothing.** Status is not a second engine with its own predicates:
v1 had `status` re-implement seven checks that rule group 12 already made, in a second
place that could disagree with the first. There is one engine now, and two ways of
printing it.

```
<project> · <stage> · spec v<version>

Spec        🟢 schema + 11 rules
Documents   🟡 3 warnings          (12.17 ×2 · 12.11 ×1)
Milestone   M11 · doing ▶ · 6/9 tasks · 3 of 5 done_when recorded
Client      2 open §A · oldest 21 days · 1 blocking M11-T9
Quiet for   4 days since the last `work` entry

Next
1. Chase A5 — M11-T9 is blocked on it and it was asked 21 days ago
2. UX-UI.md was last checked against the code 41 days ago — /macstack-dev:check --code
3. 4 acceptance bullets have no test — /macstack-dev:update
```

Order the attention list by cost of ignoring it, not by rule number. A blocked task
with a client dependency outranks a stale `reviewed` date, which outranks a formatting
warning.

`--docs` limits the run to pass 3 and the judgment checks. `--code` hands over to
`conformance`, which is the only mode that reads the source tree.
