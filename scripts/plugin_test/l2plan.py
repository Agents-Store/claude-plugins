"""Выбор плагинов для ночной фазы L2 и её состояние (spec очереди 2 §6.1).

Порядок: перенос с прошлой ночи → изменённые с commit-а прошлого L2 → срез ротации дня недели.
Каталог (плагины с кейсами) делится на SLICES срезов примерно равного веса — жадно и детерминированно,
так что за неделю каждый плагин проходит хотя бы раз. Состояние — l2-state.json в каталоге состояния,
последний вердикт L2 по каждому плагину репозитория — l2-latest-<репозиторий>.json рядом с ним.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import tempfile

from . import discover, evalsrc
from .model import L2_FAILED, L2_NOT_RUN, L2_STOPPED, LEVELS
from .report import REPORT_VERSION

STATE = "l2-state.json"
SLICES = 7
MAX_FAILED_CARRY = 2   # плагин с «L2 сбой» переносится на следующую ночь, пока не упал так подряд больше стольких ночей
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


def _sane(entry):
    """Запись репозитория в состоянии: чужие/битые значения → пустые (файл правят руками и другие версии)."""
    if not isinstance(entry, dict):
        return {}
    if not isinstance(entry.get("commit"), str):
        entry.pop("commit", None)
    if "carry" in entry:
        entry["carry"] = [n for n in entry["carry"] if isinstance(n, str)] if isinstance(entry["carry"], list) else []
    if "failed" in entry:
        failed = entry["failed"] if isinstance(entry["failed"], dict) else {}
        entry["failed"] = {n: c for n, c in failed.items() if isinstance(c, int) and not isinstance(c, bool)}
    return entry


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _load(state_dir):
    data = _read_json(os.path.join(state_dir, STATE))
    if not isinstance(data, dict) or not isinstance(data.get("repos"), dict):
        data = {"version": 1, "repos": {}}
    data["repos"] = {key: _sane(entry) for key, entry in data["repos"].items()}
    return data


def _write_json(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".l2-state-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _save(state_dir, data):
    _write_json(os.path.join(state_dir, STATE), data)


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


def latest_path(state_dir, repo):
    return os.path.join(state_dir, "l2-latest-%s.json" % _key(repo))


def _is(finding, *prefixes):
    return str(finding.get("message", "")).startswith(prefixes)


def _only_notes(findings):
    """Плагин ночью не прогонялся: у него только «L2 не прогнан» / «L2 остановлен»."""
    return bool(findings) and all(_is(f, L2_NOT_RUN, L2_STOPPED) for f in findings)


def _behavior(findings):
    return [f for f in findings or [] if isinstance(f, dict) and f.get("check") == "behavior"
            and isinstance(f.get("plugin"), str)]


def _by_plugin(findings):
    out = {}
    for f in findings:
        out.setdefault(f["plugin"], []).append(f)
    return out


def _latest(repo, state_dir, report, catalog, named, tonight):
    """l2-latest-<репозиторий>.json: последний вердикт L2 по каждому плагину (spec очереди 2 §7), в форме отчёта."""
    prev = _read_json(latest_path(state_dir, repo))
    merged = _by_plugin(_behavior(prev.get("findings") if isinstance(prev, dict) else None))
    for name in named | set(tonight):
        found = tonight.get(name, [])
        if _only_notes(found):    # не прогонялся: прежний вердикт остаётся, старые заметки заменяются новыми
            merged[name] = [f for f in merged.get(name, []) if not _is(f, L2_NOT_RUN, L2_STOPPED)] + found
        else:
            merged[name] = found
    findings = [f for name in sorted(merged) if name in catalog for f in merged[name]]
    counts = {lvl: 0 for lvl in LEVELS}
    for f in findings:
        if f.get("level") in counts:
            counts[f["level"]] += 1
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_json(latest_path(state_dir, repo), {
        "version": report.get("version", REPORT_VERSION),
        "mode": report.get("mode", "server"),
        "repo": report.get("repo") or _key(repo),
        "started": report.get("started") or now,
        "plugins": sorted({f["plugin"] for f in findings}),
        "summary": {**counts, "suppressed": 0},
        "findings": findings,
    })


def record(repo, state_dir, report):
    """Итог ночи: commit, перенос и последний вердикт по плагинам. → причина остановки L2 или "".

    Перенос: плагины с «L2 не прогнан» и плагины с «L2 сбой» — пока тот же плагин не падал подряд больше
    MAX_FAILED_CARRY ночей; прогнанный без сбоя плагин счётчик обнуляет. Остановка на всю ночь — только
    находка «L2 остановлен» (окно ночи общее для репозиториев и остановки не требует)."""
    catalog = {p.name for p in discover.discover(repo)}
    l2 = _behavior(report.get("findings"))
    tonight = _by_plugin(l2)
    named = {n for n in report.get("plugins") or [] if isinstance(n, str)}
    ran = {n for n in named | set(tonight) if not _only_notes(tonight.get(n, []))}
    failed_now = {n for n in ran & catalog if any(f.get("level") == "infra" and _is(f, L2_FAILED)
                                                 for f in tonight.get(n, []))}
    not_run = {f["plugin"] for f in l2 if f.get("level") == "infra" and _is(f, L2_NOT_RUN)}
    stopped = [f for f in l2 if _is(f, L2_STOPPED)]

    data = _load(state_dir)
    prev = data["repos"].get(_key(repo), {})
    old_failed = prev.get("failed", {})
    failed = {n: c for n, c in old_failed.items() if n in catalog and n not in ran}
    for name in failed_now:
        failed[name] = old_failed.get(name, 0) + 1
    data["repos"][_key(repo)] = {
        "commit": _head(repo) or prev.get("commit", ""),
        "carry": sorted(not_run | {n for n in failed_now if failed[n] <= MAX_FAILED_CARRY}),
        "failed": failed,
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _save(state_dir, data)
    _latest(repo, state_dir, report, catalog, named, tonight)
    if stopped:
        return str(stopped[0]["message"])[len(L2_STOPPED):].lstrip(": ")
    return ""


def defer(repo, state_dir, names):
    data = _load(state_dir)
    st = data["repos"].setdefault(_key(repo), {})
    st["carry"] = sorted(set(st.get("carry") or []) | set(names))
    _save(state_dir, data)
