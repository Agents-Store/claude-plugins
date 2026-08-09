---
name: scaffold-project
description: This skill should be used when the user asks to "scaffold the project from macstack.json", "создай рабочие файлы проекта", "разверни проект по macstack.json", "generate project files", or after a macstack.json is validated and the working tree must be built. Creates project files strictly in the prototype → stack plugins → dev plugins order.
---

# Scaffold Project Files From macstack.json

Turn a validated macstack.json into a working Claude project. The knowledge-source
order below is MANDATORY — it prevents reinventing what the ecosystem already
standardized. Each source overrides generic defaults; later sources fill what earlier
ones did not.

## THE ORDER (не нарушать)

### 1. PROTOTYPE FIRST — `macstack.json.prototype`

If `prototype` is set, resolve and study it BEFORE writing any file:

- `github:owner/repo[#ref]` or https-URL → clone shallow:
  `git clone --depth 1 https://github.com/owner/repo "$TMP/proto"`
- Absolute path (`/Users/...`) → это локальная папка, читай напрямую.
- Папка/репо → корневой `macstack.json`; merge-by-id даёт унаследованный состав.

From the prototype take (copy, then adapt): directory layout, `docker-compose.yml`,
config files (trigger.config.ts, next.config.ts…), `scripts/`, `.claude/`
(rules/commands/skills), `.env.example`, CLAUDE.md skeleton, `.gitignore`.
The prototype is the ground truth for HOW this stack is assembled — файлы из него
важнее любых общих шаблонов. Chain prototypes resolve recursively (child wins).

### 2. STACK PLUGINS SECOND — `context.plugins.stack[]`

Плагины с суффиксом/префиксом **stack** описывают АРХИТЕКТУРУ связки: слои,
integration patterns (a-to-b потоки), decision frameworks, `.mcp.json` с `${VAR}`,
`templates/.env.example`, `templates/CLAUDE.md.template`.

- Install/enable them in `.claude/settings.json` → `enabledPlugins`
  (`"<plugin>@<marketplace>": true`).
- Generate the project's `.mcp.json` from the stack plugin's template (или из
  `connections.mcp` в macstack.json, если stack-плагина нет) — `${VAR}` placeholders,
  НИКОГДА значения.
- Architecture rules from the stack plugin's CLAUDE.md.template merge into the
  project CLAUDE.md.

### 3. DEV PLUGINS THIRD — `context.plugins.technology[]`

Плагины `{tool}-dev` говорят, КАК разрабатывать на каждом software из архитектуры
(SDK-паттерны, API, готчи). Enable them, and follow their conventions when writing
initial code stubs (например: Directus SDK `cache: 'no-store'`; Trigger.dev v4
импорты из `@trigger.dev/sdk/v3`). Do not copy their content into the project —
plugins own tool knowledge; the project only references them.

### 4. Only then — generate project files

С опорой на источники 1→3 создай:

| Артефакт | Источник |
|---|---|
| Каркасы software (указан `nextjs` → Next.js заготовка; `trigger-dev` → trigger.config.ts + `src/trigger/`) | prototype, затем dev-плагины |
| `CLAUDE.md` (секция «Спецификация стека» → macstack.json; Tech Stack из software; Installed Plugins из context.plugins) | prototype + stack-плагин template |
| `.mcp.json` (`${VAR}`) | stack-плагин / connections |
| `.env.example`, `.env.prod`, `.env.dev`, `.infisical.json` | скилл `infisical-env` (обязательно вызвать) |
| `.claude/rules/`, `.claude/commands/`, `scripts/` | скилл `best-practices` (обязательно вызвать) |
| Заготовки workflows (по `workflows[]`+`triggers[]`) и entities (схемы/миграции) | macstack.json + dev-плагины |

## Rules

- **Идемпотентность**: повторный запуск доращивает недостающее и НИКОГДА не затирает
  пользовательский код (existing file + отличие → показать diff, спросить).
- **Никаких секретов в файлах**: только имена ключей; значения приходят через
  `infisical-env`.
- Every generated piece must trace to macstack.json (software/workflow/entity id) —
  файл, который ни к чему не привязан, не создаём (это и есть «кодинг ради кодинга»).
- After scaffolding run `lint` again + report: созданные файлы, что взято из
  prototype / stack-плагина / dev-плагинов, что осталось ручным (open_questions).

<example>
user: "Разверни проект по macstack.json"
→ prototype github:stackmakers-ai/project-directus-nextjs-trigger-dev → clone, копирую
  compose/scripts/.claude/структуру
→ stack-плагин stack-directus-nextjs-trigger-dev → enabledPlugins + .mcp.json (${VAR}) + CLAUDE.md merge
→ dev-плагины directus-dev, nextjs-dev, trigger-dev → enable, конвенции для стабов
→ файлы: src/trigger/<wf-id>.ts по workflows[], collections-схемы по entities[]
→ infisical-env → best-practices → lint → отчёт
</example>
