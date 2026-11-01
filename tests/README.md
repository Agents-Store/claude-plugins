# Тесты плагинов — L1 «Контракт» и L2 «Поведение»

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
python3 scripts/plugin_test.py --repo <workspace>/claude-plugins-private \
  --with-repo <workspace>/claude-public-plugins   # зависимость лежит в другом репозитории
python3 scripts/plugin_test.py --plugin <name> --verbose   # печатать и skipped / info
```

Коды выхода: 0 чисто, 1 есть `fail`, 2 только `warn` / `infra`.

`--with-repo` — ещё один репозиторий, где ищутся плагины по имени (ссылки `` `плагин:skill` ``,
имена `mcp__plugin_<p>_…`); соседний репозиторий workspace находится сам. `--verbose` добавляет в вывод
`skipped` и `info` (запись снимка), которые на код выхода не влияют.

## Статусы

Все проверки блокирующие (`blocking`), кроме `skill-budget` (навсегда) и `behavior` (до решения
владельца после калибровки L2): у них `fail` понижается до `warn`.
У блокирующей проверки `fail` остаётся `fail`, а под `--strict` (так запускает CI)
её `warn` тоже становится `fail`. `infra` — сбой окружения (сеть, сервер не стартовал, нет
toolchain, дрейф снимка не закреплённого MCP-сервера) — не блокирует никогда: код выхода 2.
Статусы — константа `STATUS` в `scripts/plugin_test/model.py`, меняются только коммитом.

## Проверки

| ID | Что проверяет | Режим |
|---|---|---|
| `manifest` | `plugin-test.toml` разбирается: синтаксис TOML, известные ключи, типы и значения; ошибка — находка с путём файла, а не traceback | ci |
| `skill-links` | относительные ссылки Markdown ведут в файлы плагина; `` `плагин:skill` `` указывает на существующий skill, команду или агента | ci |
| `skill-snippets` | ```` ```json ````, ```` ```yaml ```` разбираются, ```` ```bash ```` проходит `bash -n` (`<плейсхолдер>` заменяется словом) | ci |
| `skill-budget` | всегда-загружаемые токены (`claude plugin details`) и SKILL.md длиннее 500 строк — только предупреждение | ci |
| `mcp-names` | каждое `mcp__plugin_<p>_<server>__<tool>` есть в снимке `tools/list` | ci |
| `mcp-list` | сервер из `.mcp.json` стартует, его `tools/list` совпадает со снимком | stdio со `start = "ci"` — ci; остальное — server |
| `hook-fixtures` | command-hooks на фикстурах: код выхода и поля JSON-ответа | ci |
| `cli-flags` | подкоманды и `--флаги` в bash-блоках есть в снимке `--help` (opt-in) | ci |
| `api-paths` | метод и путь curl-рецептов есть в OpenAPI-спецификации (opt-in) | ci |
| `unit` | собственные тесты плагина из `[[unit]]` | ci |
| `eval-files` | `skills/<s>/evals/evals.json` и `triggers.json` в формате skill-creator; родной кейс в `tests/plugins/<p>/evals/<case>/` имеет `graders/` | ci |
| `eval-coverage` | у каждого skill, который вызывает модель, есть `triggers.json` с ≥ 5 «должен» и ≥ 5 «не должен» | ci |

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

[behavior]
threshold = 0.8            # порог оценки кейса L2; по умолчанию 0.8

[behavior.case."q-<skill>-<id>"]
threshold = 0.6            # свой порог кейса — только с причиной в комментарии (триаж калибровки)

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

## Кейсы L2

Источник — файлы формата skill-creator рядом со skill; они едут вместе с плагином, правка = новая версия.

```
plugins/<p>/skills/<s>/evals/
  evals.json      # кейсы качества (skill-creator): {skill_name, evals: [{id, prompt, expected_output, files, expectations}]}
  triggers.json   # срабатывание: [{"query": "…", "should_trigger": true}, …]
tests/plugins/<p>/evals/<case>/   # редко: родной кейс claude plugin eval (prompt.md + graders/*.md)
```

- `evals.json`: `id` — число или строка из латиницы, цифр и `_ . -`, уникальный; `prompt` непустой;
  ожидания — `expectations` (строки) **или** `assertions` (объекты с `text`); без них судят по
  `expected_output`. Кейс с непустым `files` в L2 не идёт. Под `--strict` (CI) такой кейс — `fail`: перенеси данные в prompt или оформи родной кейс.
- `triggers.json`: ровно ключи `query` и `should_trigger`; ≥ 5 `true` и ≥ 5 `false`, всего ≤ 20;
  `false` — «почти, но не то»: соседний skill, общие слова, задача соседнего плагина. Skill с
  `disable-model-invocation: true` набора не требует, а `should_trigger: true` для него — ошибка.
  Не меньше 2 из `true` — по-русски (с кириллицей); меньше — `warn` «запросов «должен» по-русски: N» (под `--strict` — `fail`), для skill без вызова моделью предупреждения нет.
- Наборы пишет `/plugin-creator:evals` (методика `skill-creator`).

### Прогон L2

L2 зовёт модель и тратит подписку, поэтому запускается только явно и только на сервере:

```bash
python3 scripts/plugin_test.py --plugin <name> --check behavior --mode server [--state-dir <dir>]
```

- Нужен вход `claude auth login` по подписке claude.ai. `ANTHROPIC_API_KEY` в прогон не попадает никогда.
- L2 меряет skills, не агентов: прогоны идут на копии плагина без `agents/` (агент в песочнице забирает ход у Skill и портит ответ), и `dependencies` в её `plugin.json` тоже нет.
- Срабатывание: 1 прогон на запрос, провал перепроверяется ещё двумя. Промах засчитывается при 2 провалах из 3.
- Качество: 3 прогона с плагином и 3 без, видна дельта. Порог по умолчанию 0.8, свой — в `[behavior]`.
- `--state-dir` ведёт историю `l2-history.jsonl`. Без неё нет находки «регресс».
- `--state-dir` хранит и `l2-usage.json` — последний снимок окон подписки (5 часов и неделя: загрузка, статус, время сброса), он пишется после каждого вызова. Если снимок уже выше порога остановки, а сброс впереди (время сброса неизвестно — снимок моложе 5 часов для окна 5 часов и суток для недели; снимок из будущего или со сбросом дальше длины окна не держит), плагин не начинается: `L2 не прогнан` и `L2 остановлен`, `claude` не вызывается. Битый или чужой файл игнорируется.
- Находки: промах, ниже порога и регресс — `fail` (пока `behavior` advisory, это `warn`). «Не помогает», «нестабильно» и «L2 остановлен» — `info`. «L2 не прогнан» и «L2 сбой» (лимит, окно, вход, сбой вызова, прогон с ошибкой) — `infra`. Ошибка отдельного прогона (API, сеть, 5xx) вердиктом не становится: такой прогон не судится, а оценка кейса считается по чистым.
- Ночью L2 идёт только при `PLUGIN_TEST_L2=1` (по умолчанию выключен), после L1: перенос, изменённые плагины и срез недельной ротации (`scripts/plugin_test_l2plan.py`). Новый плагин не начинается после 07:00 UTC (`PLUGIN_TEST_L2_UNTIL`), идущий вызов может закончиться на 45 минут позже. На лимите подписки останавливается.
- Пороги остановки по подписке — окно 5 часов 0.9 и неделя 0.8 — для волн и ручных прогонов переопределяются в окружении runner-а: `PLUGIN_TEST_L2_FIVE_HOUR_STOP` и `PLUGIN_TEST_L2_SEVEN_DAY_STOP` (число из (0, 1], `1.0` — останавливаться только по настоящему лимиту); ночной прогон их не ставит и живёт на значениях по умолчанию.
- Дешёвый повтор для триажа волн и ручных прогонов — две переменные окружения runner-а: `PLUGIN_TEST_L2_SKILLS=<skill>[,<skill>…]` гонит только срабатывание и качество названных skills плагина (родные кейсы `tests/plugins/<p>/evals` не идут; плагин, у которого нет ни одного из них, не гоняется — одна строка в stderr, неизвестные имена тоже названы в stderr); `PLUGIN_TEST_L2_QUICK=1` (только значение `1`) гонит качество в один прогон без плеча «без плагина» — нет дельты, «не помогает» и «регресса», порог `L2_BELOW` остаётся, оценки качества в `l2-history.jsonl` не пишутся (срабатывание не меняется и пишется как обычно). Итоговая калибровка плагина и ночной прогон не ставят ни ту, ни другую: полные 3+3 прогона, история пишется. Отчёт такого прогона не передавать `plugin_test_l2plan.py record` и `plugin_test_issue.py`: он неполный, а выглядит как полный.
- Живой smoke движка: `PLUGIN_TEST_L2_LIVE=1 python3 -m unittest scripts/tests/test_plugin_test_l2_live.py -v`.
