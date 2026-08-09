---
name: troubleshoot
description: This skill should be used when the user reports "macstack lint fails", "prototype не резолвится", "env keys missing", "scaffold сломал файлы", "cross-stack ссылка не работает", or any macstack-dev skill errors out. Diagnoses the common failure modes of the macstack.json toolchain.
---

# Troubleshoot macstack-dev

## Lint failures

| Симптом | Причина → фикс |
|---|---|
| `entity master problem` | master не входит в stores ровно один раз с role=master → добавь store с ролью master или поправь `master` |
| `category не в реестре` | опечатка или новая ниша → сверь со `references/software-categories.json`; новая категория = kebab-слаг + предложение в реестр (PR), не молчаливый кастом |
| `rating mismatch` | agentic.rating не совпадает с каналами → правило: 3×true=full, 2=good, 1=basic, только "partial"=partial |
| `trigger unknown` | workflow ссылается на код триггера, которого нет в `triggers[]` → триггеры живут ТОЛЬКО в коллекции, не инлайн |
| `делегация не вниз` | orchestrator в delegates_to у worker'а → иерархия строго control_plane → orchestrator → worker |
| `x-stack не объявлен` | префикс `foo:` не объявлен → добавь стек в `stacks.root/substacks/links` |

## Prototype resolution

- `github:owner/repo` не клонится → проверь `gh auth status` / приватность репо;
  для приватных нужен PAT. Fallback: попроси юзера дать локальный absolute path.
- В репо нет `macstack.json` → это legacy-прототип (только `stack.json`): используй
  его файлы для scaffold, но наследовать нечего — зафиксируй в open_questions.
- Цикл прототипов (A→B→A) → ошибка by design; разорви цепочку.
- Локальный path в iCloud-папке может «висеть» при первом чтении (материализация) —
  повтори или скопируй прототип в обычную папку.

## Infisical / env

- `infisical secrets` читает не тот инстанс → CLI игнорирует `--domain` на
  authenticated reads; активен один инстанс — сначала `infisical login --domain=…`.
- `.env` затёрся пустым → в setup.sh нет guard'а: fetch во временный файл, mv только
  при успехе. Восстанови из Infisical повторным pull.
- required-ключ есть в macstack.json, но пуст после sync → его нет в Infisical:
  создать там; `provided_by: client` → в `lifecycle.needs_from_client`.
- Значения с `$`/пробелами ломают `source .env` → рендерить `KEY='value'`
  в одинарных кавычках (внутренняя кавычка → `'\''`).

## Scaffold

- Перезаписал пользовательский файл → нарушение идемпотентности: существующий файл с
  отличиями = diff + вопрос, никогда молчаливый overwrite. Восстанови из git.
- Файлы не совпадают с архитектурой → нарушен порядок источников: prototype →
  stack-плагины → dev-плагины; переделай от prototype.
- `${VAR}` из .mcp.json не резолвится → значения должны быть в env-блоке
  `.claude/settings.local.json` (заполняет scripts/setup.sh), не в .mcp.json.

## Discovery

- `curl raw.githubusercontent.com/...marketplace.json` → 404: ветка не `main` или
  репо приватный → `gh api repos/agents-store/claude-plugins/contents/...`.
- Нет плагина для software → gap в open_questions + предложение создать через
  plugin-creator; НЕ вписывать несуществующее имя в context.plugins.
