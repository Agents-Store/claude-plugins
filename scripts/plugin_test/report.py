"""Отчёт runner-а: статусы проверок, коды выхода, редактирование секретов, вывод.

Всё, что уходит в stdout, JSON-отчёт, снимок или issue, сначала проходит
Redactor: значения env-файла превращаются в ${ИМЯ}, строки, похожие на секрет
по правилам publication gate, скрываются целиком.
"""
from __future__ import annotations

import os
import sys

from . import model
from .model import ADVISORY, BLOCKING, FAIL, INFO, INFRA, LEVELS, SKIPPED, WARN

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
import scrub_check  # noqa: E402

REPORT_VERSION = 1
MIN_SECRET_LEN = 6
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


class Redactor:
    """Значения env-файла → ${ИМЯ}; строки, похожие на секрет, → HIDDEN."""

    def __init__(self, env):
        pairs = [(v, k) for k, v in (env or {}).items()
                 if isinstance(v, str) and len(v) >= MIN_SECRET_LEN]
        self.pairs = sorted(pairs, key=lambda p: -len(p[0]))
        self.rules = [scrub_check.RULES_BY_ID[r] for r in SECRET_RULES]  # KeyError — громкий отказ, не тихое ослабление

    def _secret_line(self, line):
        ctx = {"strict": True, "config_surface": False, "extra_allowed_prefixes": [],
               "in_example_block": False, "published": True}
        return any(any(True for _ in (rule.check(line, ctx) or ())) for rule in self.rules)

    def text(self, s):
        if not s:
            return s
        for value, name in self.pairs:
            s = s.replace(value, "${%s}" % name)
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
            message = f["message"].replace("\n", " ⏎ ")
            out.append("- `%s` %s%s" % (f["check"], "`%s` — " % loc if loc else "", message))
        if level == WARN:
            out += ["", "</details>"]
        out.append("")
    text = "\n".join(out)
    if len(text) > MAX_MARKDOWN:
        text = text[:MAX_MARKDOWN] + "\n\n… сводка обрезана; полный список — в JSON-отчёте прогона."
    return text
