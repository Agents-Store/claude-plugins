---
name: lint
description: This skill should be used when the user asks to "validate macstack.json", "lint macstack", "check the stack spec", "проверь macstack.json", or after any skill of this plugin writes/edits macstack.json. Validates against the bundled JSON Schema and the referential-integrity rules.
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

No `jsonschema` lib → fallback to structural checks (required: macstack, name,
version, description; известные enum'ы) — и скажи юзеру, что полная валидация
пропущена.

## Pass 2 — Referential integrity (ошибки)

1. `results[].produced_by[*]` ∈ processes; `processes[].produces[*]` ∈ results —
   result-first: процесс без результата = «кодинг ради кодинга».
2. `results[].goal` ∈ goals.
3. `tasks[].workflow`, `workflows[].software`, `entities[].stores[].software`,
   `interfaces[].software|related[*]`, `connections.mcp[].software` разрешаются
   (свои id, унаследованные от prototype, или cross-stack).
4. `entities[].master` входит в stores ровно один раз с ролью master.
5. **Triggers**: `workflows[].triggers[*]` ∈ triggers; `triggers[].software` ∈ software,
   `instance` ∈ его instances.
6. **Instances**: `stores[].instance`, `mcp[].instance` ∈ instances соответствующего
   software; `interfaces[].instances[*]` ∈ instances своего software.
7. `software[]`: category ∈ реестра
   (`references/software-categories.json`), type заполнен, layers ⊆
   {data, logic, interface, infrastructure} без дублей, `agentic.rating` согласован
   (3×true=full, 2=good, 1=basic, только partial=partial, ничего=none).
8. **Cross-stack**: префикс `<stack-id>:` объявлен в `stacks.root.id` /
   `stacks.substacks[].id` / `stacks.links[].id`; `role: substack` → есть `root`.
9. **Agents**: `stack_agents[].access[*]` ∈ mcp|software|interfaces;
   `delegates_to` только вниз (control_plane → orchestrator → worker);
   `context_packs[*]` ∈ context.packs; `managed_agents[].tools.*` разрешаются;
   `invocations[*].interface|workflow|trigger` разрешаются.
10. **Env**: у `resources.accesses[].env` — ИМЕНА, не значения (строка, похожая на
    секрет/токен — ошибка); слаги kebab-case; `prototype` без циклов.

## Warnings (не блокируют)

- goal без единого result («цель без пути к ней»); result без goal при непустых goals.
- Триггер, на который не ссылается ни workflow, ни агент.
- software без agentic-паспорта; required-ключ отсутствует в `.env` (если файл есть).

## Output format

`ERRORS` списком (файл не годен к scaffold) → `WARNINGS` → `OK: schema + N правил
целостности` одной строкой. При prototype — сначала резолв и мёрж, линт итогового
слитого документа.
