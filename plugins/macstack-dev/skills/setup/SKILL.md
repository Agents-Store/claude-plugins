---
name: setup
description: This skill should be used when the user asks "what is macstack.json", "set up macstack", "check macstack setup", "verify macstack.json", "где схема macstack", or before any other macstack-dev skill runs in a project for the first time. Explains the standard, locates the schema and category registry, and verifies tooling.
---

# MACSTACK Setup & Orientation

macstack.json is the standardized JSON file of the MACSTACK framework (Multi-Agent
Composable Stacks). It lives in the **root of a Claude project** and is at once: the
business spec (goals, results), the technical spec (software, entities, interfaces,
workflows) and the meta-config from which project files are scaffolded. `CLAUDE.md`
references it — never duplicates it.

## Canonical resources (bundled)

- JSON Schema: `${CLAUDE_PLUGIN_ROOT}/skills/lint/references/macstack.schema.json`
- Category registry: `${CLAUDE_PLUGIN_ROOT}/skills/lint/references/software-categories.json`

Read the schema's top-level `description` first — it encodes the section order
(result-first): goals → results → processes → triggers → workflows → software →
entities → interfaces → connections → agents → context → resources.

## Core concepts (30 seconds)

- **Result-first**: every stack starts from goals/results in money terms; a process
  without a result is "coding for coding's sake".
- **prototype**: a parent macstack.json (GitHub repo `github:owner/repo` or a local
  absolute path). The child extends/overrides it — merge by `id`.
- **stacks**: organization composition — one `root` stack + `substacks`.
  Cross-stack refs use `<stack-id>:<element-id>`.
- **software[]**: every piece of software with mandatory `category` (registry) and
  `type` (ready_made | constructor | framework | library | custom), strict layers
  (data | logic | interface | infrastructure), `instances[]` with URLs.
- **agents**: `stack_agents` (orchestrate the whole stack, read `.claude/`, may modify
  the stack) and `managed_agents` (model + instructions + tools; invoked via
  interface / workflow / trigger / api).
- **Secrets are NAMES only**: `resources.accesses[]` lists env keys (with `required`
  flag); values live in Infisical.

## Verification steps

1. **Tooling**: `python3 -c "import jsonschema"` (fallback: structural checks only),
   `jq --version`, `gh --version` (needed for discover-context and github prototypes).
2. **Project state**: does `./macstack.json` exist?
   - Yes → validate it (`lint` skill) and report stage (`lifecycle.stage`).
   - No → offer `init-project` (existing codebase) or `generate-stack` (from scratch).
3. **CLAUDE.md link**: check CLAUDE.md contains a "Спецификация стека" section pointing
   to macstack.json. If missing, offer to add:

```markdown
## Спецификация стека
Бизнес- и техническая спецификация проекта — **`macstack.json`** (стандарт MACSTACK).
Читай его первым: goals → results → processes → workflows → software → entities → interfaces.
Не редактируй код, противоречащий macstack.json, — сначала обнови спецификацию.
```

## Skill routing

| Задача | Скилл |
|---|---|
| macstack.json в существующем проекте | `init-project` |
| Новый стек с нуля по запросу | `generate-stack` |
| Найти плагины/прототипы | `discover-context` |
| Создать рабочие файлы проекта | `scaffold-project` |
| .infisical.json + .env.prod/.env.dev | `infisical-env` |
| Правила и команды проекта | `best-practices` |
| Валидация | `lint` |
