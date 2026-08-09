---
name: lint
description: This skill should be used when the user asks to "validate macstack.json", "lint macstack", "check the stack spec", "verify macstack.json integrity", or after any skill of this plugin writes/edits macstack.json. Validates against the bundled JSON Schema and the referential-integrity rules.
---

# Lint macstack.json

Two passes: JSON Schema, then referential integrity. A file that fails lint must not
be scaffolded from.

## Pass 1 — JSON Schema

Schema: `${CLAUDE_PLUGIN_ROOT}/skills/lint/references/macstack.schema.json`.

```bash
python3 - <<'EOF'
import json, jsonschema
schema = json.load(open("<PLUGIN_ROOT>/skills/lint/references/macstack.schema.json"))
doc = json.load(open("macstack.json"))
jsonschema.validate(doc, schema)
print("schema: VALID")
EOF
```

No `jsonschema` lib → fall back to structural checks (required: macstack, name,
version, description; the known enums) — and tell the user that full validation was
skipped.

## Pass 2 — Referential integrity (errors)

1. `results[].produced_by[*]` ∈ processes; `processes[].produces[*]` ∈ results —
   result-first: a process with no result is "coding for coding's sake".
2. `results[].goal` ∈ goals.
3. `tasks[].workflow`, `workflows[].software`, `entities[].stores[].software`,
   `interfaces[].software|related[*]`, `connections.mcp[].software` resolve
   (own ids, ids inherited from the prototype, or cross-stack).
4. `entities[].master` appears in stores exactly once with the master role.
5. **Triggers**: `workflows[].triggers[*]` ∈ triggers; `triggers[].software` ∈
   software, `instance` ∈ its instances.
6. **Instances**: `stores[].instance`, `mcp[].instance` ∈ the instances of the
   matching software; `interfaces[].instances[*]` ∈ the instances of its software.
7. `software[]`: category ∈ the registry
   (`references/software-categories.json`), type filled, layers ⊆
   {data, logic, interface, infrastructure} without duplicates, `agentic.rating`
   consistent (3×true=full, 2=good, 1=basic, only partial=partial, nothing=none).
8. **Cross-stack**: the `<stack-id>:` prefix is declared in `stacks.root.id` /
   `stacks.substacks[].id` / `stacks.links[].id`; `role: substack` → `root` present.
9. **Agents**: `stack_agents[].access[*]` ∈ mcp|software|interfaces;
   `delegates_to` only downward (control_plane → orchestrator → worker);
   `context_packs[*]` ∈ context.packs; `managed_agents[].tools.*` resolve;
   `invocations[*].interface|workflow|trigger` resolve.
10. **Env**: `resources.accesses[].env` holds NAMES, not values (a string that looks
    like a secret/token is an error); slugs are kebab-case; `prototype` has no cycles.

## Warnings (non-blocking)

- A goal with no result ("a goal with no path to it"); a result with no goal when
  goals are non-empty.
- A trigger referenced by no workflow and no agent.
- Software without an agentic passport; a required key missing from `.env` (when the
  file exists).

## Output format

`ERRORS` as a list (the file is not scaffold-ready) → `WARNINGS` → one `OK: schema +
N integrity rules` line. With a prototype set — resolve and merge first, lint the
merged document.
