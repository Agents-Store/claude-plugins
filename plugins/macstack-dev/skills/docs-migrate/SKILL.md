---
name: docs-migrate
description: This skill should be used when the user asks to "migrate docs to macstack", "move the project documents", "перенести docs в macstack", "standardize an existing project's documents", "we already have a docs folder", "move macstack.json into the folder", or wants an organically-grown `docs/` folder (with `macstack.json` still at the repo root) relocated into the standard `macstack/` layout. Disabled for model-invocation: this is a one-time, destructive, multi-gate procedure that must only run when a human explicitly asks for it, never inferred from context.
disable-model-invocation: true
---

# Migrate an existing `docs/` into `macstack/`

A one-time, destructive relocation: a project whose documents grew organically in
`docs/`, with `macstack.json` at the repo root, gets its specification-side material
moved into the standard `macstack/` folder — safely, reversibly, and never silently.
The target layout, ID spaces, anchors and section contract are owned by
`project-docs` — read `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json`
before writing anything; do not recall anchors or ID patterns from memory.

`disable-model-invocation: true` because this moves files with `git mv`, rewrites
references across the repo, and can break links from outside it — the same reason
`skills/feedback/SKILL.md` carries the flag. It must only fire on an explicit ask.

## The classification — what moves and what stays

`docs/` stays the **engineering** folder. Only specification-side material moves.
The principle: `macstack/` must stay a folder you can hand to a client whole;
anything that only helps someone write code belongs in `docs/`. When a document
straddles the line, ASK — do not guess.

| Genre in the wild | Destination | How to recognize it |
|---|---|---|
| Acceptance cases per role, "what the user must get" | `macstack/USER-CASES.md` | role sections, per-case acceptance lists, priorities |
| Open items / debt register split by owner | `macstack/OPEN-QUESTIONS.md` | "what is still owed and by whom", client inputs vs. deferred work |
| Dated rulings with reasoning | `macstack/decisions/` | numbered decisions, "because", cost-if-wrong |
| Analysis of a client document against the live spec | `macstack/deltas/` | "contradictions / what to add", declares itself a proposal |
| Conformance audits, case→code→test | `macstack/reviews/` | status vocabulary, mechanical counts |
| Client-supplied source material (PDF, docx, exports) | `macstack/inbox/` | not authored by the team |
| Product logic in plain words | `macstack/BUSINESS-LOGIC.md` | invariants, state machines, what the platform refuses |
| Architecture, API conventions, code style, data contracts, runbooks, deployment, cloud setup | **stays in `docs/`** | tells an engineer how to build, not what to build |
| Execution plans and design specs per milestone | **stays in `docs/`** | dated working artifacts of how the work got done |

## Procedure

**0. Preconditions — refuse unless all hold.** A git repo with a CLEAN working
tree (a destructive move with uncommitted work has no undo); not on the default
branch — create and switch to a migration branch first; no existing `macstack/`
with content, or an explicit go-ahead to merge into it.

**1. Inventory.** List every file under `docs/` with size, first-added / last-modified
dates and commit count (the best single signal of a LIVING document). Read enough
of each — headings plus the opening paragraph — to classify it. Find client
material anywhere in the tree: PDFs, `.docx`, `.xlsx`, exports, anything not
authored by the team.

**2. Move map — present before touching anything.** A table of source → destination
→ genre → why, plus an explicit STAYS list, plus an UNSURE list with a question for
each. **── GATE 1 ──** the user confirms, corrects, or reclassifies.

**3. Inbound references.** Grep the whole repository for every path about to move.
Report references inside this repo (will be rewritten) separately from references
from OUTSIDE this repo, which CANNOT be rewritten — list them for the user. This is
real: a sibling knowledge base can cite `projects/<name>/docs/open-items.md` or
`projects/<name>/macstack.json` by path from a different repository, including from
a `sources:` frontmatter field. **── GATE 2 ──** the user accepts the external
breakage, or the move is narrowed.

**4. Move.** `git mv` only — never `cp`+`rm`, so history follows the file. Rewrite
in-repo references with the Edit tool, one file at a time — never `sed` across the
tree, a blind substitution hits code, changelogs and quoted examples. For
`macstack.json`: `git mv` to `macstack/macstack.json`. Do NOT leave a redirect stub
at the old path — a three-line pointer fails the schema's required keys, and
relaxing `required` is not an additive change. Offer `git rm` of the root file only
after the moved copy parses and lints.

**5. Normalize.** Invoke `project-docs` to create whatever the layout is still
missing. Insert the section anchors from `doc-contracts.json` into the moved
documents idempotently, mapping each existing heading to its anchor key; where a
document has no equivalent of a required section, add the anchor with an empty
placeholder rather than inventing content. Rename dated artifacts to
`YYYY-MM-DD-<slug>.md`; ASCII-only filenames in `inbox/` (the zone is immutable —
fix a bad name now, never after). Build `inbox/README.md` from what is known about
each source, leaving "from whom" and "supersedes" blank rather than guessed. Seed
`log.md` with one backfill entry per moved client source, marked as backfilled.

**6. Reconcile IDs — a named gate, not a heuristic.** Local numbering in existing
rulings files ("1." … "26.") is not the project's D-space, and the two cannot be
reconciled mechanically. Present the mapping you propose and let the owner correct
it. **── GATE 3 ──** the owner confirms the D-ID assignment. Then convert
`lifecycle.open_questions` and `lifecycle.needs_from_client` from prose strings to
pointer form `{id, ref, status, blocks, closed_by}`, keeping the prose in
`OPEN-QUESTIONS.md` — the JSON must end up holding no prose. Back-fill `roles[].cases`.

**7. Verify.** Run `lint`; every rule in group 12 must pass or be explained. Confirm
no file lost content — compare line counts before and after. Report: what moved,
what stayed, what was renamed, which references were rewritten, which external
references are now broken and who must fix them, and which IDs still need a human
decision.

## Guard rails

- Nothing is moved before the move map (Gate 1) is confirmed.
- `git mv` only, one migration branch, a clean tree — no exceptions.
- `inbox/` becomes immutable the moment material lands in it: fix bad filenames
  during the move, never after.
- Three named gates (map, external references, D-ID reconciliation) — never
  collapse them into one confirmation.
