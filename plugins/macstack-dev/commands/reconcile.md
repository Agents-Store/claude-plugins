---
description: Sync the code and every document in one declared direction — the code is master and the documents get corrected, or the documents are master and the gaps become tasks
argument-hint: --master=code | --master=docs [--dry] [--only <documents>]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion]
---

Use `macstack-dev:reconcile`.

`update` closes the loop after one task; `check` reports and writes nothing. This is the
command for the case neither covers: **code and documents have drifted apart wholesale**
and somebody has to say which side is right.

## `--master` is required

Without it, stop and print this, then ask which the user wants:

| | Means | Run it |
|---|---|---|
| `--master=code` | The code is what the product IS. Documents that disagree are corrected. | after a build phase, when the docs lag |
| `--master=docs` | The documents are the contract. Code that disagrees is work. | before a client review or a release |

There is no default on purpose. A default here picks the winner of every disagreement in
the folder without anybody deciding, and picking a winner silently is the one thing this
plugin refuses everywhere else.

## What runs

Five stages; only the fourth reads `--master`.

1. **`conformance`** — one verdict per case into the ledger. Nothing downstream may call
   a case built without a verdict saying so.
2. **`code-audit`** — what the code has that no document mentions: three lists, sorted
   by blast radius. Read `generated/ARCHITECTURE.md` as the map, never a blind grep.
3. **`sync`** — the spec against the documents and against the code. Values, never ids.
4. **Resolve.** `code` → each contradiction becomes an edit to the client document
   through the `intake` gate (delta → ruling → apply → journal). `docs` → each gap
   becomes a task through `planning`, with acceptance read out of the code.
5. **Settle.** Task statuses from the verdicts, both directions:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/planning/references/task_status.py" macstack --apply
   ```

   Then regenerate `generated/`, re-derive `TEST-CASES.md` for the touched ids, move
   `reviewed` **only for the documents this run actually read**, journal every edit, and
   finish with `lint`.

## Three things to raise rather than do

- **A statement the client answered.** A `comment` row in the ledger against that id
  means the client said something explicit about that sentence. Even with
  `--master=code`, collect these and ask — overruling a client's own answer silently is
  what the ledger exists to prevent.
- **Anything needing a new id**, a milestone, or a tracker item.
- **Anything contradicting a ruling** in `history/DECISIONS.md`.

Use AskUserQuestion for these, batched at the end — one question per contradiction turns
a reconcile into an interrogation, and the answer to most of them is the same.

## Report

A table with **one row per document in the contract — all seventeen**, saying what
happened to each and why. A document with no row is an error: "everything is synced" has
to be checkable rather than claimed.

Then the counts that matter — verdicts by kind, statuses moved, edits applied, questions
raised — and the single next command. After `--master=code` that is usually
`/macstack-dev:review`; after `--master=docs`, `/macstack-dev:plan`.

`--dry` runs every stage and writes nothing, including the ledger. Use it first on a
folder nobody has reconciled in months.
