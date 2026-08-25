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

Read the shape from
`${CLAUDE_PLUGIN_ROOT}/skills/documents/references/doc-contracts.json` — every rule
below is checked against that file, never against memory.

### Layout and identity

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
12.2 **Anchors** — each document carries the anchors its contract requires: the
     `doc` header, every declared `section`, and an `entity` anchor above every entity
     heading.
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
     header version equals the last journal row. Three places, and all three must agree.
12.6 **`needs_from_client` is a view** — contains no closed items, omits no open §A
     client item.

### Shape (v2)

12.21 **Entities parse** — every entity declared in the contract is found by its
      anchor, carries exactly one fenced `yaml` block immediately after its heading,
      and that block declares every `yaml_required` key for its kind and no key the
      contract does not declare. Every `sections_required` anchor is present beneath
      it, and the conditional sets (`sections_required_when`,
      `sections_required_except_prefix`) are applied by the entity's own values — a
      `manual` test needs preconditions and steps, an `auto` one needs evidence, a
      `Z-` prohibition needs neither flow nor experience.
      This rule replaces v1's column-position check. Columns were read by POSITION
      because heading text follows `docs.language`; the anchor and the YAML key give
      the same language independence without pulling prose into a grid.
12.24 **Tables stay inside the budget** — at most 4 columns, at most 80 characters a
      cell, at least 3 rows, and no `<br>`, bold, code fence or pipe inside a cell.
      Journals are exempt. Report the file, the table's anchor or heading, the column
      count and the longest cell verbatim, because "this table is too wide" is not
      actionable and "cell 4 of row 12 is 876 characters" is.
      The budget exists because every oversized table measured in the field started as
      a reasonable one and grew a paragraph at a time.
12.25 **The document is written in its declared language** — measure the ratio of
      letters from the wrong alphabet outside code spans, YAML blocks, anchors and ID
      tokens against `docs.files.<key>.language` or `docs.language`. Past 15% it is an
      ERROR for a document whose `audience` is `client`, and a WARNING otherwise.
      Terminology is expected to be English and is excluded by the measurement, not by
      an exception list. The severity split is the whole point: the rule exists so the
      client can read the documents written for them. An internal journal drifting into
      English costs nothing; a client document doing it costs the review.
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
