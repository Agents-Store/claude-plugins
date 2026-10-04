# Тесты плагинов — L1 «Контракт»

Runner: `scripts/plugin_test.py`. Он сверяет текст каждого плагина со снимками
реальности, без модели и без ключей. Данные тестов лежат здесь, вне плагинов:
пользователь при установке их не получает, в зеркала они не попадают.

```
tests/plugins/<каталог-плагина>/
  plugin-test.toml          # необязателен: исключения и opt-in
  snapshots/mcp/<server>.tools.json
  snapshots/cli/<tool>.json
  hooks/<case>.json
```

## Запуск

```bash
python3 scripts/plugin_test.py                          # все плагины, режим ci
python3 scripts/plugin_test.py --plugin <name>          # один плагин
python3 scripts/plugin_test.py --changed origin/main --strict   # как в pull request
python3 scripts/plugin_test.py --check skill-snippets   # одна проверка
python3 scripts/plugin_test.py --mode server --env-file <workspace>/.env   # с ключами
python3 scripts/plugin_test.py --repo <workspace>/claude-plugins-private   # private-репо
```

Коды выхода: 0 чисто, 1 есть `fail`, 2 только `warn` / `infra`.

## Проверки

| ID | Что проверяет | Режим |
|---|---|---|
| `skill-links` | относительные ссылки Markdown ведут в файлы плагина; `` `плагин:skill` `` указывает на существующий skill, команду или агента | ci |
| `skill-snippets` | ```` ```json ````, ```` ```yaml ```` разбираются, ```` ```bash ```` проходит `bash -n` (`<плейсхолдер>` заменяется словом) | ci |
| `skill-budget` | всегда-загружаемые токены (`claude plugin details`) и SKILL.md длиннее 500 строк — только предупреждение | ci |
| `mcp-names` | каждое `mcp__plugin_<p>_<server>__<tool>` есть в снимке `tools/list` | ci |
| `mcp-list` | сервер из `.mcp.json` стартует, его `tools/list` совпадает со снимком | stdio со `start = "ci"` — ci; остальное — server |
| `hook-fixtures` | command-hooks на фикстурах: код выхода и поля JSON-ответа | ci |
| `cli-flags` | подкоманды и `--флаги` в bash-блоках есть в снимке `--help` (opt-in) | ci |
| `api-paths` | метод и путь curl-рецептов есть в OpenAPI-спецификации (opt-in) | ci |
| `unit` | собственные тесты плагина из `[[unit]]` | ci |

## `plugin-test.toml`

Значения — только фиктивные (`dummy`, `https://example.com`) или `${VAR}`: файл публичный.

```toml
[mcp.<server>]
start = "ci"            # ci | server (по умолчанию) | never
env = { API_KEY = "dummy" }   # фиктивные значения для старта в CI
snapshot = "names"      # full (по умолчанию) | names — только имена и required:
                        # для self-hosted серверов, чей tools/list несёт данные инстанса

[cli.<tool>]
bin = "<tool>"          # по умолчанию — имя таблицы
version = "1.2.3"       # версия, с которой снят снимок
commands = ["login", "secrets set"]   # чьи флаги снимать

[[api]]
spec = "skills/<skill>/references/openapi.json"   # от каталога плагина
base_vars = { API = "/rest/api/3", API_ROOT = "" } # переменная → префикс пути

[[unit]]
name = "<plugin> unittest"
run = "python3 -m unittest discover -s tests"
cwd = "plugins/<plugin>"   # от корня репозитория; по умолчанию — каталог плагина
needs = ["python3"]
timeout = 600

[budget]
always_on_tokens = 3000    # порог skill-budget; поднимать только с причиной

[skip]
# Точечное исключение — глоб от каталога плагина; причина — в комментарии.
"skill-snippets" = ["skills/legacy/SKILL.md"]   # vendored, правится только синхронизацией
```

## Сниппеты, которые не надо проверять

Блок, перед которым последней непустой строкой стоит `<!-- plugin-test: skip -->`,
пропускается. Пример с комментариями или `...` помечайте ```` ```jsonc ````,
транскрипт сессии — ```` ```console ````.

## Фикстуры hooks

```json
{
  "event": "PreToolUse",
  "matcher": "<буквально как в hooks.json; можно опустить, если у события одна запись>",
  "index": 0,
  "stdin": {"hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_x_y__z", "tool_input": {}},
  "expect": {"exit": 0, "json": {"hookSpecificOutput.permissionDecision": "ask"},
             "stdout_contains": "…", "stdout_empty": true}
}
```

## Снимки

Снимок — файл в репозитории; L1 в CI не ходит за ним в сеть. Обновление:

```bash
python3 scripts/plugin_test.py --mode server --env-file <workspace>/.env \
  --plugin <name> --check mcp-list --check cli-flags --update-snapshots
./scripts/scrub-check.sh --no-lint tests/plugins/<name>
```

Значения из env-файла в снимке заменяются на `${ИМЯ}`; scrub-check после записи обязателен.
