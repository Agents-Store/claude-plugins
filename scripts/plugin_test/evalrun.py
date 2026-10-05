"""Запуск `claude plugin eval` за счёт подписки и разбор результата (spec очереди 2 §6.3, §6.4, §3a).

Окружение — только allowlist: ANTHROPIC_API_KEY важнее входа по подписке, и CLI передаёт большинство
ANTHROPIC_* в прогон. К allowlist всегда добавляется ENABLE_CLAUDEAI_MCP_SERVERS=false: коннекторы аккаунта
claude.ai иначе грузятся в прогон и перехватывают единственный ход срабатывания. Признаки лимита — события
rate_limit_event в трейсах (--keep-temp); каталоги <tmp>/claude-eval-* удаляются сразу после чтения, только по
точному шаблону. Пороги остановки по окнам подписки — по умолчанию 0.9 и 0.8; волны и ручные прогоны
переопределяют их переменными PLUGIN_TEST_L2_FIVE_HOUR_STOP и PLUGIN_TEST_L2_SEVEN_DAY_STOP.
Вывод `claude auth status` несёт email и организацию — он не печатается и не пишется никуда.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

from .model import L2_TIMEOUT
from .proc import run_group

MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "claude-haiku-4-5-20251001"
CONCURRENCY = 4
FIVE_HOUR_STOP = 0.9     # окно 5 часов: дальше L2 съест дневную работу
SEVEN_DAY_STOP = 0.8     # неделя: запас для дневной работы владельца
FIVE_HOUR_VAR = "PLUGIN_TEST_L2_FIVE_HOUR_STOP"    # свои пороги волн и ручных прогонов; ночной прогон их не ставит
SEVEN_DAY_VAR = "PLUGIN_TEST_L2_SEVEN_DAY_STOP"
AUTH_TIMEOUT = 60
KEEP_ENV = ("PATH", "HOME", "LANG", "USER", "LOGNAME", "TMPDIR")
OK_STATUSES = {"allowed", "allowed_warning"}
RE_LIMIT = re.compile(r"rate.?limit|usage.?limit|\b429\b|limit (?:reached|exceeded)|out of (?:usage|credits)", re.I)
RESULT = "aggregate-result.json"
RE_IDENT = re.compile(r"[A-Za-z0-9_.-]{1,40}")
MAX_UTILIZATION = 100.0


class EvalError(Exception):
    """Вызов не дал результата: тайм-аут, нет CLI, нет или битый aggregate-result.json."""


@dataclass
class RunResult:
    data: dict
    returncode: int
    stop: str = ""            # причина остановить L2 на эту ночь; "" — продолжать
    invalid: bool = False     # оценкам этого вызова не верить: лимит, вход, прерывание посреди прогона
    usage: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)


def environment():
    env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    env.setdefault("LANG", "C.UTF-8")
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"     # значение родителя не берётся никогда
    return env


def _stop_threshold(var, default):
    """Порог из переменной окружения самого runner-а: число из (0, 1]; иначе default и строка в журнал
    (имя переменной, не значение). 1.0 — останавливаться только по настоящему лимиту."""
    raw = os.environ.get(var)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        value = math.nan
    if 0.0 < value <= 1.0:
        return value
    _debug("%s: нужно число из (0, 1], взят порог по умолчанию %s" % (var, default))
    return default


def five_hour_stop():
    return _stop_threshold(FIVE_HOUR_VAR, FIVE_HOUR_STOP)


def seven_day_stop():
    return _stop_threshold(SEVEN_DAY_VAR, SEVEN_DAY_STOP)


def preflight(claude, env):
    """"" — вход по подписке claude.ai есть; иначе причина (без данных аккаунта)."""
    try:
        done = run_group([claude, "auth", "status", "--json"], env=env, cwd=env.get("HOME") or "/",
                         timeout=AUTH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return "claude auth status не ответил за %d с" % AUTH_TIMEOUT
    except OSError as exc:
        return "claude не запускается: %s" % (exc.strerror or type(exc).__name__)
    try:
        data = json.loads(done.stdout)
    except ValueError:
        return "claude auth status: не JSON (код %d)" % done.returncode
    if not isinstance(data, dict) or data.get("loggedIn") is not True:
        return "нет входа в claude — на сервере: claude auth login"
    method = data.get("authMethod")
    if method != "claude.ai":
        return "вход не по подписке claude.ai (authMethod=%s): L2 платит только подписка" % _ident(method)
    return ""


def command(claude, copy_dir, eval_dir, out_dir, *, ablation, runs=None):
    args = [claude, "plugin", "eval", copy_dir, "--eval-dir", eval_dir, "--trust-plugin", "--no-publish",
            "--mocks", "record", "--keep-temp", "--threshold", "0", "--ablation", ablation,
            "--concurrency", str(CONCURRENCY), "--model", MODEL, "--judge-model", JUDGE_MODEL,
            "--output-dir", out_dir]
    if runs is not None:
        args += ["--runs", str(runs)]
    return args


def _tail(text):
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    return lines[-1][:200] if lines else ""


def _debug(text):
    """Сырая деталь — одной строкой в stderr (журнал ночного прогона), не в сообщение находки: issue публичный."""
    print("[evalrun] %s" % " ".join(str(text).split())[:400], file=sys.stderr)


def _ident(value, default="не указан"):
    """Короткий идентификатор из ответа CLI (authMethod, partialReason, status); иной текст в сообщения не попадает."""
    return value if isinstance(value, str) and RE_IDENT.fullmatch(value) else default


def run(claude, copy_dir, eval_dir, out_dir, *, ablation, runs=None, env, timeout=L2_TIMEOUT):
    os.makedirs(out_dir, exist_ok=True)
    try:
        os.remove(os.path.join(out_dir, RESULT))   # результат прошлого прохода не должен сойти за свежий
    except FileNotFoundError:
        pass
    args = command(claude, copy_dir, eval_dir, out_dir, ablation=ablation, runs=runs)
    try:
        done = run_group(args, env=env, cwd=out_dir, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise EvalError("claude plugin eval не завершился за %d с" % timeout) from None
    except OSError as exc:
        _debug("claude не запускается: %s" % (exc.strerror or type(exc).__name__))
        raise EvalError("claude не запускается") from None
    try:
        with open(os.path.join(out_dir, RESULT), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        _debug("нет результата (код %d): %s" % (done.returncode, _tail(done.stderr) or _tail(done.stdout) or "без вывода"))
        raise EvalError("claude plugin eval: нет результата (код %d)" % done.returncode) from None
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise EvalError("claude plugin eval: результат без cases (код %d)" % done.returncode)
    result = RunResult(data=data, returncode=done.returncode)
    if done.returncode == 1:
        _debug("код 1: %s" % (_tail(done.stderr) or "без stderr"))
        result.problems.append("claude plugin eval, код 1")
    try:
        usage, status, overage = _scan_traces(data)
        result.usage = usage
        result.stop, result.invalid = _verdict(data, done.returncode, usage, status, overage)
    finally:
        _cleanup(data)
    return result


def _runs(data):
    for case in data.get("cases") or []:
        if not isinstance(case, dict):
            continue
        arms = case.get("arms") if isinstance(case.get("arms"), dict) else {}
        for arm in ("with", "without"):
            for r in arms.get(arm) or []:
                if isinstance(r, dict):
                    yield r


def _temp_root(path):
    """<tmp>/claude-eval-XXXX для tracePath внутри него; иначе None."""
    if not isinstance(path, str):
        return None
    base = os.path.realpath(tempfile.gettempdir())
    m = re.match(r"^(%s/claude-eval-[A-Za-z0-9_-]+)/" % re.escape(base), os.path.realpath(path))
    return m.group(1) if m else None


def _scan_traces(data):
    usage = {"five_hour": 0.0, "seven_day": 0.0}
    status, overage = "", False
    for r in _runs(data):
        path = r.get("tracePath")
        if not _temp_root(path):
            continue
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"rate_limit_event"' not in line:
                    continue
                try:
                    info = json.loads(line).get("rate_limit_info")
                except (ValueError, AttributeError):
                    continue
                if not isinstance(info, dict):
                    continue
                if isinstance(info.get("status"), str) and info["status"] and info["status"] not in OK_STATUSES:
                    status = info["status"]
                if info.get("isUsingOverage") is True:
                    overage = True
                windows = info.get("unifiedWindows")
                for window, value in (windows.items() if isinstance(windows, dict) else ()):
                    u = value.get("utilization") if isinstance(value, dict) else None
                    if window in usage and isinstance(u, (int, float)) and not isinstance(u, bool) \
                            and math.isfinite(u):     # NaN/Infinity из JSON — не оценка; потолок 100 = 10000%, чтобы round() не падал
                        usage[window] = max(usage[window], min(float(u), MAX_UTILIZATION))
    return usage, status, overage


def _cleanup(data):
    for r in _runs(data):
        root = _temp_root(r.get("tracePath"))
        if root:
            shutil.rmtree(root, ignore_errors=True)


def _verdict(data, returncode, usage, status, overage):
    """(причина остановить L2, оценки недействительны)."""
    partial = bool(data.get("partial"))
    reason = data.get("partialReason") if partial else None
    if reason == "auth_failed":
        return "вход отклонён посреди прогона (auth_failed)", True
    if reason == "interrupted" or returncode in (130, 143) or returncode < 0:
        return "прогон прерван (код %d)" % returncode, True
    if status:
        if _ident(status) != status:       # в сообщение идёт только идентификатор; остальное — в журнал
            _debug("лимит подписки: status=%s" % status)
        return "лимит подписки: status=%s" % _ident(status), True
    for r in _runs(data):
        err = r.get("error")
        if isinstance(err, str) and RE_LIMIT.search(err):
            _debug("ошибка лимита в прогоне: %s" % err[:120])
            return "ошибка лимита в прогоне", True
    if partial:
        return "прогон неполный (partialReason=%s)" % _ident(reason, "не указана"), True
    if overage:
        return "подписка ушла в overage — сверх подписки L2 не платит", False
    if usage["five_hour"] >= five_hour_stop():
        return "окно 5 часов занято на %d%%" % round(usage["five_hour"] * 100), False
    if usage["seven_day"] >= seven_day_stop():
        return "недельный лимит занят на %d%% — запас для дневной работы" % round(usage["seven_day"] * 100), False
    return "", False


def cases(data):
    """{имя кейса: {score, delta, with: [прогоны], without: [прогоны]}}; score/delta — None, если их нет."""
    out = {}
    for case in data.get("cases") or []:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str):
            continue
        agg = case.get("aggregates") if isinstance(case.get("aggregates"), dict) else {}
        arms = case.get("arms") if isinstance(case.get("arms"), dict) else {}
        score, delta = agg.get("score"), agg.get("delta")
        out[case["name"]] = {
            "score": float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else None,
            "delta": float(delta) if isinstance(delta, (int, float)) and not isinstance(delta, bool) else None,
            "with": [r for r in arms.get("with") or [] if isinstance(r, dict)],
            "without": [r for r in arms.get("without") or [] if isinstance(r, dict)],
        }
    return out


def run_scores(entry, arm="with"):
    return [float(r["score"]) for r in entry.get(arm) or []
            if isinstance(r.get("score"), (int, float)) and not isinstance(r.get("score"), bool)]
