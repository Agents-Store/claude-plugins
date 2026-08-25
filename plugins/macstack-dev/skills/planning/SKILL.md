---
name: planning
description: This skill should be used when the user asks to "add a task", "what's left to do", "что осталось сделать", "завести задачу", "план работ", "backlog", "milestone status", "sync tasks with the tracker", "синхронизировать задачи", "what should I work on next", "какая веха дальше", "add to the backlog", "отметить задачу выполненной", "block this on", "plan the changes", "what needs building", "turn the requirements into tasks", "which cases have no plan", or mentions TASKS.md, milestones, M<n>-T<n> ids, or the team's task tracker. Owns TASKS.md — milestones, tasks, backlog — turns unplanned requirements into task entries, and reconciles bidirectionally with whatever tracker the project is bound to, without ever naming a specific product.
---

# Planning — from a requirement to a task somebody can pick up

`TASKS.md` says what will be done, in what order, and how it will be known done. It
sits beside `USER-CASES.md` (the bar), `OPEN-QUESTIONS.md` (owed / deferred) and the
team's own task tracker — where the *conversation* happens: comments, attachments,
assignment, notifications. `TASKS.md` is the **source of truth** for scope and order;
the tracker is never edited around it.

Open `${CLAUDE_PLUGIN_ROOT}/skills/documents/references/doc-contracts.json`
(`documents.tasks`) for the anchors, id patterns and required fields first — this
skill assumes both and does not repeat them beyond the worked examples below.
Headings and prose follow `docs.language`; anchors and ids never translate.

## Layout and ids

```
<!-- macstack:section=howto -->        ## How to use this file
<!-- macstack:section=milestones -->   ## Milestones          M<n>
<!-- macstack:section=tasks -->        ## Tasks               M<n>-T<n>, grouped under their milestone
<!-- macstack:section=backlog -->      ## Backlog             BL-<n>, no milestone yet
<!-- macstack:section=journal -->      ## Journal             two columns: date, what changed
```

One anchor line immediately above the heading it marks, byte-exact, re-inserted
idempotently — never a reason to rewrite the file. ASCII only inside every id token
— a Cyrillic look-alike greps as absent. Ids are never renumbered, never reused; a
dropped task is struck, not deleted:

```
~~M11-T9~~ · DROPPED 2026-08-24 — superseded by M11-T14, same acceptance
```

## Status vocabulary

| Status | Glyph | Means |
|---|---|---|
| `todo` | · | not started |
| `doing` | ▶ | active now |
| `blocked` | ⏸ | `blocked_by` names what's in the way |
| `done` | ✓ | acceptance passed |
| `dropped` | ⊘ | struck — see the form above |

`status` and `tracker` are the two REQUIRED task fields. A task with no `tracker`
id is a lint ERROR — see Tracker sync below.

## One task, worked

````markdown
<!-- macstack:task=M2-T3 -->
### M2-T3 · Verify email before first login

```yaml
status: doing
tracker: TRACK-142
milestone: M2
spec: client/USER-CASES.md#C-02
files: [src/auth/verify.ts, src/auth/routes.ts]
acceptance: 'auth.int.spec.ts — "rejects unverified login"'
blocked_by: [A5]
```

<!-- macstack:notes -->
Remove the verify guard and that named test reddens. That is the check.
````

The status lives in the YAML block, not in the heading — v1 put a glyph after the
title and every tool had to parse a heading to learn a state. The glyph stays in the
`INDEX.md` render, where it is for the reader.

`spec` points, it never restates — the pointer plus `acceptance` is the row's whole
value; a paraphrase only drifts. `acceptance` names the test(s) and what each
asserts — where the project mutation-tests, "remove X and this named test reddens"
is the strongest form. `files` is the expected footprint; correct it as the task's
shape changes. `blocked_by` holds task or open-item ids (`A6`, `B3`) — an item
blocking three tasks is the argument for chasing the client.

## One milestone, worked

````markdown
<!-- macstack:milestone=M2 -->
## M2 · Auth hardening

```yaml
status: doing
target: 2026-09-15
```

<!-- macstack:done_when -->
- works in every role area at both narrow and wide viewport
- migrations proven, up and down, against a seeded snapshot
- `auth.pinning.spec.ts` unchanged and green
- full suite, zero skipped
- the `AuthContext` shape frozen for M3 and M4
- email verification required before the first booking action
- failed-login rate limit holds under the load test in CI

Order is strict: M2-T1 → M2-T2 → M2-T3 — the migration must land before the route
guard or local dev breaks mid-branch. Do not reorder without re-opening this note.
````

`done_when` is a list of FALSIFIABLE checks, typically 5–7; "works well" is not
one. Five recur across milestones — offer as the default, then add 2–3 specific to
this one: works in every role area at both viewports · migrations proven · a named
pinning test unchanged and green · full suite, zero skipped · a contract frozen for
downstream milestones. State an ordering note, with its reason, only when task
order genuinely may not change.

## Tracker sync — reconcile, never push

`TASKS.md` is the record; the tracker is the conversation. Never let one side
clobber the other silently, never invent a tracker id.

1. **Discover the binding** — `macstack.json` → `resources.bindings` for an entry
   that looks like a task tracker (project/workspace id, issue states), or a
   binding file in the project root. None found → say so and ask which tracker
   the team uses. Never assume a product.
2. **Discover the tools** — search the session's MCP tools at runtime for ones
   that read/write work items under that binding; never hard-code a tool name.
3. **Read both sides** — every `TASKS.md` task (id, status, title, `tracker` id)
   and every item under the bound project/workspace in the tracker.
4. **Diff, then stop for a human on any disagreement:**
   - Task with no `tracker` id → create it in the tracker, write back the id it
     returns. Never invent one.
   - Tracker item with no matching task → propose a new `BL-<n>` or `M<n>-T<n>`
     row; never add it unasked.
   - Status differs on one side only → surface the proposed update to the other
     side; a human confirms before either is written.
   - Status changed on **both** sides since the last sync → a conflict — present
     both values and ask, never pick a winner.
5. **No tracker tools available** → do the file-only half, report exactly which
   tasks lack a `tracker` id or have an unsynced status; never claim a sync happened.

## §B is debt kept; a task is debt scheduled

§B records what the team **consciously accepted**, and both its required fields
argue why *not* to act now (`reason-safe-to-defer`, `trigger-that-makes-it-unsafe`).
`TASKS.md` says what *will* be done — a §B item can sit for a year and stay
correct; it becomes a task only when its trigger fires. **Promotion**: add the
task with its own `spec`/`acceptance`, then strike the §B row pointing at the new
id — `~~B7~~ · PROMOTED 2026-08-24 → M3-T2` — leaving its original text untouched.

A `BL-<n>` backlog row is a task with no milestone yet: same required fields minus
`blocked_by`. Promoting one into a milestone keeps the same `tracker` id (never a
second tracker item) and strikes the `BL-<n>` row the same way. A commit subject
ending `(M11-T9)` links a commit to its task for free — worth the convention.

## Routing

| Situation | Do |
|---|---|
| No `TASKS.md` yet | `macstack-dev:documents` scaffolds it |
| "add a task" / "завести задачу" | Append under its milestone (or `backlog`), `todo`, `tracker` filled or created |
| "what's left" / "что осталось сделать" / "what should I work on next" | List `todo`/`doing` tasks not `blocked`, ordered by milestone |
| "milestone status" | Report the milestone's `done_when` checks, pass/fail |
| "sync tasks with the tracker" / "синхронизировать задачи" | Run the reconcile procedure above |
| Debt that's fine to sit | `OPEN-QUESTIONS.md` §B, not here |
| A §B trigger just fired | Promote it — see above |
| "what needs building" / nothing planned yet | Run the gap pass below |
| A task just reached `done` | `/macstack-dev:update` — it sweeps the documents |
| After any change | `macstack-dev:lint` |

## Finding the work nobody planned

The link between `client/USER-CASES.md` — what a person must get — and `TASKS.md` —
what will be done about it. Without it a requirement reaches the code through
somebody's memory, and nothing afterwards can say which change answered which
requirement.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planning/references/uncovered.py" macstack [--emit]
```

It reads three inputs — the cases, the tasks, and the newest
`history/reviews/*-conformance.md` — and sorts every case into four states:

| State | Means | Do |
|---|---|---|
| planned | a task already names it | nothing |
| audited: done | the newest review found it implemented | nothing |
| audited: partial | found partial or externally blocked | read the verdict first |
| **neither** | nobody planned it, nobody checked it | **this is the work** |

**Read the verdicts before reporting a number.** The first version of this reported
63 cases with no plan where 35 were already confirmed implemented by an audit — true,
and useless. A work list nobody believes is a work list nobody reads. Reading the
review cut the same report to 8. A gap report that ignores what has already been
checked reports the size of the document, not the size of the work.

`--emit` prints task skeletons. The skeleton is not the deliverable — `files` and
`acceptance` come back empty, and filling them is the only real work in this pass:

1. Open `generated/ARCHITECTURE.md` and find where this behaviour belongs. Use the map,
   not a blind recursive grep — in an iCloud-backed folder that hangs for minutes, and
   it finds the word rather than the behaviour either way.
2. Write `files` as the expected footprint.
3. Write `acceptance` as a named test and what it asserts. Strongest form: *remove X and
   this named test reddens*. A bare filename is not acceptance; a line number is banned.
4. Carry `blocked_by` through from the case's open items — an `A<n>` here is how a
   client question becomes visibly load-bearing.

### Three things this refuses to do

- **Guess `files` or `acceptance` without reading the code.** If the codebase does not
  answer where something belongs, that is a finding — say so and leave the field empty
  rather than filling it plausibly. A plausible wrong path costs more than an empty one,
  because somebody will follow it.
- **Plan a case an audit already passed.**
- **Invent a milestone.** A new milestone is a decision about scope and dates and it
  belongs to the owner. The script takes the last `M<n>` from `TASKS.md`; going past it
  is a question, not a default.

### Then stop

Do not start coding here. The handoff is the point: open plan mode and say *"take
M15-T2 from macstack/history/TASKS.md"*. A planning session that slides into
implementation produces a task list nobody finished writing and a change nobody
reviewed the plan for.
