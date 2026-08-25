---
description: Turn requirements nobody scheduled into well-described tasks, edit tasks and milestones, and reconcile TASKS.md with the team's own tracker
argument-hint: [add <what> | sync | status | milestone <id> | (empty = find unplanned work)]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill]
---

Use `macstack-dev:planning`.

With no argument: find the work nobody has planned. Run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planning/references/uncovered.py" macstack [--emit]
```

which classifies every case into four states — already planned · confirmed done by the
newest conformance review · found partial or blocked by it · **neither planned nor
checked**. Only the fourth is work.

Read the audit verdicts before reporting a number. The first version of this reported
"63 cases with no plan" where 35 were already confirmed implemented: true, and useless.
A work list nobody believes is a work list nobody reads.

Then do the part the script cannot: **read the code** and fill each skeleton's `files`
and `acceptance`. Use `generated/ARCHITECTURE.md` as the map rather than a blind grep.
Acceptance names a test, and its strongest form is *remove X and this named test
reddens*. A bare filename is not acceptance; a line number is banned outright.

Three things this refuses to do:

- **Guess `files` or `acceptance` without reading the code.** If the codebase does not
  answer where something belongs, that is a finding — say so and leave the field empty
  rather than filling it plausibly.
- **Plan a case an audit already passed.**
- **Invent a milestone.** A new milestone is a decision about scope and dates and it
  belongs to the owner. Take the last `M<n>` and ask before going past it.

Then stop. The handoff is the point: open plan mode and say *"take M15-T2 from
macstack/history/TASKS.md"*. Do not start coding here.

`sync` reconciles with the team's tracker in both directions and stops at every
disagreement rather than picking a winner. `status` and `milestone <id>` report
progress against `done_when`.
