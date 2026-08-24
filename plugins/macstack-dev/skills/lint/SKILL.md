---
name: lint
description: This skill should be used when the user asks to "validate macstack.json", "lint macstack", "check the stack spec", "verify macstack.json integrity", or after any skill of this plugin writes/edits macstack.json. Validates against the bundled JSON Schema and the referential-integrity rules.
---

# Lint macstack.json

Two passes: JSON Schema, then referential integrity. A file that fails lint must not
be scaffolded from.

Resolve the path first: `macstack/macstack.json` (canonical) → `./macstack.json`
(legacy fallback). Both present is a setup error (see `setup`) — stop instead of
picking one silently.

**Prefer the reference linter** — it implements both passes and is maintained with
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

Offline fallback: run the same two passes manually with the bundled copies.

## Pass 1 — JSON Schema

Fetch the live schema first (it may be newer than the bundled copy); cache it in
`${CLAUDE_PLUGIN_DATA}`; offline → bundled
`${CLAUDE_PLUGIN_ROOT}/skills/lint/references/macstack.schema.json`.

```bash
python3 - <<'EOF'
import json, jsonschema, urllib.request, os
URL = "https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json"
try:
    schema = json.load(urllib.request.urlopen(URL, timeout=15))
except Exception:
    schema = json.load(open("<PLUGIN_ROOT>/skills/lint/references/macstack.schema.json"))
path = "macstack/macstack.json" if os.path.exists("macstack/macstack.json") else "macstack.json"
jsonschema.validate(json.load(open(path)), schema)
print("schema: VALID")
EOF
```

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
    software / entities / workflows / triggers / interfaces / connections.mcp
    (the id-spaces of the six sections the gap check looks at).

## Pass 3 — The `macstack/` folder (rule group 12)

Active only when macstack.json has a `docs` section, or a `macstack/` folder exists
on disk. Errors block scaffolding exactly like Pass 2; lint red on a document that
reads fine usually means stripped anchors (see `troubleshoot`).

12.1 **Layout** — `docs.root` resolves; every document in `doc-contracts.json`'s
     `documents` map whose `path` is a FIXED NAME exists under `docs.root`.
     Documents whose `path` carries a `<placeholder>` (`delta`, `rulings`, `review`)
     are dated instances, not required files — their directories are created lazily
     and their absence in a fresh folder is correct. `docs.files` entries, where
     present, must agree. Exactly one `macstack.json` in the repo.
12.2 **Anchors** — each document carries the anchors its type requires per
     `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json`.
12.3 **ID integrity** — unique per space (case/test-case/task/backlog/milestone/
     release/open-item/decision/contradiction/addition); ASCII-only inside an ID token — the homoglyph rule: a Cyrillic
     capital KA (U+041A) renders exactly like `K` (U+004B), greps as absent and
     silently breaks every cross-reference check, so compare codepoints rather than
     glyphs; no gaps in
     D-numbering; A/B numbers never reused after a strike.
12.4 **Cross-file refs** — every `D<n>` cited in macstack.json, USER-CASES or
     OPEN-QUESTIONS resolves in DECISIONS.md; every `A<n>` in `lifecycle.*` resolves
     to a live §A row; every `roles[].cases` prefix yields ≥1 case heading; every
     case-section letter maps to exactly one role; every `<case>.T<n>` id in
     TEST-CASES.md carries the id of a case that still exists. Every `A<n>` **and
     every `B<n>`** in `lifecycle.*` resolves to a live row — the B half was
     previously unchecked, so a pointer at a struck or nonexistent item passed clean.
     Every `blocked_by` entry in TASKS.md resolves to a live task id or open-item id.
12.5 **Checked copies** — `open_questions[].summary` equals the first sentence of
     its markdown item; for versioned documents (`user_cases`, `test_cases`),
     `docs.files.<x>.version` equals the document header version equals the last
     journal row. Parse the journal by the contract's `journal_columns` for that
     document — the shape is declared there, not guessed.
12.6 **`needs_from_client` is a view** — contains no closed items, omits no open
     client-input §A row.
12.7 **Inbox hygiene** — ASCII-only filenames; every inbox file has a manifest row
     in `inbox/README.md`; no content-modifying commit has touched an inbox path
     after its add commit.
12.8 **No rotting pointers** — no `path.ext:NNN` line-number citation anywhere
     under `macstack/`; no link resolving outside the repo root.
12.9 **No secrets anywhere under `macstack/`** — extends rule 10 past
     `resources.accesses`.
12.10 **No parallel spec** — a delta older than 30 days with neither an applied
      banner nor a superseded note.
12.11 **Every acceptance bullet is verified** — each "Готово, если" bullet in
      USER-CASES.md is covered by at least one test in TEST-CASES.md. An uncovered
      bullet is an unverified promise; that is the whole point of the document.
12.12 **Test cases are well formed** — every test declares `covers` and `expected`;
      a `manual` test also declares preconditions and steps; an `auto` test also
      names the test title that proves it (a bare filename is not evidence, and a
      `file.ts:NNN` pointer is already banned by 12.8); a struck test states why.
12.13 **The journal is typed** — every `log.md` entry declares one of
      `intake | merge | work | release` and carries that kind's required fields per
      the contract's `entry_kinds`. Before the kinds existed, `log.md` had no
      `sections` at all, so 12.2 could not fire on it and its declared shape was
      enforced by nothing.
12.14 **Every task is tracked in both places** — every task in TASKS.md declares a
      `tracker` id. The file is the source of truth for what the work IS; the team's
      tracker is where the conversation about it happens, and a task in only one of
      them is a task half the team cannot see. Also: `status` declared and one of the
      five; a struck task states why.
12.15 **A release is paired** — every `release` entry in `log.md` has a
      `CHANGELOG.md` entry with the same id, and every `CHANGELOG.md` entry has its
      `release` entry in the log. CHANGELOG.md is ordered newest first.
12.16 **Milestones are falsifiable** — every milestone in TASKS.md declares a
      non-empty `done_when`, and a milestone marked `done` has every check recorded
      as met. A milestone whose tasks are all `done` but whose checks are not
      recorded is not done — it is unverified.

12.17 **Documents have a shelf life** — every document with a `docs.files` entry carries
      `reviewed`, the date it was last checked AGAINST THE CODE. Past `freshness_days`
      (default 30) it is a WARNING; past twice that, an ERROR. A
      `reviews/<date>-*-conformance.md` dated later than `reviewed` counts as the check
      and moves the date forward. This is the one rule aimed at the failure the whole
      folder exists to prevent: a document that reads perfectly and describes a system
      that no longer exists. Everything else here checks shape; this checks truth has
      been looked at recently. `reviewed` is NOT `updated` — you can rewrite a sentence
      today without ever asking whether the platform still behaves that way.
12.18 **A generated document equals its source** — for every document whose contract
      carries `generated`, re-render it and compare. A difference is an ERROR, and it is
      exactly one of two things: somebody edited the rendered file by hand, or the source
      moved and nobody re-rendered. Both are the same defect from the reader's side — the
      document lies — so both are reported the same way, naming which. The remedy is
      `render`, never a hand fix.
12.19 **The journal is not empty** — a document whose contract declares a `journal`
      section has at least one row in it, and no row is dated later than the document's
      `updated`. An empty journal on a living document means either it has never changed
      since creation (say so in a row) or its changes went unrecorded, which is the thing
      the journal exists to prevent.
12.20 **Every handoff is recorded** — each file in `handoffs/` has a `handoff` entry in
      `log.md` naming it, and each `handoff` entry names a file that exists. The mirror of
      12.7 for the outbound direction: when the client's edits come back, the only way to
      know WHICH version they reviewed is that entry.
## Warnings (non-blocking)

- A goal with no result ("a goal with no path to it"); a result with no goal when
  goals are non-empty.
- A trigger referenced by no workflow and no agent.
- TEST-CASES.md derived from an older `USER-CASES.md` version than the current one
  (name both versions) — the coverage table is stale by definition.
- A `Z-` prohibition whose tests assert the refusal but not that the refusal
  explains itself.
- An `X-` cross-cutting case whose tests name no roles to run as.
- Software without an agentic passport; a required key missing from `.env` (when the
  file exists).
- **Coverage gap**: a non-empty *tooling-backed* section — software, entities,
  workflows, triggers, interfaces, connections — that no plugin `covers`. Say which:
  "14 workflows and no plugin covering `workflows`". Do NOT gap-check goals, results,
  processes, roles or integrations: those are authored by the architect, not taught by
  a plugin, and demanding a plugin for them only produces fake entries.
- **Plugin without `covers`** (including the legacy bare-slug form): an agent cannot
  route to it, so it will be either ignored or loaded blindly.
- **Ambiguous coverage**: an area claimed by 2+ plugins where none narrows it with
  `scope`. Resolution rule is most-specific-wins — a plugin whose `scope` holds the
  element beats an unscoped one — so an unscoped overlap has no winner.
- **Unprocessed source**: a file in `inbox/` with no `merge` entry in `log.md`
  naming it.
- `lifecycle.updated` older than the newest `log.md` entry (name the date).
- **The project has gone quiet**: a task sitting in `doing` while `log.md` has had no
  `work` entry for 14 days. The older staleness check compares `lifecycle.updated`
  against the newest log entry, and with no client input both freeze in agreement —
  a project can run for months with a perfectly green lint and no record of the work.
  This is the rule that notices.
- An §A open item past its age budget (warn 14 days, error 45 per the contract), or
  with no **asked on** date — a question nobody has actually put to the client is not
  blocked, it is forgotten.
- An §A item that one or more tasks name in `blocked_by` — say how many. That count
  is the argument for chasing the client today rather than next month.
- A task with no `spec` pointer, or whose `acceptance` names no test.
- A `BL-<n>` backlog item promoted to a task without the original being struck with a
  pointer to its new id.
- Legacy free-text entries in `lifecycle.next_steps` (offer the conversion to task
  pointers).
- A `roles[]` entry with no `cases`; a `sees`/`can` longer than one sentence.
- A case heading with no acceptance list; a §B item stating no trigger; a ruling
  with no cost-if-wrong anchor.
- A `-conformance.md` review with no `-business.md` twin of the same date and slug
  (WARNING, not error — nothing generates the twin yet).
- A delta aged 14–30 days with no applied banner.
- `docs.language` absent while the documents are visibly not English.
- Legacy string-form `open_questions`.
- An `inbox/` file heavier than 5 MB.

## Judgment checks (documents)

| Check | What it flags |
|---|---|
| Duplicate content | The same fact stated in both BUSINESS-LOGIC.md and USER-CASES.md |
| Superseded documents | A document contradicted by a newer source with no note pointing to it |
| Cross-role contradictions | Two role sections in USER-CASES.md disagree on the same behavior |
| Coverage gaps | An entity or workflow in macstack.json that no case touches |

## Output format

`ERRORS` as a list (the file is not scaffold-ready) → `WARNINGS` → one `OK: schema +
N integrity rules` line. With a prototype set — resolve and merge first, lint the
merged document.

When rule group 12 is active, append a documents block:

```
Documents: 🟢 OK | 🟡 N warnings | 🔴 N errors
1. <next step>
2. <next step>
```

🔴 on any 12.x error, 🟡 on a documents warning with zero errors, 🟢 otherwise.
Number the next steps in the same order as ERRORS/WARNINGS above (fix errors
first).
