"""Выбор плагинов для ночной фазы L2 и её состояние (spec очереди 2 §6.1).

Порядок: перенос с прошлой ночи → изменённые с commit-а прошлого L2 → срез ротации дня недели.
Каталог (плагины с кейсами) делится на SLICES срезов примерно равного веса — жадно и детерминированно,
так что за неделю каждый плагин проходит хотя бы раз. Состояние — l2-state.json в каталоге состояния.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import tempfile

from . import discover, evalsrc
from .model import L2_NOT_RUN, L2_STOPPED

STATE = "l2-state.json"
SLICES = 7
TRIGGER_WEIGHT = 1     # прогон кейса срабатывания (повтор — только для провалов)
QUALITY_WEIGHT = 6     # 3 прогона × 2 плеча


def weight(plugin):
    w = 0
    for skill in evalsrc.skills(plugin.dir):
        if os.path.isfile(skill.triggers_path):
            w += len(evalsrc.load_triggers(skill)[0]) * TRIGGER_WEIGHT
        if os.path.isfile(skill.evals_path):
            w += sum(1 for c in evalsrc.load_quality(skill)[0] if not c.has_files) * QUALITY_WEIGHT
    return w + len(evalsrc.native_cases(plugin)[0]) * QUALITY_WEIGHT


def slices(weights, n=SLICES):
    buckets, loads = [[] for _ in range(n)], [0] * n
    for name in sorted(weights, key=lambda k: (-weights[k], k)):
        i = min(range(n), key=lambda j: (loads[j], j))
        buckets[i].append(name)
        loads[i] += weights[name]
    return [sorted(b) for b in buckets]


def _load(state_dir):
    try:
        with open(os.path.join(state_dir, STATE), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict) or not isinstance(data.get("repos"), dict):
        data = {"version": 1, "repos": {}}
    return data


def _save(state_dir, data):
    os.makedirs(state_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".l2-state-", dir=state_dir)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, os.path.join(state_dir, STATE))


def _key(repo):
    return os.path.basename(os.path.abspath(repo))


def _head(repo):
    try:
        done = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def select(repo, state_dir, weekday):
    """(имена плагинов на эту ночь по порядку, заметки)."""
    plugins = discover.discover(repo)
    weights = {p.name: weight(p) for p in plugins}
    known = {name for name, w in weights.items() if w > 0}
    st = _load(state_dir)["repos"].get(_key(repo), {})
    carry = [n for n in st.get("carry") or [] if n in known]
    changed, notes = [], []
    if st.get("commit"):
        try:
            # triggers=(): правка runner-а — не повод гонять модель по всему каталогу (L1 перепроверяет всё сам)
            changed = [p.name for p in discover.changed(repo, st["commit"], plugins, triggers=()) if p.name in known]
        except discover.ChangedError as exc:
            notes.append("изменённые не посчитаны: %s" % exc)
    rotation = slices({n: weights[n] for n in known})[weekday % SLICES]
    out = []
    for name in carry + changed + rotation:
        if name not in out:
            out.append(name)
    return out, notes


def record(repo, state_dir, report):
    """Commit этой ночи и перенос (плагины с L2_NOT_RUN). → причина остановки L2 (L2_STOPPED, иначе L2_NOT_RUN) или ""."""
    l2 = [f for f in report.get("findings") or [] if f.get("check") == "behavior"]
    not_run = [f for f in l2 if f.get("level") == "infra" and str(f.get("message", "")).startswith(L2_NOT_RUN)]
    stopped = [f for f in l2 if str(f.get("message", "")).startswith(L2_STOPPED)]
    data = _load(state_dir)
    data["repos"][_key(repo)] = {
        "commit": _head(repo),
        "carry": sorted({f["plugin"] for f in not_run}),
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _save(state_dir, data)
    if stopped:
        return str(stopped[0]["message"])[len(L2_STOPPED):].lstrip(": ")
    if not_run:
        return str(not_run[0]["message"])[len(L2_NOT_RUN):].lstrip(": ")
    return ""


def defer(repo, state_dir, names):
    data = _load(state_dir)
    st = data["repos"].setdefault(_key(repo), {})
    st["carry"] = sorted(set(st.get("carry") or []) | set(names))
    _save(state_dir, data)
