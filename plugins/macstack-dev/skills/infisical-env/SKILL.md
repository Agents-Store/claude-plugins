---
name: infisical-env
description: This skill should be used when the user asks to "set up Infisical for this project", "создай .infisical.json", "подтяни env ключи", "wire the env", "sync secrets", or scaffold-project reaches the env step. Creates .infisical.json, pulls .env.prod/.env.dev, ensures every key from macstack.json resources.accesses exists, and installs the mandatory secrets scripts and commands.
---

# Infisical & Env Wiring (обязательный контур секретов)

Every MACSTACK project keeps secrets in **Infisical** (source of truth); local `.env*`
are working copies. macstack.json's `resources.accesses[]` is the canonical list of
key NAMES. This skill wires the three together. Values NEVER appear in git or in
macstack.json.

## Step 1 — `.infisical.json` (обязательный биндинг, коммитится)

Create in the project root:

```json
{
    "workspaceId": "<UUID Infisical-проекта>",
    "defaultEnvironment": "prod",
    "gitBranchToEnvironmentMapping": null
}
```

- Workspace не существует → создать в Infisical UI/CLI (имя = `identity.name` из
  macstack.json) и вписать его ID. `.infisical.json` — НЕ секрет, коммитится (это
  биндинг, как .dokploy.json).
- Домен Infisical — из реестра организации (root-стек / projects.json,
  `infisical.domain`), НЕ хардкодить в скриптах.

## Step 2 — env-ключи из macstack.json

`resources.accesses[]` — источник истины по именам:

1. Сгенерируй `.env.example`: по строке `KEY=` на каждый access (комментарий: `for`,
   `provided_by`, `required`). Коммитится.
2. Убедись, что каждый `required: true` ключ СУЩЕСТВУЕТ в Infisical (prod env);
   отсутствующие — создать с пустым/временным значением и перечислить юзеру
   («заполнить в Infisical»). Ключи с `provided_by: "client"` — в
   `lifecycle.needs_from_client`.
3. Pull: `.env.prod` ⇄ Infisical prod, `.env.dev` ⇄ Infisical dev, `.env` = рабочая
   копия prod. Все три gitignored (`.env*` catch-all + `!.env.example`).

## Step 3 — обязательные скрипты (паттерн VK-OPS, проверен в бою)

Create `scripts/setup.sh` — pulls secrets from Infisical:

- Usage: `./scripts/setup.sh [env] [.env-file] [settings-file]`
  (default: `prod .env .claude/settings.local.json`; всегда обновляет снапшоты
  `.env.prod` и `.env.dev`).
- Fetch as JSON (`infisical secrets -o json`) and render `KEY='value'` —
  **single quotes** keep `$ # & =`, пробелы, base64, JWT-точки и multiline PEM
  целыми; вложенная кавычка экранируется POSIX-стилем `'\''`.
- **Instance switching**: Infisical CLI держит отдельный логин на каждый self-hosted
  инстанс, но активен ОДИН; перед чтением проверь активный домен и при
  несовпадении — `infisical login --domain=<domain>` (флаг --domain у
  authenticated reads игнорируется!).
- **Guard**: при неудачном fetch НЕ затирать существующий .env (сначала во временный
  файл, потом mv).
- Также зеркалит значения в `.claude/settings.local.json` env-блок (для `${VAR}` в
  .mcp.json).

Create `scripts/secrets-push.sh [--yes]` — обратный поток: локальные `.env.prod`/
`.env.dev` → Infisical **upsert** (никогда не удаляет; dry-run без `--yes`).

Create `scripts/env-audit.sh` — сверка: macstack.json accesses ⇄ Infisical ⇄ `.env*`
(+ деплой-таргеты, если есть): missing required keys = ошибка.

## Step 4 — обязательные commands и правило

`.claude/commands/`:

| Command | Тело |
|---|---|
| `secrets-sync.md` | `Run ./scripts/setup.sh prod .env .claude/settings.local.json и отчитайся` (описание: Pull Infisical → .env/.env.prod/.env.dev) |
| `secrets-push.md` | dry-run по умолчанию, `--yes` для записи; upsert, не удаляет |
| `env-audit.md` | сверка ключей macstack.json ⇄ Infisical ⇄ .env |
| `setup-tokens.md` | первичная настройка: login + первый pull |

`.claude/rules/secrets-env-sync.md` (ставится скиллом `best-practices`): Infisical —
truth; изменил .env → `/secrets-push`; перед деплоем/пушем — `/env-audit`; НИКОГДА
не коммитить `.env*`.

## Step 5 — verify

`/secrets-sync` отрабатывает; `.env.prod` содержит все required-ключи из
macstack.json (пустые — перечислены юзеру); `git status` не показывает `.env*`
кроме `.env.example`; `${VAR}` из `.mcp.json` разрешаются из settings.local.json.

<example>
user: "Подключи Infisical к проекту"
→ .infisical.json (workspaceId нового workspace "nova-website")
→ .env.example из 6 accesses (MAILGUN_* помечены required:false, provided_by:client)
→ scripts/setup.sh + secrets-push.sh + env-audit.sh, commands 4 шт.
→ /secrets-sync → .env.prod: 4/6 заполнены, MAILGUN_* пустые → в needs_from_client
</example>
