"""Общая модель runner-а: уровни находок, статусы проверок, тайм-ауты, контекст."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

FAIL, WARN, INFRA, SKIPPED, INFO = "fail", "warn", "infra", "skipped", "info"
LEVELS = (FAIL, WARN, INFRA, SKIPPED, INFO)
ADVISORY, BLOCKING = "advisory", "blocking"
CI, SERVER = "ci", "server"

# Порядок — порядок запуска. "manifest" — не проверка, а разбор plugin-test.toml;
# его находки идут под этим id, чтобы на них действовали статус и [skip].
CHECK_IDS = (
    "manifest", "skill-links", "skill-snippets", "skill-budget", "mcp-names",
    "mcp-list", "hook-fixtures", "cli-flags", "api-paths", "unit",
    "eval-files", "eval-coverage",
)

# Статус внедрения (spec §6). advisory: fail понижается до warn. blocking: fail
# остаётся fail, под --strict и warn становится fail. Меняется только коммитом.
# manifest и unit — blocking с первого дня: unit наследует блокирующую задачу
# `tests` из scrub.yml, а сломанный манифест молча выключил бы проверки плагина.
# Остальные проверки стали blocking 2026-10-04: итоговый прогон по обоим репозиториям
# дал у них 0 находок fail и warn.
# skill-budget — advisory навсегда: spec §5 называет его «только предупреждение».
STATUS = {
    "manifest": BLOCKING,
    "skill-links": BLOCKING,
    "skill-snippets": BLOCKING,
    "skill-budget": ADVISORY,
    "mcp-names": BLOCKING,
    "mcp-list": BLOCKING,
    "hook-fixtures": BLOCKING,
    "cli-flags": BLOCKING,
    "api-paths": BLOCKING,
    "unit": BLOCKING,
    "eval-files": BLOCKING,       # формат кейсов L2 — с первого дня (spec очереди 2 §4.1)
    "eval-coverage": ADVISORY,    # blocking после наполнения наборов срабатывания (Task 17)
}

# Проверки, которые запускает только явный --check: behavior зовёт модель (spec очереди 2 §2).
# Без --check — DEFAULT_CHECKS: CI, ночной L1 и этап contract в /plugin-creator:test модель не трогают.
OPT_IN_CHECKS = ("behavior",)
DEFAULT_CHECKS = tuple(c for c in CHECK_IDS if c not in OPT_IN_CHECKS)

# Префиксы сообщений behavior: по ним issue раскладывает раздел «L2 Поведение» (spec очереди 2 §7).
L2_MISFIRE = "промах срабатывания"
L2_BELOW = "ниже порога"
L2_REGRESS = "регресс"
L2_UNHELPFUL = "не помогает"
L2_FLAKY = "нестабильно"
L2_NOT_RUN = "L2 не прогнан"
L2_FAILED = "L2 сбой"
L2_STOPPED = "L2 остановлен"   # info: этот плагин остановил L2 на ночь (порог подписки) — l2plan откладывает остальные репозитории

CHECK_TIMEOUT = 120      # потолок одного subprocess проверки, секунды
MCP_START_TIMEOUT = 60   # initialize + tools/list одного MCP-сервера
UNIT_TIMEOUT = 600       # [[unit]] по умолчанию
L2_TIMEOUT = 5400        # один вызов claude plugin eval (все кейсы плагина), секунды


@dataclass(frozen=True)
class Finding:
    plugin: str
    check: str
    level: str
    message: str
    file: str = ""       # путь от корня репозитория
    line: int = 0
    fix: str = ""
    original: str = ""   # уровень до применения статуса, если статус его изменил

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def replace(self, **changes) -> "Finding":
        return dataclasses.replace(self, **changes)


@dataclass
class Context:
    mode: str                        # CI | SERVER
    repo: str                        # абсолютный путь проверяемого репозитория
    catalog: object                  # discover.Catalog по всем известным репозиториям
    env: dict = field(default_factory=dict)   # значения env-файла; {} в режиме ci
    update_snapshots: bool = False
    state_dir: str = ""      # каталог состояния L2 (история оценок); "" — история не ведётся
    deadline: float = 0.0    # unix-время: после него L2 не начинает новый плагин; 0 — без окна
    l2_stop: str = ""        # L2 остановлен в этом прогоне (лимит подписки) — дальше только infra
