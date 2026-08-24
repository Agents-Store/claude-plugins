---
name: sync-spec
description: This skill should be used when the user says "client corrected the tables", "sync the spec with the documents", "синхронизировать спеку с документами", "клиент поправил роли", "the roles document and macstack.json disagree", when lint reports that the business half of macstack.json differs from client/ROLES-AND-TASKS.md, or after anyone edits the task, trigger or screen tables. Reconciles macstack.json against the documents the client actually reads.
---

# Reconcile the spec with the client's documents

`client/ROLES-AND-TASKS.md` and `client/SCREENS.md` are **authored** — a human writes them and
the client corrects them. The business half of `macstack.json` is the same facts in machine
form. This skill compares the two and reports every disagreement.

## Run it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sync-spec/references/sync-spec.py" macstack
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sync-spec/references/sync-spec.py" macstack --apply
```

Dry run by default. `--apply` writes only the changes it can make safely.

## What it changes, and what it refuses to

**Changes:** values of items it matched — today the gate of a task (`input` / `execute` /
`approve`).

**Refuses:** creating or deleting anything. A new row needs an **id**, and an id is a decision:
workflows, tests and prose all reference it. A machine that invents one is a machine that
silently orphans every reference the next time somebody renames the row. New and missing rows
are reported; a human gives them ids.

This is also why a **rename shows up as one addition and one removal.** Without an id in the
document the two are genuinely indistinguishable, and the report says so rather than guessing.
If renames are frequent, that is the argument for carrying ids in the tables — pay the clutter
and get the difference.

## The direction, and where it stops

| From the documents | To the spec |
|---|---|
| roles and their names | `roles[]` |
| tasks with their gates | `processes[].tasks[].human` |
| triggers, type and schedule | `triggers[]` |
| screens and their addresses | `interfaces[]` id, name, path, roles |

**Not derivable from any client document, and never touched here:** where a workflow lives in
the code, what engine runs it, which entities and software exist, what is actually implemented.
Those are the architect's, measured against the code. Claiming to generate them from a client's
table would be a promise the format cannot keep — and the failure would be silent, which is
worse than the gap.

## Columns are read by position

The header row follows `docs.language`; the parser never looks at it. A project writing its
documents in German parses identically to one writing in Russian. **Never reorder the columns**
— that is the one edit to these tables that breaks the tool, and it breaks it quietly.

## When to run

After the client returns a package, after anyone edits the tables, and before a release. Lint
calls it too: a spec that disagrees with the document the client signed off on is the failure
this whole folder exists to prevent.
