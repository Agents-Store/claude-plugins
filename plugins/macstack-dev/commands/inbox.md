---
description: Take in client material — a document, a returned review package, a list of corrections — and merge it into macstack/ through the delta → gate → ruling → apply loop
argument-hint: [file in inbox/ | artifact URL | what to change]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill]
---

Use `macstack-dev:intake`. It owns the loop; this command only routes into it.

The loop, and none of it is optional:

1. **Land it.** The file goes into `inbox/` under an ASCII name and gets an entry in
   the manifest. A source already committed in this repo is cited by path, never
   copied. Nothing in `inbox/` is ever edited afterwards.
2. **Read it.** Check size and first bytes before parsing — an iCloud placeholder
   reads as empty and yields a confidently wrong delta. `.xlsx` is refused: ask for a
   CSV beside it and write no log entry, so the file stays in the unprocessed set.
3. **Write the delta** into `history/deltas/` — contradictions `K-<n>` with their blast
   radius, additions `N-<n>` grouped by role, what the document confirms, and what it
   does not touch at all. A delta is a proposal, not an edit.
4. **Gate.** Contradictions are ruled on by the owner, not by this session. Allocate
   the `D<n>` ids in `DECISIONS.md` in their own commit first, then write the rulings
   file with a `cost-if-wrong` clause on each — written now, before the outcome is
   known, because a retrospective cost clause is worthless.
5. **Apply** to the client documents, bumping each document's version in all three
   places, and to the spec's business half through `sync`.
6. **Log** a `merge` entry naming the source, the delta, the decisions, what was
   applied, what opened and what closed.

If `$ARGUMENTS` is an artifact URL, read the comment threads from it first and turn
them into ordinary incoming material. Do not build a second path for returned
packages — the one that exists is the best-tested part of this plugin, and a parallel
one is a second place for a client's change to get lost.
