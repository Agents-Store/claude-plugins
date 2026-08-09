---
name: best-practices
description: This skill should be used when the user asks to "install best practice rules", "поставь правила проекта", "add project rules and commands", "set up project conventions", or scaffold-project reaches the rules step. Installs the proven MACSTACK rule set (.claude/rules) and core commands into a project.
---

# Install Best-Practice Rules & Commands

Every MACSTACK project ships the same battle-tested `.claude/rules/` and core
commands (проверены в продакшн-оркестраторе VK-OPS). Install them at scaffold time;
adapt wording to the project, never drop a rule silently.

## Mandatory `.claude/rules/`

Create each file; content = короткая версия правила + WHY:

1. **`safety.md`** — Never: commit secrets (`.env`, tokens, `.mcp.json` со значениями),
   `any` в TypeScript, display names вместо resource IDs в MCP-вызовах, удаление
   прод-данных без подтверждения, хардкод URL/токенов. Always: валидация на границах,
   обработка 401/404/429/500 у внешних вызовов, env-переменные для кредов,
   `created_at`/`updated_at` на всех таблицах, batch-эндпоинты для >10 записей.
2. **`secrets-env-sync.md`** — Infisical = источник истины; локальные `.env*` —
   рабочие копии; изменил env → `/secrets-push`; перед деплоем/пушем → `/env-audit`;
   push = upsert (не удаляет); никогда не коммитить `.env*` (см. скилл
   `infisical-env`).
3. **`commit-after-task.md`** — Conventional Commits (`type(scope): summary`),
   маленькие частые коммиты после каждой законченной единицы работы; тело с WHAT/WHY;
   коммит ≠ пуш (пуш — отдельное явное действие).
4. **`search-first.md`** — Part A: реюз перед написанием (кодовая база → зависимости →
   с нуля); Part B: 2+ неудачные попытки / незнакомый API → искать официальные доки
   (Context7 → llms.txt → web), не гадать.
5. **`external-api-docs.md`** — перед кодом против стороннего SDK/API сверься с
   официальными доками (llms.txt карта сервисов стека); training data протухает.
6. **`project-conventions.md`** — naming: TS PascalCase/camelCase/kebab-файлы; БД
   snake_case, FK `{table}_id`, boolean `is_*/has_*`, timestamps `*_at`; workflows
   `[Domain] - [Action] - [Trigger]`; API kebab-URLs.
7. **`macstack-sync.md`** (новое, специфичное для стандарта) — macstack.json = живая
   спецификация: любое изменение стека (новый software/workflow/entity/интерфейс)
   сопровождается обновлением macstack.json + `lint` в том же коммите; definition of
   done включает синк спеки.

Если проект деплоится на PaaS (dokploy/coolify) — добавь `deploy-verify.md`
(деплой закончен, когда билд done + контейнеры healthy + логи чистые + домен 200).

## Mandatory `.claude/commands/`

| Command | Что делает |
|---|---|
| `commit.md` | Conventional commit по правилу commit-after-task |
| `pr.md` | Создать PR (тело: what/why, ссылка на work item) |
| `secrets-sync.md`, `secrets-push.md`, `env-audit.md`, `setup-tokens.md` | из скилла `infisical-env` |
| `update-context.md` | обновить macstack.json + CLAUDE.md + .env.example после изменений стека (аналог sync) |
| `macstack-lint.md` | прогнать скилл `lint` |

## CLAUDE.md wiring

Ensure CLAUDE.md: (1) секция «Спецификация стека» → macstack.json; (2) перечисляет
rules как MANDATORY одной строкой каждое; (3) остаётся коротким (<100 строк) — детали
живут в rules/skills/macstack.json, не в CLAUDE.md.

## Rules for applying

- Идемпотентно: existing rule file с локальными правками — не перезаписывать, показать diff.
- Правила — файлы проекта (коммитятся), плагин лишь устанавливает их начальные версии.
