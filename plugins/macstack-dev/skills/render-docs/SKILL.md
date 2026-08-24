---
name: render-docs
description: This skill should be used when the user asks to "render the generated docs", "rebuild ROLES.md", "update ARCHITECTURE.md", "пересобрать документы", "обновить роли и архитектуру", when lint reports rule 12.18 (a generated document differs from its source), or after any change to macstack.json's roles, processes, workflows, triggers, software, entities or context.plugins. Rebuilds the documents whose source of truth is the spec, not themselves.
---

# Render the generated documents

Three documents in `macstack/` are **not authored** — they are rebuilt from a source:

| Document | Source | Answers |
|---|---|---|
| `generated/ARCHITECTURE.md` | `macstack.json` | how the project is built, for the agent building in it |
| `README.md` | `doc-contracts.json` | this folder's own contract |

**`ROLES.md` used to be here and is not any more.** The direction was inverted: who does what
is now authored in `client/ROLES-AND-TASKS.md`, because a client cannot correct a generated
file and the client is the one who knows whether a task belongs to a role. `seed.py` writes its
first version and then never touches it; `sync-spec` reconciles the spec against it.

Each carries `<!-- macstack:generated from=… -->` on its second line. A hand edit to any
of them is lost on the next render, and lint reports the difference (rule 12.18) rather
than silently overwriting it.

## Run it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/render-docs/references/render.py" macstack
python3 "${CLAUDE_PLUGIN_ROOT}/skills/render-docs/references/render.py" macstack --check   # lint 12.18
```

`--check` renders into memory, prints a diff and exits non-zero. That is the form lint
uses; it writes nothing.

## Why a script and not instructions

Rule 12.18 re-renders and compares byte for byte. A renderer described in prose produces
a slightly different document every run — a different word here, a reordered table there —
so the rule would be permanently red and everyone would learn to ignore it. **The renderer
is therefore deterministic code, and everything it emits is a pure function of the spec:**
no timestamp in the body, no iteration whose order depends on a hash, nothing invented at
render time.

## The one thing that survives a rebuild

The **journal**. Those rows are human history and the spec does not contain them, so the
renderer reads them back out of the existing file and carries them forward. A new row is
appended only when the rendered body actually changed — which is what keeps a second run
byte-identical to the first, and what keeps rules 12.18 and 12.19 from fighting each other.

## What goes where, and what must NOT

`seed.py` writes the first `client/ROLES-AND-TASKS.md` and `client/SCREENS.md` and **refuses
to overwrite them**. A role section there lists only what a PERSON does; automation is the
Triggers table, a reverse index of schedule or event → what it raises.

That split was a measured mistake first: an earlier renderer listed, under each role, every
workflow of every process where that role had any task. Under *Coach* it produced invoice
issuance and the Sonderänderung flow — neither of which a coach may touch. **A process workflow
does not belong to a role.** Filing it under one because they share a process misstates that
person's duties, which is precisely the failure a roles document exists to prevent.

`ARCHITECTURE.md` does **not** replace `docs/architecture.md`. It holds what can be
rebuilt from the spec — software, entities and their stores, workflows and their code paths,
integrations and plugins. The measured trap, the argument behind a decision, the rake already
stepped on: those cannot be regenerated, they belong in `docs/`, and merging the two makes
one of them a worse copy of the other.

## When to run

- After editing `roles[]`, `processes[].tasks[]`, `workflows[]`, `triggers[]`, `software[]`,
  `entities[]`, `connections` or `context.plugins` in `macstack.json`.
- When `lint` reports 12.18.
- As the last step of `docs-migrate` and of `project-docs` folder creation.

Never edit the three documents by hand — fix the spec and render. If the spec cannot express
what you want to say, that is the signal the sentence belongs in an authored document instead.
