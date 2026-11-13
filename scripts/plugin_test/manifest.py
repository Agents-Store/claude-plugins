"""tests/plugins/<каталог>/plugin-test.toml — исключения и opt-in (spec §4.3).

Без манифеста runner работает по соглашению. Значения в манифесте — только
фиктивные или ${VAR}: файл публичный.
"""
from __future__ import annotations

import datetime
import os
import tomllib
from dataclasses import dataclass, field

from .model import CHECK_IDS, FAIL, UNIT_TIMEOUT, WARN, Finding

START_VALUES = ("ci", "server", "never")
SNAPSHOT_VALUES = ("full", "names")
TOP_KEYS = {"mcp", "cli", "api", "unit", "skip", "budget", "behavior", "upstream"}
UPSTREAM_KINDS = ("npm", "pypi", "github-release", "github-tag", "docker", "docs")   # за чем следит плагин (refresh)
DEFAULT_ALWAYS_ON = 3000
DEFAULT_THRESHOLD = 0.8
FIX = "исправь plugin-test.toml по образцу из tests/README.md"


@dataclass
class McpSpec:
    start: str = "server"
    env: dict = field(default_factory=dict)
    snapshot: str = "full"     # names — только имена и required (данные инстанса не попадают в репозиторий)


@dataclass
class CliSpec:
    bin: str
    version: str = ""
    commands: list = field(default_factory=list)


@dataclass
class ApiSpec:
    spec: str                                        # путь от каталога плагина
    base_vars: dict = field(default_factory=dict)    # имя переменной → префикс пути


@dataclass
class UnitSpec:
    run: str
    cwd: str = ""                 # от корня репозитория; "" — каталог плагина
    needs: list = field(default_factory=list)
    timeout: int = UNIT_TIMEOUT
    name: str = ""


@dataclass
class UpstreamSource:
    kind: str                   # UPSTREAM_KINDS
    id: str = ""                # пакет npm/PyPI, owner/repo на GitHub, образ Docker
    url: str = ""               # страница документации или changelog (kind = docs)
    pinned: str = ""            # версия, под которую плагин сейчас выверен (пишет /plugin-creator:refresh)


@dataclass
class Manifest:
    mcp: dict = field(default_factory=dict)
    cli: dict = field(default_factory=dict)
    api: list = field(default_factory=list)
    unit: list = field(default_factory=list)
    skip: dict = field(default_factory=dict)
    always_on_tokens: int = DEFAULT_ALWAYS_ON
    threshold: float = DEFAULT_THRESHOLD                 # порог оценки кейса L2 (spec очереди 2 §5.4)
    case_thresholds: dict = field(default_factory=dict)  # имя кейса → свой порог (с причиной в комментарии)
    upstream_sources: list = field(default_factory=list)     # UpstreamSource — что сверяет plugin_upstream.py
    upstream_reviewed: "datetime.date | None" = None          # последнее полное обновление (квартальная ротация)
    upstream_skip_paths: list = field(default_factory=list)  # маски vendored-путей: refresh их не правит

    def mcp_spec(self, server) -> McpSpec:
        return self.mcp.get(server) or McpSpec()

    def threshold_for(self, case) -> float:
        return self.case_thresholds.get(case, self.threshold)


def path_of(plugin):
    return os.path.join(plugin.tests_dir, "plugin-test.toml")


def load(plugin):
    """(Manifest, [Finding]). Нет файла — пустой манифест и ни одной находки."""
    path = path_of(plugin)
    if not os.path.isfile(path):
        return Manifest(), []
    rel = plugin.rel(path)
    findings = []

    def bad(message, level=FAIL):
        findings.append(Finding(plugin.name, "manifest", level, message, rel, 0, FIX))

    # ValueError покрывает TOMLDecodeError и UnicodeDecodeError, а ещё слишком длинное целое
    # (лимит int() в 4300 цифр); RecursionError — очень глубокая вложенность; OSError — файл не читается.
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except (ValueError, RecursionError, OSError) as exc:
        if isinstance(exc, OSError):    # str(OSError) несёт абсолютный путь — в находку он не попадает
            bad("файл не читается: %s" % (exc.strerror or type(exc).__name__))
        else:
            bad("TOML не разбирается: %s" % exc)
        return Manifest(), findings

    m = Manifest()
    for key in sorted(set(data) - TOP_KEYS):
        bad("неизвестный ключ верхнего уровня %r" % key, WARN)
    _mcp(_section(data, "mcp", dict, "должна быть таблицей серверов", bad), m, bad)
    _cli(_section(data, "cli", dict, "должна быть таблицей утилит", bad), m, bad)
    _api(_section(data, "api", (dict, list), "должна быть таблицей или массивом таблиц ([[api]])", bad), m, bad)
    _unit(_section(data, "unit", list, "должен быть массивом таблиц ([[unit]])", bad), m, bad)
    _skip(_section(data, "skip", dict, "должна быть таблицей «проверка = [маски]»", bad), m, bad)
    _budget(_section(data, "budget", dict, "должна быть таблицей", bad), m, bad)
    _behavior(_section(data, "behavior", dict, "должна быть таблицей", bad), m, bad)
    _upstream(_section(data, "upstream", dict, "должна быть таблицей", bad), m, bad)
    return m, findings


def _section(data, key, kinds, expected, bad):
    """data[key], если он нужного типа; иначе одна находка FAIL и None (секция пропускается).

    TOML не имеет null, поэтому None — это «ключа нет»; 0, "", false и [] — уже неверный тип.
    """
    raw = data.get(key)
    if raw is None:
        return None
    if not isinstance(raw, kinds):
        bad("[%s] %s" % (key, expected))
        return None
    return raw


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _budget(raw, m, bad):
    if raw is None or "always_on_tokens" not in raw:
        return
    if _is_int(raw["always_on_tokens"]):
        m.always_on_tokens = raw["always_on_tokens"]
    else:
        bad("[budget] always_on_tokens должно быть целым числом")


def _mcp(raw, m, bad):
    for server, spec in (raw or {}).items():
        if not isinstance(spec, dict):
            bad("[mcp.%s] должна быть таблицей" % server)
            continue
        start = spec.get("start", "server")
        if start not in START_VALUES:
            bad("[mcp.%s] start=%r, ожидалось одно из: %s" % (server, start, ", ".join(START_VALUES)))
            start = "server"
        env = spec.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
            bad("[mcp.%s] env должна быть таблицей строк" % server)
            env = {}
        snapshot = spec.get("snapshot", "full")
        if snapshot not in SNAPSHOT_VALUES:
            bad("[mcp.%s] snapshot=%r, ожидалось full или names" % (server, snapshot))
            snapshot = "full"
        m.mcp[server] = McpSpec(start=start, env=dict(env), snapshot=snapshot)


def _cli(raw, m, bad):
    for tool, spec in (raw or {}).items():
        commands = spec.get("commands", []) if isinstance(spec, dict) else None
        if not isinstance(commands, list) or not all(isinstance(c, str) for c in commands):
            bad("[cli.%s] нужна таблица с commands = [строки]" % tool)
            continue
        m.cli[tool] = CliSpec(bin=str(spec.get("bin", tool)), version=str(spec.get("version", "")),
                              commands=list(commands))


def _api(raw, m, bad):
    for spec in [raw] if isinstance(raw, dict) else (raw or []):
        if not isinstance(spec, dict) or not isinstance(spec.get("spec"), str):
            bad("[api] нужен ключ spec — путь к OpenAPI от каталога плагина")
            continue
        base = spec.get("base_vars", {})
        if isinstance(base, list) and all(isinstance(v, str) for v in base):
            base = {v: "" for v in base}
        if not isinstance(base, dict) or not all(isinstance(v, str) for v in base.values()):
            bad("[api] base_vars — список имён или таблица имя → префикс пути")
            continue
        m.api.append(ApiSpec(spec=spec["spec"], base_vars=dict(base)))


def _unit(raw, m, bad):
    for spec in raw or []:
        if not isinstance(spec, dict) or not isinstance(spec.get("run"), str):
            bad("[[unit]] нужен ключ run — команда для bash -c")
            continue
        timeout = spec.get("timeout", UNIT_TIMEOUT)
        needs = spec.get("needs", [])
        if not _is_int(timeout) or not isinstance(needs, list):
            bad("[[unit]] %r: timeout — целое число секунд, needs — список" % spec["run"])
            continue
        m.unit.append(UnitSpec(run=spec["run"], cwd=str(spec.get("cwd", "")), needs=[str(n) for n in needs],
                               timeout=timeout, name=str(spec.get("name", ""))))


def _skip(raw, m, bad):
    for check, globs in (raw or {}).items():
        if check not in CHECK_IDS:
            bad("[skip] неизвестная проверка %r" % check, WARN)
            continue
        globs = globs if isinstance(globs, list) else [globs]
        m.skip[check] = [g for g in globs if isinstance(g, str)]


def _is_score(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _behavior(raw, m, bad):
    if raw is None:
        return
    for key in sorted(set(raw) - {"threshold", "case"}):
        bad("[behavior] неизвестный ключ %r" % key, WARN)
    if "threshold" in raw:
        if _is_score(raw["threshold"]):
            m.threshold = float(raw["threshold"])
        else:
            bad("[behavior] threshold — число от 0 до 1")
    cases = raw.get("case", {})
    if not isinstance(cases, dict):
        bad("[behavior.case] должна быть таблицей: [behavior.case.\"<имя кейса>\"] threshold = …")
        return
    for name, spec in sorted(cases.items()):
        value = spec.get("threshold") if isinstance(spec, dict) else None
        if not _is_score(value):
            bad("[behavior.case.%s] нужен threshold — число от 0 до 1" % name)
            continue
        m.case_thresholds[name] = float(value)


SOURCE_KEYS = {"kind", "id", "url", "pinned"}


def _upstream(raw, m, bad):
    if raw is None:
        return
    for key in sorted(set(raw) - {"reviewed", "skip_paths", "source"}):
        bad("[upstream] неизвестный ключ %r" % key, WARN)
    if "reviewed" in raw:
        value = raw["reviewed"]
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            m.upstream_reviewed = value
        else:
            bad("[upstream] reviewed — дата TOML без кавычек: reviewed = 2026-11-20")
    paths = raw.get("skip_paths", [])
    if isinstance(paths, list) and all(isinstance(p, str) for p in paths):
        m.upstream_skip_paths = list(paths)
    else:
        bad("[upstream] skip_paths — массив строк-масок")
    sources = raw.get("source", [])
    if not isinstance(sources, list):
        bad("[upstream] source — массив таблиц ([[upstream.source]])")
        return
    for i, spec in enumerate(sources):
        where = "[[upstream.source]] #%d" % (i + 1)
        if not isinstance(spec, dict):
            bad("%s должен быть таблицей" % where)
            continue
        extra = sorted(set(spec) - SOURCE_KEYS)
        if extra:
            bad("%s: неизвестный ключ %r (допустимы kind, id, url, pinned)" % (where, extra[0]))
            continue
        kind = spec.get("kind")
        if kind not in UPSTREAM_KINDS:
            bad("%s: kind — один из %s" % (where, ", ".join(UPSTREAM_KINDS)))
            continue
        if any(not isinstance(spec.get(k, ""), str) for k in ("id", "url", "pinned")):
            bad("%s: id, url и pinned — строки" % where)
            continue
        if kind == "docs" and not spec.get("url"):
            bad("%s: kind = \"docs\" требует url" % where)
            continue
        if kind != "docs" and not spec.get("id"):
            bad("%s: kind = \"%s\" требует id" % (where, kind))
            continue
        m.upstream_sources.append(UpstreamSource(kind, id=spec.get("id", ""), url=spec.get("url", ""),
                                                 pinned=spec.get("pinned", "")))
