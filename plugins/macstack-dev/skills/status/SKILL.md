---
name: status
description: This skill should be used when the user asks "project status", "where are we", "что сейчас в проекте", "на чём остановились", "what should I work on next", "что дальше", "покажи состояние", "am I on track", "what's blocking us", "status dashboard", "куда смотреть дальше", "что мешает", or wants a single-screen read of a macstack/ project's state before deciding what to do next.
---

# Status — the read-only orientation dashboard

Answers two questions in one screen: **where is this project, and what should I do
next?** The plugin has 17 other skills and none of them answer that — this is the
orientation entry point. **It reads, computes, renders. It writes nothing. Ever.**
No file is created, edited, or "fixed while here" — that is `docs-merge`, `test-cases`,
`lint`, or a human's job.

## What it reads

Resolve the folder first (`macstack-dev:project-docs`'s path rules), then read only
what exists — a missing document is reported missing, never treated as empty:

- `macstack.json` — `lifecycle.stage`, `lifecycle.updated`, `lifecycle.open_questions[]`,
  `lifecycle.needs_from_client[]`, `lifecycle.decisions[]`, `roles[].cases`,
  `docs.files.<key>.version`
- `USER-CASES.md` / `TEST-CASES.md` — case and test ids, document versions, acceptance bullets
- `TASKS.md` — milestones, tasks (`M<n>-T<n>`), backlog (`BL-<n>`), each task's `status`,
  `blocked_by`, `tracker`, and each milestone's `done_when`
- `OPEN-QUESTIONS.md` — §A owed by client (`A<n>`), §B deferred engineering (`B<n>`), asked-on dates
- `DECISIONS.md`, `CHANGELOG.md` (newest `R-YYYY-MM-DD`), `log.md`, `inbox/`, `deltas/*.md`

Exact anchors, id patterns, statuses and age budgets are defined once in
`${CLAUDE_PLUGIN_ROOT}/skills/project-docs/references/doc-contracts.json` — read it in
this project, never recall it from memory. Task glyphs: `todo ·` `doing ▶` `blocked ⏸`
`done ✓` `dropped ⊘` — reuse exactly these, invent no second vocabulary.

## The attention list is COMPUTED, never stored

No TODO file. Nothing to keep in sync, nothing to go stale — every line below is a
predicate over artifacts that already exist. When every predicate comes back empty,
say so in one line (`none — on track`) instead of printing an empty section.

1. **Unprocessed inbox** — a file in `inbox/` with no `merge` entry in `log.md` naming it.
2. **Stale delta** — a file in `deltas/*.md` with no applied banner, past its age
   budget (`deltas.age_budget_days` in doc-contracts.json: warn 14d / error 30d).
3. **Forgotten §A** — an open item past the same age budget, or carrying no "asked
   on" date — a question nobody actually put to the client is forgotten, not blocked.
4. **Client-blocked work** — an §A item that one or more tasks name in `blocked_by`.
   Rank these highest and say how many tasks each one blocks.
5. **Blocked task** — `status: blocked`, name exactly what blocks it.
6. **Tracker drift** — a task with no `tracker` id — the file and the team's tracker
   have diverged.
7. **Untested bullet** — an acceptance bullet in `USER-CASES.md` with no test in `TEST-CASES.md`.
8. **Stale test derivation** — `TEST-CASES.md` derived from an older `USER-CASES.md`
   version than the current one.
9. **Stale lifecycle** — `lifecycle.updated` older than the newest `log.md` entry.
10. **Unverified milestone** — every task under a milestone is `done`, but its
    `done_when` checks are not recorded as met.
11. **Silent work** — no `work` entry in `log.md` for N days while tasks sit in
    `doing` — work happening with no trace.

Name the exact file and id for every hit. Never summarize a hit as "some tests
missing" when the ids are known.

## The render

One screen, adapt if you can do better:

1. **Header** — project name, `lifecycle.stage`, date of the newest `log.md` entry,
   current release from `CHANGELOG.md`.
2. **Milestone tree** — milestone, then its tasks, using the glyph vocabulary.
   Collapse a fully-`done` milestone to one line with a count (`✓ done (6/6)`).
3. **Coverage**, one row each — cases per role · tested bullets / total · open items
   §A / §B · decisions recorded.
4. **⚠ Attention** — the computed list, most consequential first (client-blocking
   items outrank everything), each with its file and id. Or `none — on track`.
5. **The exact next command** — one copy-pasteable line, chosen from what the state
   implies: unprocessed inbox → `/macstack-dev:docs-merge`; untested bullets →
   `/macstack-dev:test-cases`; blocked on the client → the §A ids to chase; nothing
   blocking → the next `todo` task by milestone order. This line is the point of the
   whole skill — never end without one.

Worked example:

```
macstack status — Acme Checkout · stage: compose · updated 2026-08-10
last log entry: 2026-08-22 (work) · release: R-2026-08-15

M9  Checkout flow                                            ✓ done (6/6)
M10 Payments                                                 ▶ doing
  ✓ M10-T1  Stripe webhook handler
  ▶ M10-T2  Refund flow                    blocked by A4 (webhook secret rotation)
  ⏸ M10-T3  3-D Secure fallback            blocked_by: M10-T2
  ·  M10-T4  Payout report                 no tracker id
M11 Notifications                                             · todo (0/4)

Coverage — cases: 34 (12 critical) · tested bullets: 58/64 · open: 3×§A / 5×§B · decisions: 9

⚠ Attention
1. A4 blocks 2 tasks (M10-T2, M10-T3) — OPEN-QUESTIONS.md, asked 2026-07-30, 25d old
2. inbox/client-brief-2026-08-18.pdf has no merge entry — log.md
3. M10-T4 has no tracker id — TASKS.md
4. 6 acceptance bullets untested (C-11, C-14 x2, S-02 x3) — TEST-CASES.md

Next: chase A4 with the client — it blocks 2 tasks in M10.
```

## Graceful degradation

- A folder with only `macstack.json` (no `macstack/` documents yet) still produces a
  useful screen — header from `macstack.json` alone, empty coverage row marked
  "not tracked", and ends in `/macstack-dev:docs`.
- A project on the legacy root `macstack.json` path works the same way; note which
  path resolved.
- A missing document is reported **missing**, never treated as empty or zero.
- A count that cannot be determined is reported as **cannot be determined** — never
  guessed, never rounded to a nearby number.

## Report only what the artifacts show

Never estimate progress, never invent a percentage no file supports, never claim a
milestone is "close" or "almost done" — say what fraction of its tasks are `done` and
stop there. Never write, never create a missing file, never repair a stripped anchor
or a broken cross-reference — that is `lint`'s job to find and a human's or another
skill's job to fix; if lint would fail, say so and name `/macstack-dev:lint` rather
than reimplementing its rules. This skill reports project state and what to do next —
it does not judge conformance to the standard, and it does not duplicate the linter.
