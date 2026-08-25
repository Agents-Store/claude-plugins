---
description: Create or repair a project's macstack/ folder and macstack.json — from an existing codebase, from a business request, or by migrating an older layout
argument-hint: [project path | business request | --migrate]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Skill, WebFetch]
---

One entry point for everything that brings a project into the standard. Work out
which of the five it is, **say which and why, and wait for confirmation** before
writing anything. Guessing here is expensive: three of the five modes move or
overwrite files.

Read `macstack-dev:setup` first — it resolves paths, checks the tooling and tells you
what already exists.

| What you find | Mode |
|---|---|
| A codebase, no `macstack.json` | **audit** — read the code into a spec (`spec-authoring`) |
| No codebase, a business request in `$ARGUMENTS` | **design** — result-first from scratch (`spec-authoring`) |
| `macstack.json` at the repo root, or a flat/`docs/`-era layout, or v1 table-shaped documents | **migrate** — `documents`, migration mode |
| A valid spec, an incomplete `macstack/` | **repair** — `documents`, create only what is missing |
| A valid spec and folder, no project files | **scaffold** — `scaffold-project` |

Then, in order and without skipping:

1. **`spec-authoring`** — produce or complete `macstack.json`. For a hard case,
   delegate to the `macstack-architect` agent.
2. **`documents`** — create or repair `macstack/`, seeding the authored client
   documents once and rendering the generated ones. Read `document-format` before
   writing any document.
3. **`infisical-env`** — wire the environment if the spec declares accesses.
4. **`best-practices`** — install the project rules and commands.
5. **`scaffold-project`** — only in scaffold mode, and only in the mandatory source
   order: prototype → stack plugins → dev plugins → generation. That order is the
   product; every violation in testing produced files that contradicted the
   architecture.
6. **`lint`** — a spec that fails lint is not scaffolded from.

Finally write the `## Stack Specification` block into **both** `CLAUDE.md` and
`AGENTS.md`, pointing at `macstack/macstack.json` and naming the six client documents.
Both, not one: the documents are meant to be read by whichever coding agent the team
runs, and a spec only Claude Code can find is a spec half the team cannot use.

Report what was created, what was left alone, and the single next command.
