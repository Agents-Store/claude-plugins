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
├── macstack.json          the spec — machine-readable facts
├── README.md              this folder's contract: map, ownership, ID spaces   [generated]
├── USER-CASES.md          [client] cases per role, versioned            ← the bar
├── BUSINESS-LOGIC.md      [client] invariants and logic in plain words
├── OPEN-QUESTIONS.md      §A owed by the client · §B deferred by us
├── DECISIONS.md           D-ID registry and allocator → files in decisions/
├── log.md                 append-only journal of intakes and merges
├── inbox/                 IMMUTABLE client material · README.md = manifest
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

## Path resolution

Resolve once, at the start of every operation, in this order:

1. `<repo>/macstack/macstack.json` — canonical.
2. `<repo>/macstack.json` — legacy. Works, but say so and offer `docs-migrate`.
3. Search upward from cwd to the git root.

**Both 1 and 2 present is an ERROR**, never a silent choice — two specs mean two
truths. Report both paths and stop.

## Six invariants

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

## Who owns what

`macstack.json` owns the ID-space binding and machine-readable state. The markdown owns
the text and allocates the IDs. A copy is permitted only where a machine can prove it
is still a copy.

| Concern | Owner | The other side holds |
|---|---|---|
| `roles[].id/name/acl/isolation` | `macstack.json` | `USER-CASES.md` role sections, joined via `roles[].cases` |
| What a person gets, per case | `USER-CASES.md` | — |
| Open questions | `OPEN-QUESTIONS.md` | `lifecycle.open_questions[]` as `{id, ref, status, blocks, closed_by}` pointers |
| Owed by the client | `OPEN-QUESTIONS.md §A` | `lifecycle.needs_from_client[]` — a **derived view**: live §A client rows only |
| Decisions | `decisions/*.md` | `lifecycle.decisions[]` pointers; prose cites `D-NN` |
| Prose, rationale, cost-if-wrong | markdown | JSON never |

Pointer form carries no prose, so there is nothing to drift. Where a human genuinely
needs text in the JSON, an optional `summary` (≤200 chars) **must equal the first
sentence** of its markdown item — mismatch is an ERROR, not a warning.

## Language

Read `docs.language` (ISO 639-1) from the spec; absent means English. Per-document
override lives in `docs.files.<name>.language`. Write headings, prose and tables in
that language. Never translate: anchors, ID tokens, frontmatter keys, `docs.*` field
names. For a document with `audience: client`, confirm the output language before
writing.

## Creating or repairing the folder

1. Resolve the spec; read `docs.root` (default `macstack`), `docs.language`, `docs.files`.
2. Create only what is missing — **never overwrite an existing document.** For a file
   that exists but lacks anchors or sections, add what is missing in place and report
   it; do not regenerate.
   Materialize eagerly: the six documents, plus `inbox/` with its `README.md` manifest.
   Create `deltas/`, `decisions/` and `reviews/` **lazily, on first use** — git does
   not track an empty directory, so creating them up front either leaves untracked
   empties that vanish on clone or scatters four `.gitkeep` files. Their absence in a
   fresh folder is correct, not a gap; lint must not report it.
3. Seed each document from `doc-contracts.json`: the required anchors, the section
   headings translated into `docs.language`, and a one-line placeholder saying what
   belongs there. Seed `USER-CASES.md` role sections from `roles[]`, and back-fill
   `roles[].cases` with the matching ID prefix.
4. Write `README.md` from the contract: the map above, the ownership table, the ID
   spaces, and the merge loop in four lines.
5. `.gitignore` — leave `inbox/` committed (an immutable zone must be durable). Respect
   the existing `*.local.md` convention for sensitive companions.
6. Add the `docs` section to `macstack.json` if absent, then run `lint`.

Prototypes may seed `macstack/README.md` and nothing else — a parent's cases and open
questions are not this project's.

## Routing

| Task | Skill |
|---|---|
| Client edits arrived, or "improve X" | `docs-merge` |
| Move an existing `docs/` into this layout | `docs-migrate` |
| Validate the folder and the spec | `lint` |
| The spec itself | `init-project` · `generate-stack` |
