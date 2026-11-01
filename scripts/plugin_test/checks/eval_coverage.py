"""eval-coverage: у каждого skill, который вызывает модель, есть набор срабатывания (spec очереди 2 §4.1).

advisory, пока идёт наполнение (Tasks 12–16); blocking — после него (Task 17). Vendored skill
снимаются [skip] "eval-coverage" с причиной. Битый triggers.json — дело eval-files.
"""
from __future__ import annotations

import os

from .. import evalsrc
from ..model import WARN, Finding

CHECK = "eval-coverage"
FIX = "/plugin-creator:evals пишет набор по методике skill-creator; формат — раздел «Кейсы L2» в tests/README.md"


def run(plugin, ctx, manifest):
    out = []
    for skill in evalsrc.skills(plugin.dir):
        if not skill.invocable:
            continue
        if not os.path.isfile(skill.triggers_path):
            out.append(Finding(plugin.name, CHECK, WARN, "skill %s: нет evals/triggers.json" % skill.name,
                               plugin.rel(skill.skill_md), 0, FIX))
            continue
        queries, errors = evalsrc.load_triggers(skill)
        if errors:
            continue
        pos = sum(1 for q in queries if q.should_trigger)
        neg = len(queries) - pos
        if pos < evalsrc.MIN_TRUE or neg < evalsrc.MIN_FALSE:
            out.append(Finding(plugin.name, CHECK, WARN,
                               "skill %s: %d «должен» и %d «не должен» — нужно не меньше %d и %d"
                               % (skill.name, pos, neg, evalsrc.MIN_TRUE, evalsrc.MIN_FALSE),
                               plugin.rel(skill.triggers_path), 0, FIX))
    return out
