"""eval-files: формат файлов кейсов L2 — evals.json, triggers.json, родной набор (spec очереди 2 §4.1).

Без модели и сети, в CI. Битый файл — fail: проверка behavior его не прогонит, а skill-creator
и /plugin-creator:evals не прочитают.
Набор срабатывания без двух русских запросов «должен» — warn (правило наборов; не относится к битому набору
и к skill с disable-model-invocation).
"""
from __future__ import annotations

import os
import re

from .. import evalsrc
from ..model import FAIL, WARN, Finding

CHECK = "eval-files"
FIX = "формат — раздел «Кейсы L2» в tests/README.md; наборы пишет /plugin-creator:evals"
FIX_RU = "добавь русский запрос «должен» (правило наборов, /plugin-creator:evals)"
MIN_RU_TRUE = 2           # русских запросов «должен» в наборе: правило наборов, волны удаляли их незаметно
RE_CYRILLIC = re.compile("[А-Яа-яЁё]")


def run(plugin, ctx, manifest):
    out = []
    for skill in evalsrc.skills(plugin.dir):
        if os.path.isfile(skill.evals_path):
            cases, errors = evalsrc.load_quality(skill)
            rel = plugin.rel(skill.evals_path)
            out += [Finding(plugin.name, CHECK, FAIL, e, rel, 0, FIX) for e in errors]
            with_files = [c.id for c in cases if c.has_files]
            if with_files:
                out.append(Finding(plugin.name, CHECK, WARN,
                                   "кейсы с files не идут в L2 (входные файлы не подкладываются): %s"
                                   % ", ".join(with_files), rel, 0,
                                   "вставь нужные данные в prompt или оформи родной кейс в tests/plugins/<p>/evals/"))
        if os.path.isfile(skill.triggers_path):
            queries, errors = evalsrc.load_triggers(skill)
            rel = plugin.rel(skill.triggers_path)
            out += [Finding(plugin.name, CHECK, FAIL, e, rel, 0, FIX) for e in errors]
            positives = [q for q in queries if q.should_trigger]
            russian = sum(1 for q in positives if RE_CYRILLIC.search(q.query))
            if not errors and skill.invocable and positives and russian < MIN_RU_TRUE:
                out.append(Finding(plugin.name, CHECK, WARN, "запросов «должен» по-русски: %d — нужно не меньше %d"
                                   % (russian, MIN_RU_TRUE), rel, 0, FIX_RU))
    _, native_errors = evalsrc.native_cases(plugin)
    for path, message in native_errors:
        out.append(Finding(plugin.name, CHECK, FAIL, message, plugin.rel(path), 0,
                           "положи graders/<имя>.md (формат — документация claude plugin eval)"))
    return out
