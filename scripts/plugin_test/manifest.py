"""tests/plugins/<каталог>/plugin-test.toml — исключения и opt-in (spec §4.3).

Без манифеста runner работает по соглашению. Значения в манифесте — только
фиктивные или ${VAR}: файл публичный.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field

from .model import CHECK_IDS, FAIL, UNIT_TIMEOUT, WARN, Finding

START_VALUES = ("ci", "server", "never")
SNAPSHOT_VALUES = ("full", "names")
TOP_KEYS = {"mcp", "cli", "api", "unit", "skip", "budget"}
DEFAULT_ALWAYS_ON = 3000
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
class Manifest:
    mcp: dict = field(default_factory=dict)
    cli: dict = field(default_factory=dict)
    api: list = field(default_factory=list)
    unit: list = field(default_factory=list)
    skip: dict = field(default_factory=dict)
    always_on_tokens: int = DEFAULT_ALWAYS_ON

    def mcp_spec(self, server) -> McpSpec:
        return self.mcp.get(server) or McpSpec()


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

    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        bad("TOML не разбирается: %s" % exc)
        return Manifest(), findings

    m = Manifest()
    for key in sorted(set(data) - TOP_KEYS):
        bad("неизвестный ключ верхнего уровня %r" % key, WARN)
    _mcp(data.get("mcp"), m, bad)
    _cli(data.get("cli"), m, bad)
    _api(data.get("api"), m, bad)
    _unit(data.get("unit"), m, bad)
    _skip(data.get("skip"), m, bad)
    budget = data.get("budget") or {}
    if isinstance(budget, dict) and "always_on_tokens" in budget:
        if isinstance(budget["always_on_tokens"], int):
            m.always_on_tokens = budget["always_on_tokens"]
        else:
            bad("[budget] always_on_tokens должно быть целым числом")
    return m, findings


def _mcp(raw, m, bad):
    for server, spec in (raw or {}).items():
        if not isinstance(spec, dict):
            bad("[mcp.%s] должна быть таблицей" % server)
            continue
        start = spec.get("start", "server")
        if start not in START_VALUES:
            bad("[mcp.%s] start=%r, ожидалось одно из: %s" % (server, start, ", ".join(START_VALUES)))
            start = "server"
        env = spec.get("env") or {}
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
        if not isinstance(timeout, int) or not isinstance(needs, list):
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
