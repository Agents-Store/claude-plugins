---
name: intake
description: This skill should be used when the user says "client sent edits", "merge client feedback", "клиент прислал правки", "разобрать правки", "improve the user cases", "new spec from the client", "process the inbox", "what changed in the client's document", "apply the delta", pastes new client material into chat, or drops a file into macstack/inbox/. Runs the full intake → delta → gate → ruling → apply → log loop against the macstack/ folder standard — never edits the client documents or macstack.json directly from raw client material.
---

# Docs Merge — the Client-Feedback Loop

Turns one piece of client material (a file, or plain text) into a versioned, ruled-on
change to `macstack/`. Nothing skips from raw material straight into the spec — every
change passes through a delta, at least one human gate, and a logged ruling.

Open `${CLAUDE_PLUGIN_ROOT}/skills/documents/SKILL.md` for the folder layout and
`${CLAUDE_PLUGIN_ROOT}/skills/documents/references/doc-contracts.json` for anchors,
section keys and ID regexes first — this skill assumes both and does not repeat them.

## Two entry points

A file arrives (client email, upload, path already in this repo) → start at Step 1
Intake. "надо улучшить X" / "improve X" with no file → skip straight to Step 3 Delta,
source = `"chat, YYYY-MM-DD"`.

## 0. Resolve

`macstack/macstack.json` → `./macstack.json` (legacy) → search upward to the git root.
**Both present is an ERROR**, not a silent choice — report both paths and stop: the
remedy is migration mode in `documents`, which relocates the legacy root file into the folder (or
`git rm`s it once the moved copy is verified). Read `docs.language` (documents are
written in it; anchors and IDs never are) and `docs.files`.

## 1. Intake

New material → `inbox/<slug>-YYYY-MM-DD.<ext>`, ASCII filename, never touched again
once it lands — inbox is immutable, the only writable file in it is `inbox/README.md`
(the manifest). Content pasted in chat is saved to inbox/ first so the raw survives.
A source already committed in this repo at a stable path is **cited by path, not
copied** — a copy diverges from its original and an immutable zone can't be fixed
afterward. Add a row to `inbox/README.md`: `| file | received | from whom | channel |
supersedes | processed in |`.

**GATE 1** — "N unprocessed in inbox/. Taking `<one>`. Who sent it, what does it
supersede?" One source at a time, human in the loop.

## 2. Read

- `.pdf` — Read tool with page ranges.
- `.docx` — unzip `word/document.xml` and strip tags (read-only, prints to stdout,
  writes nothing); paragraphs collapse into one stream — rebuild hierarchy from the
  section numbering in the text, not from markup:
  ```
  python3 -c "import zipfile,re,sys; x=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode('utf-8','replace'); print(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x)).strip())" "path/file.docx"
  ```
- `.xlsx` — REFUSED. Ask for a CSV export beside it and write NO log entry, so the
  file stays in the unprocessed set. Say so in the report rather than closing the
  journal.
- Before reading anything: check size / first bytes. A not-yet-materialized iCloud
  file reads as empty and produces a confidently wrong delta — refuse rather than
  guess.

## 3. Delta

Write `deltas/YYYY-MM-DD-<slug>.md` with the anchored sections from doc-contracts.json
(`howto`, `contradictions`, `additions`, `confirmed`, `absent`, `journal`, plus
`applied` for the closing banner):

| Part | Content |
|---|---|
| 1 — Contradictions `K-N` | The document says something a live case doesn't; each carries a blast-radius tag and names the cases it would rewrite. ASCII `K` only (U+004B) — the Cyrillic capital KA (U+041A) renders identically, greps as absent, and silently breaks every cross-reference check. |
| 2 — Additions `N-N` | Grouped by role. |
| 3 — Confirmed | What the document already matches. |
| 4 — Absent | What the document doesn't address at all. |

The file declares itself a proposal, not an edit, and names its bar (`USER-CASES.md`).
It stays as history after applying — never deleted or rewritten.

**3b. Bypass** — Part 1 is empty (pure additions) → skip the delta AND the rulings
file, apply directly, log it. Skip this branch and the ceremony gets abandoned
wholesale by the third small edit.

**GATE 2** — Present K-N ordered by blast radius. The OWNER rules on each. Additions
merge without a ruling unless the owner objects. Nothing in Part 1 merges silently.

## 4. Rulings

Allocate D-ids in `DECISIONS.md` FIRST, in their own commit — writing each row's id,
date, title, decided by and file at allocation time — then write
`decisions/YYYY-MM-DD-<slug>-rulings.md`. Each entry: the ruling, "— because …",
**Cost if wrong** under its anchor (written AT DECISION TIME, before the outcome is
known — a retrospective cost clause is worthless), and who decided (owner | session).
Header stamps date, branch, result (e.g. "USER-CASES.md v1.9"). Tail: what is left to
the client, where this was applied.

## 5. Apply

Order matters: USER-CASES.md → UX-UI.md and AUTOMATION.md → TEST-CASES.md → OVERVIEW.md → macstack.json. The
last three are derived from the first, so writing the spec first means writing changes
you may have to reverse. A changed or added acceptance bullet leaves `TEST-CASES.md`
stale by definition — re-derive it with `macstack-dev:test-cases` in the same pass, or
the coverage table starts lying. USER-CASES gets a version bump in its header AND a matching journal-table
row naming the delta and the rulings file. Re-insert any stripped anchors idempotently
— a missing anchor is never a reason to rewrite the document; headings and prose stay
in `docs.language`, anchors never translate. No line-number pointers into source
(`src/foo.ts:214`) — cite a symbol name or a test title instead. When a role is
removed from `roles[]`, strike its entire USER-CASES.md section heading as well as
its cases — the letter is retired with it and never reassigned.

**GATE 3** — show the USER-CASES diff before writing.
**GATE 4** — show the macstack.json diff separately (a spec change is lint-gated).

## 6. Remainder, then 7. Close

- Unresolved → `OPEN-QUESTIONS.md` §A with fresh A<n> ids, cross-referencing the K-N.
  Resolved → struck with the closing decision id and date: `~~A6~~ · CLOSED D14, 2026-08-24`
  (numbers never reused). New deferred engineering → §B with BOTH the reason it was
  safe to defer AND the trigger that makes it unsafe.
- Close: prepend the applied banner under the `applied` anchor in the delta, naming
  the resulting version, the rulings file, and the A<n> ids opened — the delta is now
  history. DECISIONS.md rows were already written in step 4 — do not re-add them here;
  only fill in a row's `file` link now if it was not yet known at allocation time.

## 8. Log

Append to `log.md` — kind `merge`, one of the four the journal accepts
(`intake · merge · work · release`; `work` and `release` belong to the
`journal` skill, not this one):

```
## [2026-08-24] merge | OHAWO Client Portal Functional Spec
- source: macstack/inbox/ohawo-client-portal-spec-2026-08-24.pdf (Read, pages 1-18)
- delta: macstack/deltas/2026-08-24-client-portal.md — K-1..K-9, N-1..N-18
- decisions: macstack/decisions/2026-08-24-client-feedback-rulings.md — D13..D23
- applied: USER-CASES.md 1.7→1.8 · UX-UI.md 1.2→1.3 · macstack.json (roles, lifecycle)
- opened: A10..A14 · closed: A6
- note: <the one thing a reader six months from now needs>
```

Bump `lifecycle.updated` to today's date in this same step — the two dates must
never disagree.

Second entry point (no file): record the source as `chat, YYYY-MM-DD` in both the
delta and this entry — there is no inbox row and no Gate 1 for it.

## 9. Verify — and what's machine-checkable vs. judgment

Run the `lint` skill → report 🟢/🟡/🔴 with numbered next steps. Lint plus this loop
together cover:

**Script it:** inbox file with no manifest row · inbox file with no merge entry naming
it in log.md · missing anchors · non-unique / non-ASCII / gap-numbered IDs · a cited
D<n> that doesn't resolve in DECISIONS.md · a struck A<n> with no closing decision id and date ·
USER-CASES header version ≠ last journal row · `lifecycle.updated` older than the
newest log.md entry · a delta past its age budget with no applied banner.

**Call it yourself:** whether a contradiction is real or the client's silence ·
whether an addition duplicates an existing case · whether a §B trigger has already
fired · whether OVERVIEW has started restating USER-CASES.

## Routing

| Situation | Do |
|---|---|
| No `macstack/` yet | `macstack-dev:documents` first |
| Delta has no contradictions | 3b bypass — apply directly, skip rulings |
| Anything headed for a client document or macstack.json | Never directly — always through this loop |
| Acceptance bullets changed | `macstack-dev:test-cases` in the same pass |
| After apply | `macstack-dev:lint` |
