---
name: plan-changes
description: This skill should be used when the user asks "what do we build next", "turn the requirements into tasks", "что надо сделать по кейсам", "спроектировать правки", "составить ТЗ по требованиям клиента", "which cases have no plan", or needs the bridge between what the client agreed must be true and what an agent will actually change in the code. Turns uncovered user cases into task entries carrying files, acceptance and a pointer back to the requirement.
---

# From what the client agreed to what an agent will change

This is the link between `client/USER-CASES.md` — what a person must get — and
`history/TASKS.md` — what will be done about it. Without it a requirement reaches the code
through somebody's memory, and nothing afterwards can say which change answered which
requirement.

## Step 1 — find the real work list

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/plan-changes/references/uncovered.py" macstack
```

Every case lands in one of four states:

| State | Means | Do |
|---|---|---|
| задача заведена | somebody scheduled it | nothing |
| аудит: сделано | the newest `reviews/*-conformance.md` found it implemented | nothing |
| аудит: не до конца | the audit found it partial or externally blocked | read the audit's verdict first |
| **ни того ни другого** | nobody scheduled it, nobody checked it | **this is the work** |

**Reading the audit is what makes the number believable.** Without it the tool reports "63
cases with no plan" on a project where nearly all of them are built — true, useless, and a
work list nobody believes is a work list nobody reads.

## Step 2 — emit skeletons

```bash
python3 ".../uncovered.py" macstack --emit
```

Prints one task per uncovered case with its id, its name, and `spec:` pointing back at the
case. `files` and `acceptance` come out **empty on purpose.**

## Step 3 — fill in the two empty fields. This is the work of this skill

For each skeleton, read the codebase and complete:

- **`files`** — the paths the task is expected to touch. Find them: which collection holds the
  data, which route renders it, which workflow runs it. `generated/ARCHITECTURE.md` maps
  entities and workflows to code paths; use it rather than grepping blind.
- **`acceptance`** — how it will be known done, as **named tests**. Where the project
  mutation-tests, the strongest form is "remove X and this named test reddens". A bare
  filename is not acceptance and a line number is banned outright.
- **`blocked_by`** — the script fills open-item ids it found in the acceptance bullets. Add
  task ids where one task must land before another.

**Never restate the requirement in the task.** `spec` points at the case; a paraphrase in the
task is a second copy that drifts from the first, and the client only ever signed the first.

## Step 4 — append to TASKS.md, then hand off

Append the completed entries under their milestone in `history/TASKS.md`, add a journal row,
and stop. **Do not start coding here.**

The handoff is the point: open plan mode and say *"take M15-T2 from macstack/history/TASKS.md"*.
The agent then reads a task that names its files, its acceptance and the requirement it
answers — instead of being told the requirement again in the prompt, where nothing records
what it was for.

## What this skill refuses to do

**Guess `files` or `acceptance` without reading the code.** A plan whose file list is a guess
sends an agent to edit the wrong module, and the wrongness is invisible until review. If the
codebase does not answer where something belongs, that is a finding — say so and leave the
field empty rather than filling it plausibly.

**Plan a case an audit already passed.** Re-planning finished work is how a backlog becomes
noise.

**Invent a milestone.** New tasks join the newest milestone in `TASKS.md`; a new milestone is
a decision about scope and dates, and it belongs to the owner.

## When to run

After `docs-merge` accepts client changes, after `sync-spec` updates the spec, and before any
planning session. The number it prints — cases with no plan and no check — is the honest
answer to "what is left", and it is the only place that number exists.
