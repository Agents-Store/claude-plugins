"""История оценок L2 — l2-history.jsonl в каталоге состояния сервера, не в git (spec очереди 2 §7).

Строка — один кейс за прогон: {repo, plugin, case, date, commit, model, score, delta, runs, ok}.
Оценки недействительного прогона (лимит, вход посреди прогона) не пишутся вовсе.
"""
from __future__ import annotations

import json
import os
import statistics

FILE = "l2-history.jsonl"
WINDOW = 4        # медиана последних оценок кейса
DROP = 0.25       # регресс — падение на столько и больше
EPS = 1e-9        # 0.9 - 0.65 в двоичной арифметике чуть меньше 0.25


def _path(state_dir):
    return os.path.join(state_dir, FILE)


def scores(state_dir, repo, plugin):
    """{кейс: [оценки в порядке записи]} — только ok-строки этого репозитория и плагина."""
    out = {}
    if not state_dir or not os.path.isfile(_path(state_dir)):
        return out
    with open(_path(state_dir), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict) or e.get("repo") != repo or e.get("plugin") != plugin or e.get("ok") is not True:
                continue
            case, score = e.get("case"), e.get("score")
            if isinstance(case, str) and isinstance(score, (int, float)) and not isinstance(score, bool):
                out.setdefault(case, []).append(float(score))
    return out


def append(state_dir, entries):
    if not state_dir or not entries:
        return
    os.makedirs(state_dir, exist_ok=True)
    with open(_path(state_dir), "a", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")


def regressed(previous, score):
    """Медиана последних WINDOW оценок, если score ниже неё на DROP и больше; иначе None (меньше двух — None)."""
    last = list(previous)[-WINDOW:]
    if len(last) < 2:
        return None
    median = statistics.median(last)
    return float(median) if median - score >= DROP - EPS else None
