---
name: project-docs
description: This skill should be used when the user asks to "create the macstack folder", "set up project docs", "where do user cases live", "add USER-CASES.md", "standardize the project documents", "repair the macstack folder", mentions `macstack/`, OPEN-QUESTIONS, DECISIONS, the client inbox or the document log — and BEFORE any other skill reads or writes anything under `macstack/`. Defines the folder standard: layout, path resolution, ID spaces, section anchors, the language rule and the immutability guardrails.
---

# The `macstack/` folder — standard

`macstack.json` holds the machine-readable facts. Everything a human needs and JSON
cannot hold — the product logic in plain words, cases per role, why a decision was
taken and what it costs if wrong, what is still owed by the client — lives beside it
as markdown in the same folder.

Structure is defined once in `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json`,
which both this skill (the writer) and `lint` (the checker) read. Never restate that
file's anchors or ID patterns from memory — open it.

## Layout

```
macstack/
├── macstack.json          the spec — machine-readable facts (canonical location; a legacy root file stays put until `docs-migrate` moves it)
├── README.md              this folder's contract: map, ownership, ID spaces   [generated]
├── USER-CASES.md          [client] cases per role, versioned            ← the bar
├── TEST-CASES.md          how each acceptance bullet is verified, auto | manual
├── ROLES.md               who does what and what starts it              [generated]
├── ARCHITECTURE.md        how the project is built, for the agent       [generated]
├── TASKS.md               milestones and tasks — what will be done, in what order
├── BUSINESS-LOGIC.md      [client] invariants and logic in plain words
├── OPEN-QUESTIONS.md      §A owed by the client · §B deferred by us
├── DECISIONS.md           D<n> registry and allocator → files in decisions/
├── log.md                 append-only journal: intake · handoff · merge · work · release
├── inbox/                 IMMUTABLE client material · README.md = manifest
├── handoffs/              IMMUTABLE packages sent to the client, exactly as sent
├── deltas/                YYYY-MM-DD-<slug>.md — proposals, not edits
├── decisions/             YYYY-MM-DD-<slug>-rulings.md — with cost-if-wrong
└── reviews/               <slug>-conformance.md + its -business.md twin
```

`docs/` stays the **engineering** folder — `architecture.md`, `api-conventions.md`,
`code-style.md`, deployment runbooks do not move here. `macstack/` must stay a folder
you can hand to a client whole.

There is no physical `client/` vs `technical/` split: these documents cross-cite each
other constantly, and two trees would double every relative link. Audience is declared
in `docs.files.<name>.audience` and in the `-business.md` suffix, not in the path.
`docs.files.<key>` uses the document keys from `doc-contracts.json` (`user_cases`,
`test_cases`, `business_logic`, `open_questions`, `decisions`, `log`), not filenames.

## Path resolution

Resolve once, at the start of every operation, in this order:

1. `<repo>/macstack/macstack.json` — canonical.
2. `<repo>/macstack.json` — legacy. Works, but say so and offer `docs-migrate`.
3. Search upward from cwd to the git root.

**Both 1 and 2 present is an ERROR**, never a silent choice — two specs mean two
truths. Report both paths and stop: the remedy is `docs-migrate`, which relocates
the legacy root file into the folder (or `git rm`s it once the moved copy is
verified).

## Nine invariants

1. **`inbox/` is immutable.** Never edit, rename or delete anything in it. A source
   already committed in this repo at a stable path is **not copied** into `inbox/` —
   cite it by path. A copy diverges from its original with the first edit, and an
   immutable zone cannot be fixed afterwards. The one writable file is
   `inbox/README.md`, the manifest.
2. **ASCII only** in `inbox/` filenames and inside every ID token. Refuse at the
   moment of adding: the zone is immutable, so a bad name can never be corrected.
   Watch the homoglyphs: U+041A CYRILLIC CAPITAL KA renders identically to ASCII `K`,
   so an id typed with it greps as absent and silently breaks every cross-reference
   check. Same trap with А О С Е Р Т Х. Verify the codepoint, not the glyph.
3. **Anchors, not headings.** Each section is marked by an HTML comment
   (`<!-- macstack:section=contradictions -->`) on the line above its heading.
   Headings and prose are written in `docs.language`; **anchors are never
   translated** — the linter greps the anchor, which is what makes the folder
   language-independent. Re-insert missing anchors idempotently; a stripped anchor
   is never a reason to rewrite the document.
4. **Closed items are struck, not deleted:** `~~A6~~ · CLOSED D14, 2026-08-24`.
   Numbers are never reused.
5. **No line-number pointers.** Never `src/foo.ts:214` — cite a symbol name or a test
   title. Line numbers rot the moment the file above them grows, and a pointer at a
   closing brace is worse than none because it reads as authoritative.
6. **A delta is not a spec.** It names its bar (`USER-CASES.md`) and stays the history
   of an analysis.
7. **A generated document is never edited by hand.** `README.md`, `ROLES.md` and
   `ARCHITECTURE.md` carry a `generated` banner naming their source and are rebuilt by
   `render-docs`. A hand edit is lost on the next render, and lint reports the difference
   (12.18) rather than quietly overwriting it. What a human needs to add about a generated
   subject belongs where the source points back: architecture arguments and measured traps
   in `docs/architecture.md`, what a role MEANS to a person in `USER-CASES.md`.
8. **Every living document carries a journal.** One row per change, `date | what changed`
   (`user_cases` and `test_cases` add `version` and `source`). Write-once documents —
   rulings, reviews, deltas, the inbox manifest — carry none: their date is in the filename,
   and editing one of them is itself the defect.
9. **`reviewed` is not `updated`.** `updated` is when the text last changed; `reviewed` is
   when the document was last checked AGAINST THE CODE. Only the second one expires
   (`freshness_days`, default 30), because only the second one is a claim about the world. A
   document can be edited daily and be wrong the whole time.

## Who owns what

`macstack.json` owns the ID-space binding and machine-readable state. The markdown owns
the text and allocates the IDs. A copy is permitted only where a machine can prove it
is still a copy.

| Concern | Owner | The other side holds |
|---|---|---|
| `roles[].id/name/acl/isolation` | `macstack.json` | `USER-CASES.md` role sections, joined via `roles[].cases` |
| What a person gets, per case | `USER-CASES.md` | `TEST-CASES.md` verifies each of its acceptance bullets |
| How a bullet is checked | `TEST-CASES.md` | ids carry the case they verify (`C-06.T3`); a dated `reviews/` file records what a run found |
| What will be done, in what order | `TASKS.md` | `lifecycle.next_steps[]` and `lifecycle.milestones[]` as pointers; every task also lives in the team's tracker |
| What happened | `log.md` | typed entries — `work` is the development log, the half git cannot hold |
| What reached the client | `CHANGELOG.md` | curated from the log's `work` and `release` entries; never a commit history in disguise |
| Open questions | `OPEN-QUESTIONS.md` | `lifecycle.open_questions[]` as `{id, ref, status, blocks, closed_by}` pointers |
| Owed by the client | `OPEN-QUESTIONS.md §A` | `lifecycle.needs_from_client[]` — a **derived view**: live §A client rows only |
| Decisions | `decisions/*.md` | `lifecycle.decisions[]` pointers; prose cites `D<n>` |
| Prose, rationale, cost-if-wrong | markdown | JSON never |

Pointer form carries no prose, so there is nothing to drift. Where a human genuinely
needs text in the JSON, an optional `summary` (≤200 chars) **must equal the first
sentence** of its markdown item — mismatch is an ERROR, not a warning.

During migration, `lifecycle.open_questions[]` may legally hold a mix of legacy prose
strings and pointer objects in the same array — the lint warning for a legacy string
fires per item, never against the array as a whole.

## Language

Read `docs.language` (ISO 639-1) from the spec; absent means English. Per-document
override lives in `docs.files.<name>.language`. Write headings, prose and tables in
that language. Never translate: anchors, ID tokens, frontmatter keys, `docs.*` field
names. For a document with `audience: client`, confirm the output language before
writing.

## Creating or repairing the folder

1. Resolve the spec; read `docs.root` (default `macstack`), `docs.language`, `docs.files`.
   If the spec resolved to the legacy root path (`<repo>/macstack.json`), create the
   folder around it as-is and report that relocating it is `docs-migrate`'s job — do
   not move it here.
2. Create only what is missing — **never overwrite an existing document.** For a file
   that exists but lacks anchors or sections, add what is missing in place and report
   it; do not regenerate.
   Materialize eagerly: the nine documents, plus `inbox/` with its `README.md` manifest.
   Create `deltas/`, `decisions/` and `reviews/` **lazily, on first use** — git does
   not track an empty directory, so creating them up front either leaves untracked
   empties that vanish on clone or scatters four `.gitkeep` files. Their absence in a
   fresh folder is correct, not a gap; lint must not report it.
3. Seed each document from `doc-contracts.json`: the required anchors, the section
   headings translated into `docs.language`, and a one-line placeholder saying what
   belongs there. Seed `USER-CASES.md` role sections from `roles[]`, and back-fill
   `roles[].cases` with the matching ID prefix. If the spec's `lifecycle.open_questions`
   or `needs_from_client` still holds prose strings, offer `docs-migrate`'s conversion
   step (prose → `OPEN-QUESTIONS.md` rows with pointer objects) rather than leaving
   them as unconvertible legacy text.
3b. **Render the generated documents** — `README.md`, `ROLES.md`, `ARCHITECTURE.md` — with
   `render-docs`, never by hand, and never partially. A folder created without them is
   incomplete, not minimal: `ROLES.md` is the only place the join between a role, its tasks
   and the trigger that moves them can be read at all.
4. Write `README.md` from the contract: the map above, the ownership table, the ID
   spaces, and the merge loop in four lines. Scaffolding does not write to `log.md` —
   that journal records incoming material and merges only, so a freshly created
   folder has no log entry, and that absence is correct, not forgotten.
5. `.gitignore` — leave `inbox/` committed (an immutable zone must be durable). Respect
   the existing `*.local.md` convention for sensitive companions.
6. Add the `docs` section to `macstack.json` if absent, then run `lint`.

Prototypes may seed `macstack/README.md` and nothing else — a parent's cases and open
questions are not this project's.

## Routing

| Task | Skill |
|---|---|
| Client edits arrived, or "improve X" | `docs-merge` |
| Turn the acceptance bullets into checks | `test-cases` |
| Plan work, or reconcile with the tracker | `tasks` |
| Record what was built, or cut a release | `changelog` |
| "Where are we and what next" | `status` |
| Rebuild the generated documents | `render-docs` |
| Hand the client something to edit | `client-package` |
| Move an existing `docs/` into this layout | `docs-migrate` |
| Validate the folder and the spec | `lint` |
| The spec itself | `init-project` · `generate-stack` |
