---
description: Close the loop after work — reconcile the spec with the code and the client documents, rebuild the generated documents, re-derive test cases, journal the work and curate the changelog
argument-hint: [--after M11-T9 | --release M11 | (empty = every task finished since the last work entry)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill]
---

The closing half of the loop. Everything else in this plugin moves a requirement
towards code; this moves finished code back into the documents.

With no argument, find every task that reached `done ✓` since the newest `work` entry
in `history/ledger.jsonl`, and run the sequence for them together.

1. **Read the finished tasks' `spec` pointers.** That set of case ids is what
   determines which documents this pass has to look at. A task with no `spec` pointer
   cannot be swept — report it and fix the task rather than guessing.
2. **Journal it** — a `work` entry naming the task ids, what now exists that did not,
   and `notes`: the dead end taken, the thing that turned out harder, the decision
   deferred. A work entry with empty notes is usually a work entry not worth writing,
   because `what` is the half git already knows.
3. **`macstack-dev:sync`** — the technical half of the spec against the code, and the
   business half against `client/AUTOMATION.md` and `client/UX-UI.md`. It changes
   values, never ids: a new row needs an id, and an id is a decision.
4. **Re-render** `generated/ARCHITECTURE.md`, `generated/INDEX.md` and `README.md` with
   `documents`, then re-derive `generated/TEST-CASES.md` for the touched ids only with
   `macstack-dev:test-cases`. Regeneration is by id — update in place, never clobber
   hand-written manual steps.
5. **Bump what changed.** Each edited document gets a journal row and a version bump in
   all three places that must agree. Each document actually checked against the code
   gets a new `reviewed` date — and only those. `reviewed` is not `updated`, and
   conflating them is how a document stays confidently wrong.
6. **If it reached users**, write the `release` entry and its `CHANGELOG.md` twin of
   the same id, in the words of somebody who does not read code. Drop everything with
   no user-visible effect — a changelog that mirrors the log is a git log with extra
   steps. The exception: if `notes` says something did not work and the client saw it,
   the changelog does not get to quietly omit it.
7. **Report what is left to a human.** Client prose this change contradicts is listed,
   never rewritten. The plugin does not edit the client's own words on their behalf.

End with `lint`.
