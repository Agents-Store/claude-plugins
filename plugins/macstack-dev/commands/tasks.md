---
description: Add tasks, check milestone/backlog status, or sync TASKS.md with the team's tracker
argument-hint: "[add <what> | sync | status | milestone <id>]"
---

Use the macstack-dev:project-docs skill to resolve the folder, then macstack-dev:tasks
on `macstack/TASKS.md`. Route $ARGUMENTS: `add <what>` appends a task under the right
milestone (or `backlog` with none yet) — `todo`, a `spec` pointer, `acceptance`, and a
`tracker` id, creating one in the bound tracker if missing; `sync` runs the
bidirectional reconcile against the team's tracker and stops on any conflict for a
human call; `status` reports each milestone's `done_when` progress and the backlog;
`milestone <id>` scopes to one milestone's tasks and its `done_when` checks. With no
arguments, list `todo`/`doing` tasks that are not `blocked`, ordered by milestone.
Finish with macstack-dev:lint and report: tasks added or changed with their ids, what
was reconciled with the tracker, what conflicts need a human, and what is blocked and
by what.
