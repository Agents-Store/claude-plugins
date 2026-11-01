"""Запуск `claude plugin eval` за счёт подписки и разбор результата (spec очереди 2 §6.3, §6.4, §3a).

Окружение — только allowlist: ANTHROPIC_API_KEY важнее входа по подписке, и CLI передаёт большинство
ANTHROPIC_* в прогон. К allowlist всегда добавляется ENABLE_CLAUDEAI_MCP_SERVERS=false: коннекторы аккаунта
claude.ai иначе грузятся в прогон и перехватывают единственный ход срабатывания. Признаки лимита — события
rate_limit_event в трейсах (--keep-temp); каталоги <tmp>/claude-eval-* удаляются сразу после чтения, только по
точному шаблону. Пороги остановки по окнам подписки — по умолчанию 0.9 и 0.8; волны и ручные прогоны
переопределяют их переменными PLUGIN_TEST_L2_FIVE_HOUR_STOP и PLUGIN_TEST_L2_SEVEN_DAY_STOP.
Вывод `claude auth status` несёт email и организацию — он не печатается и не пишется никуда.
Последний снимок окон подписки (загрузка, статус, время сброса) после каждого вызова ложится в
<state-dir>/l2-usage.json: пороги проверяются только после вызова, а следующая ночь иначе не знала бы, что неделя занята.
Ошибка отдельного прогона (API, сеть, 5xx) — не оценка: run_error отличает её от ожидаемого обрыва прогона
срабатывания по max_turns: 1.
"""
from __future__ import annotations

import datetime
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
USAGE_FILE = "l2-usage.json"
# Длина окна: сброс дальше неё — снимок испорчен, ему не верим
WINDOW_LEN = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}
# Сброс неизвестен: снимку верим, пока он моложе этого срока. Неделя — сутки, не 7: пока снимок держит остановку,
# его никто не обновляет, а одна пропущенная ночь дешевле недели без ротации
WINDOW_AGE = {"five_hour": 5 * 3600, "seven_day": 24 * 3600}
RESET_KEYS = ("resetsAt", "resets_at", "resetAt", "reset_at")
MILLISECONDS = 1e11          # unix-время больше этого — миллисекунды (в секундах это год 5138)
# Ожидаемый обрыв прогона срабатывания: max_turns: 1, грейдер к этому моменту уже видел вызов Skill. Узко — только эта форма.
TURN_CAP = re.compile(r"exit 1: Reached maximum number of turns \(1\)")


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
    snapshot: dict = field(default_factory=dict)     # {status, overage, windows: {окно: {utilization, resets_at?}}} из трейсов


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
        usage, status, overage, result.snapshot = _scan_traces(data)
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


def _reset_time(value):
    """Unix-секунды из времени сброса окна: число (секунды или миллисекунды) или ISO-8601; иное — None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if not math.isfinite(value) or value <= 0:
            return None
        return float(value) / 1000.0 if value > MILLISECONDS else float(value)
    if isinstance(value, str):
        try:
            moment = datetime.datetime.fromisoformat(value.strip())
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=datetime.timezone.utc)
            return moment.timestamp()
        except (ValueError, OverflowError, OSError):
            return None
    return None


def _window_reset(info, window, value):
    """Сброс окна: свой ключ окна, иначе сброс события, если событие про это окно (rateLimitType)."""
    for source in (value, info if info.get("rateLimitType") == window else {}):
        for key in RESET_KEYS:
            reset = _reset_time(source.get(key))
            if reset is not None:
                return reset
    return None


def _scan_traces(data):
    usage = {"five_hour": 0.0, "seven_day": 0.0}
    status, overage, last_status = "", False, ""
    windows_seen = {}
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
                if isinstance(info.get("status"), str) and info["status"]:
                    last_status = info["status"]
                    if info["status"] not in OK_STATUSES:
                        status = info["status"]
                if info.get("isUsingOverage") is True:
                    overage = True
                windows = info.get("unifiedWindows")
                for window, value in (windows.items() if isinstance(windows, dict) else ()):
                    u = value.get("utilization") if isinstance(value, dict) else None
                    if window in usage and isinstance(u, (int, float)) and not isinstance(u, bool) \
                            and math.isfinite(u):     # NaN/Infinity из JSON — не оценка; потолок 100 = 10000%, чтобы round() не падал
                        usage[window] = max(usage[window], min(float(u), MAX_UTILIZATION))
                        seen = windows_seen.setdefault(window, {})
                        seen["utilization"] = usage[window]
                        reset = _window_reset(info, window, value)
                        if reset is not None:
                            seen["resets_at"] = max(reset, seen.get("resets_at", reset))
    shown = status or last_status
    snapshot = {"status": _ident(shown) if shown else "", "overage": overage, "windows": windows_seen}
    return usage, status, overage, snapshot


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
        return _five_hour_reason(usage["five_hour"]), False
    if usage["seven_day"] >= seven_day_stop():
        return _seven_day_reason(usage["seven_day"]), False
    return "", False


def _five_hour_reason(utilization):
    return "окно 5 часов занято на %d%%" % round(utilization * 100)


def _seven_day_reason(utilization):
    return "недельный лимит занят на %d%% — запас для дневной работы" % round(utilization * 100)


def _read_usage(state_dir):
    """Сохранённый снимок как dict; нет файла, битый JSON или не dict — пусто."""
    try:
        with open(os.path.join(state_dir, USAGE_FILE), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_usage(state_dir, result, now=None):
    """Последний снимок окон подписки из вызова — в <state-dir>/l2-usage.json, атомарно (временный файл и замена).

    Окно, которое вызов видел, перезаписывается (свежее наблюдение важнее прежнего максимума), невиданное остаётся.
    Нет каталога состояния или в трейсах не было оценок загрузки — ничего не пишется. Сбой записи — строка в журнал."""
    snapshot = result.snapshot if isinstance(result.snapshot, dict) else {}
    windows = snapshot.get("windows")
    if not state_dir or not windows:
        return
    now = time.time() if now is None else now
    data = {k: v for k, v in _read_usage(state_dir).items() if k in WINDOW_AGE and isinstance(v, dict)}
    for window, seen in windows.items():
        data[window] = {"utilization": seen["utilization"], "at": now}
        if "resets_at" in seen:
            data[window]["resets_at"] = seen["resets_at"]
    data["status"] = snapshot.get("status", "")
    data["overage"] = bool(snapshot.get("overage"))
    tmp = ""
    try:
        os.makedirs(state_dir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".l2-usage-", dir=state_dir)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, os.path.join(state_dir, USAGE_FILE))
    except OSError as exc:
        _debug("%s не записан: %s" % (USAGE_FILE, exc.strerror or type(exc).__name__))
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _window_open(seen, window, now):
    """Окно снимка ещё то же: сброс впереди (не дальше длины окна); сброс неизвестен — снимок моложе срока
    (5 часов, сутки). Снимок из будущего или со сбросом дальше длины окна испорчен — не держит."""
    at = seen.get("at")
    if isinstance(at, (int, float)) and not isinstance(at, bool) and math.isfinite(at) and at > now:
        return False
    reset = _reset_time(seen.get("resets_at"))
    if reset is not None:
        return now < reset <= now + WINDOW_LEN[window]
    if isinstance(at, bool) or not isinstance(at, (int, float)) or not math.isfinite(at):
        return False
    return now - at < WINDOW_AGE[window]


def stored_stop(state_dir, now=None):
    """Причина не начинать вызов: прошлый снимок подписки уже выше порога остановки, а окно не сбросилось. "" — можно.

    Те же пороги и переопределения, что у вердикта вызова (five_hour_stop / seven_day_stop), тот же текст причины.
    Нет файла, битый или с мусором в полях — не остановка: снимок только подсказка, вызов сам проверит лимит."""
    data = _read_usage(state_dir) if state_dir else {}
    if not data:
        return ""
    now = time.time() if now is None else now
    for window, threshold, reason in (("five_hour", five_hour_stop(), _five_hour_reason),
                                      ("seven_day", seven_day_stop(), _seven_day_reason)):
        seen = data.get(window)
        u = seen.get("utilization") if isinstance(seen, dict) else None
        if isinstance(u, bool) or not isinstance(u, (int, float)) or not math.isfinite(u):
            continue
        u = min(float(u), MAX_UTILIZATION)
        if u >= threshold and _window_open(seen, window, now):
            _debug("прошлый снимок %s: %s занято на %d%%, окно ещё не сбросилось — вызов не начат"
                   % (USAGE_FILE, window, round(u * 100)))
            return reason(u)
    return ""


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


def _score(run):
    score = run.get("score")
    return float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else None


def run_scores(entry, arm="with"):
    return [s for s in map(_score, entry.get(arm) or []) if s is not None]


def run_error(run, turn_cap_ok=False):
    """True — у прогона ошибка (API, сеть, 5xx): его оценке верить нельзя, нулём она не считается.

    turn_cap_ok — кейсы срабатывания (max_turns: 1): их обрыв по числу ходов ожидаем, оценку грейдер выставил."""
    err = run.get("error")
    if not err:
        return False
    return not (turn_cap_ok and isinstance(err, str) and TURN_CAP.fullmatch(err.strip()))


def clean_runs(entry, arm="with", turn_cap_ok=False):
    return [r for r in entry.get(arm) or [] if not run_error(r, turn_cap_ok)]


def error_runs(entry, arm="with", turn_cap_ok=False):
    return sum(1 for r in entry.get(arm) or [] if run_error(r, turn_cap_ok))


def clean_scores(entry, arm="with", turn_cap_ok=False):
    """Оценки прогонов без ошибки (у прогона без числовой оценки её нет)."""
    return [s for s in map(_score, clean_runs(entry, arm, turn_cap_ok)) if s is not None]
