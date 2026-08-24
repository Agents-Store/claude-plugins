---
name: tasks
description: This skill should be used when the user asks to "add a task", "what's left to do", "что осталось сделать", "завести задачу", "план работ", "backlog", "milestone status", "sync tasks with the tracker", "синхронизировать задачи", "what should I work on next", "какая веха дальше", "add to the backlog", "отметить задачу выполненной", "block this on", or mentions TASKS.md, milestones, M<n>-T<n> ids, or the team's task tracker. Owns TASKS.md — milestones, tasks, backlog — and its bidirectional reconcile with whatever tracker the project is bound to, without ever naming a specific product.
---

# Tasks — Milestones, Backlog, and the Tracker

`TASKS.md` says what will be done, in what order, and how it will be known done. It
sits beside `USER-CASES.md` (the bar), `OPEN-QUESTIONS.md` (owed / deferred) and the
team's own task tracker — where the *conversation* happens: comments, attachments,
assignment, notifications. `TASKS.md` is the **source of truth** for scope and order;
the tracker is never edited around it.

Open `${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json`
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

```
### M2-T3 · Verify email before first login   doing ▶

- tracker: TRACK-142
- spec: §4.1–§4.3 of docs/design/auth-flow.md
- files: src/auth/verify.ts, src/auth/routes.ts
- acceptance: `auth.int.spec.ts` — "rejects unverified login"; remove the
  verify-guard and this test reddens
- blocked_by: —
```

`spec` points, it never restates — the pointer plus `acceptance` is the row's whole
value; a paraphrase only drifts. `acceptance` names the test(s) and what each
asserts — where the project mutation-tests, "remove X and this named test reddens"
is the strongest form. `files` is the expected footprint; correct it as the task's
shape changes. `blocked_by` holds task or open-item ids (`A6`, `B3`) — an item
blocking three tasks is the argument for chasing the client.

## One milestone, worked

```
## M2 · Auth hardening   doing ▶

done_when:
- works in every role area at both narrow and wide viewport
- migrations proven, up and down, against a seeded snapshot
- `auth.pinning.spec.ts` unchanged and green
- full suite, zero skipped
- the `AuthContext` shape frozen for M3 and M4
- email verification required before the first booking action
- failed-login rate limit holds under the load test in CI

Order is strict: M2-T1 → M2-T2 → M2-T3 — the migration must land before the route
guard or local dev breaks mid-branch. Do not reorder without re-opening this note.
```

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
| No `TASKS.md` yet | `macstack-dev:project-docs` scaffolds it |
| "add a task" / "завести задачу" | Append under its milestone (or `backlog`), `todo`, `tracker` filled or created |
| "what's left" / "что осталось сделать" / "what should I work on next" | List `todo`/`doing` tasks not `blocked`, ordered by milestone |
| "milestone status" | Report the milestone's `done_when` checks, pass/fail |
| "sync tasks with the tracker" / "синхронизировать задачи" | Run the reconcile procedure above |
| Debt that's fine to sit | `OPEN-QUESTIONS.md` §B, not here |
| A §B trigger just fired | Promote it — see above |
| After any change | `macstack-dev:lint` |
