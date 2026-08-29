---
description: Close the loop after work — bring the client documents, the spec and the generated documents up to what the code now does, move task statuses to what the audit found, journal the work and curate the changelog
argument-hint: [--after M11-T9 | --release M11 | --dry | (empty = every task finished since the last work entry)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion]
---

The closing half of the loop. Everything else in this plugin moves a requirement
towards code; this moves finished code back into the documents — **all of them**, the
client's included.

With no argument, find every task that reached `done` since the newest `work` entry in
`history/ledger.jsonl`, and run the sequence for them together.

This is `macstack-dev:reconcile --master=code` **scoped to the finished tasks** rather
than to the whole folder, and it uses that skill for the document half rather than
carrying its own copy. Two implementations of one rule diverge silently, and the first
sign is two commands telling you different things about the same document.

1. **Read the finished tasks' `Closes` pointers.** That set of case ids is what
   determines which documents this pass has to look at. A task with no pointer cannot be
   swept — report it and fix the task rather than guessing.

2. **Journal it** — a `work` entry naming the task ids, what now exists that did not,
   and `notes`: the dead end taken, the thing that turned out harder, the decision
   deferred. A work entry with empty notes is usually a work entry not worth writing,
   because `what` is the half git already knows.

3. **Verdict each swept case** — `macstack-dev:conformance`, one `audit` row per case.
   Steps 4 and 6 both read those rows; without them this command would be asserting that
   the work is done because somebody ticked a box.

4. **Actualise the client documents** — `macstack-dev:reconcile`, stage 4, `code` as
   master, over the swept ids only. Each acceptance bullet, screen prohibition, trigger
   and handbook step the code now contradicts is **corrected**, through the `intake`
   gate: delta → ruling → apply → journal. The `v3` writer patches the named line and
   leaves the prose around it alone.

   Three things become a question instead of an edit, and the first is the one that
   matters: **a statement the client answered.** A `comment` row against that id means
   the client said something explicit about that sentence, and code does not get to
   overrule it silently. The others are anything needing a new id, and anything
   contradicting a ruling in `history/DECISIONS.md`. Batch them into one
   AskUserQuestion at the end.

5. **`macstack-dev:sync`** — the technical half of the spec against the code, and the
   business half against the documents step 4 just corrected. That order matters: sync
   the spec against documents that still describe the old behaviour and you write
   yesterday's facts into `macstack.json`.

6. **Move the task statuses to what the audit found:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/planning/references/task_status.py" macstack --apply
   ```

   Both directions. A task whose every case is `implemented` closes and gets today's
   `Finished` date; a task standing `done` whose case the audit found `absent` is
   **reopened** — the case this command exists to catch, because a work list that looks
   shorter than the truth is one nobody goes looking behind.

7. **Re-render** `generated/ARCHITECTURE.md`, `generated/INDEX.md` and `README.md` with
   `documents`, then re-derive `generated/TEST-CASES.md` for the touched ids only with
   `macstack-dev:test-cases`. Regeneration is by id — update in place, never clobber
   hand-written manual steps.

8. **Bump what changed.** Each edited document gets a journal row and a version bump in
   all three places that must agree. Each document **actually checked against the code**
   gets a new `reviewed` date — and only those. `reviewed` is not `updated`, and
   conflating them is how a document stays confidently wrong while lint stays green.

9. **If it reached users**, write the `release` entry and its `CHANGELOG.md` twin of the
   same id, in the words of somebody who does not read code. Drop everything with no
   user-visible effect — a changelog that mirrors the log is a git log with extra steps.
   The exception: if `notes` says something did not work and the client saw it, the
   changelog does not get to quietly omit it.

10. **Report per document, not per task.** One row for every document the sweep touched
    and every one it deliberately did not, with the reason. Then the questions from step
    4, and the single next command — usually `/macstack-dev:review`, because the
    documents moved and the client has not seen it.

`--dry` runs all ten and writes nothing, ledger included.

End with `lint`.
