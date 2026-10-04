"""Отчёт runner-а: статусы проверок, коды выхода, редактирование секретов, вывод.

Всё, что уходит в stdout, JSON-отчёт, снимок или issue, сначала проходит
Redactor: значения env-файла превращаются в ${ИМЯ}, строки, похожие на секрет
по правилам publication gate, скрываются целиком.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import urllib.parse

from . import model
from .model import ADVISORY, BLOCKING, FAIL, INFO, INFRA, LEVELS, SKIPPED, WARN

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
import scrub_check  # noqa: E402

REPORT_VERSION = 1
MIN_SECRET_LEN = 6
# Значение короче этого порога — слово, а не ключ: подставляется только целым токеном (решение владельца 2026-10-04).
WHOLE_TOKEN_BELOW = 16
SECRET_RULES = ("secret-material", "secret-kv")
HIDDEN = "<строка скрыта: похожа на секрет>"
MAX_MARKDOWN = 60000
LABEL = {FAIL: "FAIL", WARN: "WARN", INFRA: "INFRA", SKIPPED: "SKIP", INFO: "INFO"}
ORDER = {FAIL: 0, INFRA: 1, WARN: 2, SKIPPED: 3, INFO: 4}


def apply_status(findings, strict, status=None):
    status = model.STATUS if status is None else status
    out = []
    for f in findings:
        st = status.get(f.check, ADVISORY)
        if f.level == FAIL and st == ADVISORY:
            f = f.replace(level=WARN, original=FAIL)
        elif f.level == WARN and st == BLOCKING and strict:
            f = f.replace(level=FAIL, original=WARN)
        out.append(f)
    return out


def summarize(findings):
    counts = {lvl: 0 for lvl in LEVELS}
    for f in findings:
        counts[f.level] += 1
    return counts


def exit_code(findings):
    levels = {f.level for f in findings}
    if FAIL in levels:
        return 1
    if levels & {WARN, INFRA}:
        return 2
    return 0


def _hostname(value):
    try:
        return urllib.parse.urlsplit(value).hostname
    except ValueError:  # http://[oops — не URL, значит и хоста нет
        return None


def _path_labels(repo):
    """Абсолютные префиксы, которые не должны попасть в публичный текст: корень репозитория, $HOME, временный каталог."""
    home = os.environ.get("HOME") or os.path.expanduser("~")
    labels = {}
    for path, label in ((repo, "<repo>"), (home, "~"), (tempfile.gettempdir(), "<tmp>")):
        if not path:
            continue
        for variant in (os.path.abspath(path), os.path.realpath(path)):
            variant = variant.rstrip(os.sep)
            if len(variant) > 1:  # корень «/» как префикс превратил бы в метку каждый путь
                labels.setdefault(variant, label)
    return labels


class Redactor:
    """Значения env-файла → ${ИМЯ}; строки, похожие на секрет, → HIDDEN; абсолютные пути → <repo>, ~, <tmp>.

    Значение короче 16 знаков (имя схемы, namespace, регион) заменяется только как целый токен — без соседних
    [A-Za-z0-9_-] (имена MCP-инструментов — такие идентификаторы): иначе list_publication_tables превращается
    в list_${ИМЯ}ation_tables. Значение от 16 знаков заменяется где угодно. Подстановка идёт одним проходом, поэтому вставленное ${ИМЯ} не разбирается повторно.

    Значение-URL регистрирует и свой хост под тем же именем: ошибка сети печатает host:port, а не весь URL.
    Прямое значение env сильнее хоста чужого URL. Путь заменяется только на границе пути: /work/repo-private
    не начинается с /work/repo, а `</root>` в описании инструмента — не путь к $HOME."""

    def __init__(self, env, repo=None):
        names = {}
        items = sorted((env or {}).items())  # одно значение у нескольких имён — берётся первое по порядку
        for name, value in items:
            if isinstance(value, str) and len(value) >= MIN_SECRET_LEN:
                names.setdefault(value, name)
        for name, value in items:
            host = _hostname(value) if isinstance(value, str) else None
            if host and len(host) >= MIN_SECRET_LEN:
                names.setdefault(host, name)
        self.names = names
        alternatives = []
        for value in sorted(names, key=lambda v: (-len(v), v)):
            escaped = re.escape(value)
            if len(value) < WHOLE_TOKEN_BELOW:
                escaped = r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % escaped
            alternatives.append(escaped)
        self.pattern = re.compile("|".join(alternatives)) if alternatives else None
        self.path_labels = _path_labels(repo)
        prefixes = "|".join(re.escape(p) for p in sorted(self.path_labels, key=lambda p: (-len(p), p)))
        self.path_pattern = re.compile(r"(?:(?<![A-Za-z0-9_./<>-])|(?<=://))(?:%s)(?![A-Za-z0-9_-])" % prefixes) \
            if prefixes else None
        self.rules = [scrub_check.RULES_BY_ID[r] for r in SECRET_RULES]  # KeyError — громкий отказ, не тихое ослабление

    def _secret_line(self, line):
        ctx = {"strict": True, "config_surface": False, "extra_allowed_prefixes": [],
               "in_example_block": False, "published": True}
        return any(any(True for _ in (rule.check(line, ctx) or ())) for rule in self.rules)

    def text(self, s):
        if not s:
            return s
        if self.pattern is not None:
            s = self.pattern.sub(lambda m: "${%s}" % self.names[m.group(0)], s)
        if self.path_pattern is not None:
            s = self.path_pattern.sub(lambda m: self.path_labels[m.group(0)], s)
        return "\n".join(HIDDEN if self._secret_line(line) else line for line in s.split("\n"))

    def obj(self, o):
        if isinstance(o, str):
            return self.text(o)
        if isinstance(o, list):
            return [self.obj(x) for x in o]
        if isinstance(o, dict):
            return {k: self.obj(v) for k, v in o.items()}
        return o

    def finding(self, f):
        return f.replace(message=self.text(f.message), fix=self.text(f.fix))


def _location(file, line):
    if not file:
        return ""
    return "%s:%d" % (file, line) if line else file


def render_text(findings, plugins_checked, verbose=False):
    lines = []
    for f in sorted(findings, key=lambda f: (ORDER[f.level], f.plugin, f.check, f.file, f.line)):
        if f.level in (SKIPPED, INFO) and not verbose:
            continue
        loc = _location(f.file, f.line)
        text = "%s %s [%s] %s%s" % (LABEL[f.level], f.plugin, f.check, loc + " — " if loc else "", f.message)
        if f.fix:
            text += " (fix: %s)" % f.fix
        lines.append(text)
    c = summarize(findings)
    lines.append("")
    lines.append("plugin-test: %d plugins, %d fail, %d warn, %d infra, %d skipped"
                 % (plugins_checked, c[FAIL], c[WARN], c[INFRA], c[SKIPPED]))
    return "\n".join(lines)


def build(findings, *, mode, repo, plugins, started, suppressed=0):
    return {
        "version": REPORT_VERSION,
        "mode": mode,
        "repo": os.path.basename(os.path.abspath(repo)),
        "started": started,
        "plugins": list(plugins),
        "summary": {**summarize(findings), "suppressed": suppressed},
        "findings": [f.to_dict() for f in findings],
    }


def render_markdown(report, title="Plugin tests"):
    s = report["summary"]
    out = ["## %s — %s" % (title, report["repo"]), "",
           "Запуск %s, режим `%s`, плагинов: %d." % (report["started"], report["mode"], len(report["plugins"])), "",
           "| fail | warn | infra | skipped |", "|---|---|---|---|",
           "| %d | %d | %d | %d |" % (s.get(FAIL, 0), s.get(WARN, 0), s.get(INFRA, 0), s.get(SKIPPED, 0)), ""]
    for level, heading in ((FAIL, "Провалы"), (INFRA, "Сбои окружения"), (WARN, "Предупреждения")):
        items = [f for f in report["findings"] if f["level"] == level]
        if not items:
            continue
        out.append("### %s (%d)" % (heading, len(items)))
        if level == WARN:
            out.append("<details><summary>показать</summary>")
        current = None
        for f in sorted(items, key=lambda f: (f["plugin"], f["check"], f["file"], f["line"])):
            if f["plugin"] != current:
                current = f["plugin"]
                out += ["", "**%s**" % current, ""]
            loc = _location(f["file"], f["line"])
            message = f["message"].split("\n", 1)[0]  # issue публичный: остальное (stdout проверки, пути) — в JSON и журнале
            out.append("- `%s` %s%s" % (f["check"], "`%s` — " % loc if loc else "", message))
        if level == WARN:
            out += ["", "</details>"]
        out.append("")
    text = "\n".join(out)
    if len(text) > MAX_MARKDOWN:
        text = text[:MAX_MARKDOWN] + "\n\n… сводка обрезана; полный список — в JSON-отчёте прогона."
    return text
