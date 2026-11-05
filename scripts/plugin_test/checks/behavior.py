"""behavior: L2 «Поведение» — срабатывание и качество skills через claude plugin eval (spec очереди 2).

Только --mode server и только по явному --check behavior (model.OPT_IN_CHECKS); платит подписка (evalrun).
fail — подтверждённый промах, ниже порога, регресс (advisory понижает до warn); info — «не помогает»,
«нестабильно»; infra — лимит, окно, вход, сбой CLI. Сообщения начинаются с model.L2_*: по ним issue
раскладывает раздел L2, а l2plan переносит плагины с L2_NOT_RUN на следующую ночь.
В отчёт не попадает текст ответов модели и вывод CLI — только имена кейсов, запросы из репозитория, оценки
и фиксированные классификации сбоев; сырая деталь идёт одной строкой в stderr (журнал ночного прогона).
Волны и ручные прогоны могут удешевить повтор переменными окружения runner-а (читаются на каждый плагин, не при
импорте; ночной прогон их не ставит): PLUGIN_TEST_L2_SKILLS — только эти skills плагина, без родных кейсов;
PLUGIN_TEST_L2_QUICK=1 — качество в один прогон без плеча «без плагина» (нет дельты, регресса и записи в историю);
PLUGIN_TEST_L2_KEEP=<каталог> — триаж: ответы модели и вердикты судьи каждого прогона копируются в
<каталог>/<плагин>/<кейс>.json до очистки трейсов (keep.py); в находки, историю, issue и stdout они не попадают.
Ошибка отдельного прогона (API, сеть, 5xx — не лимит) вердиктом не становится: такой прогон не судится, а кейс без
чистых прогонов и вызов, где ошибка у большинства, дают одну infra «L2 сбой» (ожидаемый обрыв прогона срабатывания
по max_turns: 1 ошибкой не считается — evalrun.run_error). Прошлый снимок подписки (<state-dir>/l2-usage.json,
пишет _call) не даёт начать плагин, если порог уже превышен, а окно не сбросилось.
"""
from __future__ import annotations

import datetime
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

from .. import evalgen, evalrun, evalsrc, history, keep, mcp_config, snapshots
from ..model import (FAIL, INFO, INFRA, L2_BELOW, L2_FAILED, L2_FLAKY, L2_MISFIRE, L2_NOT_RUN, L2_REGRESS,
                     L2_STOPPED, L2_TIMEOUT, L2_UNHELPFUL, SERVER, Finding)

CHECK = "behavior"
CONFIRM_RUNS = 2          # повтор проваленного кейса срабатывания: всего 3 прогона, промах — 2 из 3
QUERY_SHOWN = 120
GRACE_AFTER_DEADLINE = 2700   # вызов, начатый до конца окна, может идти ещё 45 минут — юнит убьют в 08:00
MIN_CALL_TIMEOUT = 300
EPS = 1e-9                 # допуск сравнения оценок: среднее трёх 0.8 бывает 0.7999999999999999
SKILLS_VAR = "PLUGIN_TEST_L2_SKILLS"   # волны: только эти skills плагина (имена через запятую); ночной прогон не ставит
QUICK_VAR = "PLUGIN_TEST_L2_QUICK"     # волны: быстрый режим качества — 1 прогон без плеча «без плагина»; только значение 1
FIX_TRIGGER = "уточни description skill (run_loop skill-creator) или замени запрос: /plugin-creator:evals"
FIX_QUALITY = "разбор: /plugin-creator:test, слой behavior; свой порог — [behavior.case] с причиной"
FIX_INFRA = "сбой окружения L2 — журнал ночного прогона; плагин уйдёт в перенос на следующую ночь"


@dataclass
class Sources:
    skills: dict = field(default_factory=dict)     # имя → evalsrc.Skill
    triggers: list = field(default_factory=list)   # evalsrc.TriggerQuery
    quality: list = field(default_factory=list)    # evalsrc.QualityCase
    native: list = field(default_factory=list)     # имена родных кейсов
    routes: dict = field(default_factory=dict)     # skill → команды плагина, ведущие к нему (evalgen.skill_routes)


def _skill_filter():
    """Имена из PLUGIN_TEST_L2_SKILLS: через запятую, пробелы по краям и пустые элементы отброшены, повторы тоже."""
    names = (name.strip() for name in os.environ.get(SKILLS_VAR, "").split(","))
    return list(dict.fromkeys(name for name in names if name))


def _quick():
    """Быстрый режим качества — только значение «1»: «true», «0», пробел вокруг — выключено."""
    return os.environ.get(QUICK_VAR) == "1"


def _sources(plugin, skip, only=()):
    """Источники кейсов без снятых [skip] "behavior": маска — путь от каталога плагина (как runner.skipped_by),
    у родного кейса — его имя в дереве n-<имя>. Снятый файл не доходит до генерации и до вызова claude.
    only — фильтр волн (_skill_filter): кейсы только этих skills и никаких родных кейсов; src.skills остаётся полным —
    по нему видно, какие имена фильтра плагину неизвестны."""
    def skipped(rel):
        return any(fnmatch.fnmatch(rel, g) for g in skip)

    src = Sources()
    for skill in evalsrc.skills(plugin.dir):
        src.skills[skill.name] = skill
        if only and skill.name not in only:
            continue
        if os.path.isfile(skill.triggers_path) and not skipped(os.path.relpath(skill.triggers_path, plugin.dir)):
            src.triggers += evalsrc.load_triggers(skill)[0]
        if os.path.isfile(skill.evals_path) and not skipped(os.path.relpath(skill.evals_path, plugin.dir)):
            src.quality += [c for c in evalsrc.load_quality(skill)[0] if not c.has_files]
    if not only:
        src.native = [n for n in evalsrc.native_cases(plugin)[0] if not skipped(evalgen.native_name(n))]
    return src


def _debug(text):
    """Сырая деталь — одной строкой в stderr, не в находку: issue публичный (spec очереди 2 §7)."""
    print("[behavior] %s" % " ".join(str(text).split())[:400], file=sys.stderr)


def _infra(plugin, message, file="", fix=FIX_INFRA):
    return Finding(plugin.name, CHECK, INFRA, message, file, 0, fix)


def _stopped(plugin, reason):
    """info: этот плагин остановил L2 на ночь — по нему l2plan откладывает остальные репозитории."""
    return Finding(plugin.name, CHECK, INFO, "%s: %s" % (L2_STOPPED, reason), "", 0, FIX_INFRA)


def _runs_phrase(n):
    """«все 2 прогона», «все 5 прогонов», «все 21 прогон»; один — «единственный прогон»."""
    if n == 1:
        return "единственный прогон"
    last, tens = n % 10, n % 100
    word = "прогон" if last == 1 and tens != 11 else "прогона" if 2 <= last <= 4 and not 12 <= tens <= 14 else "прогонов"
    return "все %d %s" % (n, word)


def _mean(values):
    return sum(values) / len(values) if values else None


def _short(text):
    flat = " ".join(text.split())
    return flat if len(flat) <= QUERY_SHOWN else flat[:QUERY_SHOWN - 1] + "…"


def _commit(repo):
    try:
        done = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


def _mocks(plugin):
    """{сервер: путь снимка L1} для серверов .mcp.json, у которых снимок есть."""
    try:
        servers = mcp_config.servers(plugin)
    except mcp_config.McpConfigError:     # битый .mcp.json — дело mcp-names; L2 идёт без моков
        return {}
    return {name: snapshots.mcp_path(plugin, name) for name in sorted(servers)
            if os.path.isfile(snapshots.mcp_path(plugin, name))}


def run(plugin, ctx, manifest):
    if ctx.mode != SERVER:
        return []
    only = _skill_filter()
    src = _sources(plugin, manifest.skip.get(CHECK, []), only)
    if only:
        known = [name for name in only if name in src.skills]
        if not known:      # плагин вне фильтра: не «не прогнан» — на следующую ночь его не переносить
            _debug("%s: %s — нет skill плагина в фильтре" % (plugin.name, SKILLS_VAR))
            return []
        if len(known) < len(only):
            _debug("%s: %s — неизвестные: %s" % (plugin.name, SKILLS_VAR, ", ".join(n for n in only if n not in known)))
    if not (src.triggers or src.quality or src.native):
        return []
    if ctx.l2_stop:
        return [_infra(plugin, "%s: %s" % (L2_NOT_RUN, ctx.l2_stop))]
    if ctx.deadline and time.time() >= ctx.deadline:
        return [_infra(plugin, "%s: окно ночи закончилось" % L2_NOT_RUN)]
    reason = evalrun.stored_stop(ctx.state_dir)
    if reason:     # порог проверяется только после вызова, а прошлая ночь уже увидела занятое окно: ни auth status, ни eval
        ctx.l2_stop = reason
        return [_infra(plugin, "%s: %s" % (L2_NOT_RUN, reason)), _stopped(plugin, reason)]
    claude = shutil.which("claude")
    if not claude:
        return [_infra(plugin, "%s: нет CLI claude" % L2_FAILED, fix="npm install -g @anthropic-ai/claude-code")]
    env = evalrun.environment()
    reason = evalrun.preflight(claude, env)
    if reason:
        ctx.l2_stop = reason
        return [_infra(plugin, "%s: %s" % (L2_NOT_RUN, reason), fix="claude auth login под пользователем сервиса"),
                _stopped(plugin, reason)]
    src.routes = evalgen.skill_routes(plugin.dir, plugin.name)     # раз на плагин: команда, ведущая к skill, = срабатывание
    repo_name = os.path.basename(os.path.abspath(plugin.repo))
    past = history.scores(ctx.state_dir, repo_name, plugin.name, model=evalrun.MODEL)
    keeper = keep.open_keeper(plugin.name, ctx.env, plugin.repo)
    entries, out = [], []
    with tempfile.TemporaryDirectory(prefix="plugin-test-l2-") as tmp:
        # L2 меряет skills, не агентов: в песочнице агент плагина забирает ход у Skill (срабатывание) и портит
        # ответ (качество) — одна копия без agents/ на все прогоны плагина
        copy = evalgen.copy_plugin(plugin.dir, os.path.join(tmp, plugin.dirname), drop_agents=True)
        if src.triggers:
            out += _triggers(plugin, ctx, src, copy, tmp, claude, env, entries, keeper)
        if src.quality or src.native:
            if ctx.l2_stop:
                out.append(_infra(plugin, "%s: %s (кейсы качества)" % (L2_NOT_RUN, ctx.l2_stop)))
            else:
                out += _quality(plugin, ctx, manifest, src, copy, tmp, claude, env, past, entries, keeper)
    if keeper:
        keeper.announce()
    if ctx.l2_stop:   # остановил этот плагин (выше ранний возврат при уже заданной остановке)
        out.append(_stopped(plugin, ctx.l2_stop))
    if entries:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        commit = _commit(plugin.repo)
        try:
            history.append(ctx.state_dir, [dict(e, repo=repo_name, plugin=plugin.name, date=stamp, commit=commit,
                                                model=evalrun.MODEL) for e in entries])
        except OSError as exc:   # находки уже есть — не терять их из-за каталога состояния
            out.append(_infra(plugin, "%s: история не записана: %s" % (L2_FAILED, exc.strerror or type(exc).__name__)))
    return out


def _call(plugin, ctx, label, claude, copy, eval_dir, out_dir, env, keeper=None, tree="", **kw):
    """(RunResult | None, находки). None — оценкам не верить, находки уже объясняют почему.
    keeper — триаж (keep.py): ответы и вердикты судьи сохраняются и у недействительного вызова."""
    timeout = L2_TIMEOUT
    if ctx.deadline:
        left = int(ctx.deadline + GRACE_AFTER_DEADLINE - time.time())
        if left < MIN_CALL_TIMEOUT:      # до юнита-убийцы не успеть даже минимальный вызов — перенос на следующую ночь
            return None, [_infra(plugin, "%s: окно ночи закончилось (%s)" % (L2_NOT_RUN, label))]
        timeout = min(L2_TIMEOUT, left)
    try:
        res = evalrun.run(claude, copy, eval_dir, out_dir, env=env, timeout=timeout, keep=keeper is not None, **kw)
    except evalrun.EvalError as exc:
        if ctx.deadline and time.time() >= ctx.deadline:
            return None, [_infra(plugin, "%s: окно ночи закончилось во время прогона (%s)" % (L2_NOT_RUN, label))]
        return None, [_infra(plugin, "%s: %s: %s" % (L2_FAILED, label, exc))]
    if keeper is not None:
        try:
            keeper.add(label, tree, res.kept)
        except Exception as exc:     # noqa: BLE001 — копия для триажа не должна ронуть прогон L2
            _debug("%s: копия для триажа не снята: %s" % (plugin.name, type(exc).__name__))
    evalrun.save_usage(ctx.state_dir, res)      # и у недействительного вызова: лимит в трейсе — самое важное для следующего
    found = [_infra(plugin, "%s: %s: %s" % (L2_FAILED, label, p)) for p in res.problems]
    if res.stop:
        ctx.l2_stop = res.stop
    if res.invalid:
        return None, found + [_infra(plugin, "%s: %s (%s)" % (L2_NOT_RUN, res.stop, label))]
    return res, found


def _first_error(entries, turn_cap_ok):
    """Текст первой ошибки прогонов — только в журнал (stderr), не в находку."""
    for entry in entries:
        for r in entry["with"]:
            if evalrun.run_error(r, turn_cap_ok):
                return str(r.get("error"))
    return ""


def _mostly_errored(plugin, label, entries, turn_cap_ok=False):
    """Находка, если больше половины прогонов вызова с ошибкой (не лимит — его ловит evalrun): API лёг, оценки этого
    вызова не судим вовсе. Ровно половина — вызов в силе, ошибочные прогоны отсеиваются по одному. Иначе None."""
    runs = [r for e in entries for r in e["with"]]
    bad = sum(1 for r in runs if evalrun.run_error(r, turn_cap_ok))
    if not runs or bad * 2 <= len(runs):
        return None
    _debug("%s: %s: %d из %d прогонов с ошибкой: %s" % (plugin.name, label, bad, len(runs),
                                                        _first_error(entries, turn_cap_ok)[:120]))
    return _infra(plugin, "%s: %s: более половины прогонов с ошибкой" % (L2_FAILED, label))


def _triggers(plugin, ctx, src, copy, tmp, claude, env, entries, keeper=None):
    cases = evalgen.write_triggers(copy, evalgen.TRIGGER_DIR, plugin.name, src.triggers, routes=src.routes)
    res, out = _call(plugin, ctx, "срабатывание", claude, copy, evalgen.TRIGGER_DIR, os.path.join(tmp, "out-trigger"),
                     env, keeper, "trigger", ablation="none", runs=1)
    if res is None:
        return out
    got = evalrun.cases(res.data)
    outage = _mostly_errored(plugin, "срабатывание", [got[n] for n in cases if n in got], turn_cap_ok=True)
    if outage:
        return out + [outage]
    first = {}      # кейс → оценка чистого первого прогона; None — прогон с ошибкой, его не судим
    for name in sorted(cases):
        scores = evalrun.clean_scores(got[name], turn_cap_ok=True) if name in got else []
        if scores:
            first[name] = scores[0]
        elif name in got and evalrun.error_runs(got[name], turn_cap_ok=True):
            first[name] = None
            _debug("%s: %s: прогон с ошибкой: %s" % (plugin.name, name, _first_error([got[name]], True)[:120]))
        else:
            out.append(_infra(plugin, "%s: кейс %s без оценки" % (L2_FAILED, name),
                              plugin.rel(src.skills[cases[name].skill].triggers_path)))
    pending = sorted(n for n, s in first.items() if s is None or s < 1.0)    # провал и прогон с ошибкой — на повтор
    again = {}      # кейс → оценки чистых прогонов повтора; нет ключа — повтора не было
    if pending and not ctx.l2_stop:
        evalgen.write_triggers(copy, evalgen.RERUN_DIR, plugin.name, src.triggers, only=set(pending),
                               routes=src.routes)
        res2, more = _call(plugin, ctx, "повтор срабатывания", claude, copy, evalgen.RERUN_DIR,
                           os.path.join(tmp, "out-rerun"), env, keeper, "trigger", ablation="none",
                           runs=CONFIRM_RUNS)
        out += more
        if res2 is not None:
            got2 = evalrun.cases(res2.data)
            outage = _mostly_errored(plugin, "повтор срабатывания", [got2[n] for n in pending if n in got2],
                                     turn_cap_ok=True)
            if outage:
                out.append(outage)
            else:
                again = {n: evalrun.clean_scores(got2[n], turn_cap_ok=True) for n in pending
                         if n in got2 and got2[n]["with"]}
    for name in sorted(first):
        q = cases[name]
        file = plugin.rel(src.skills[q.skill].triggers_path)
        if first[name] is not None and first[name] >= 1.0:
            entries.append({"case": name, "score": 1.0, "delta": None, "runs": 1, "ok": True})
            continue
        if name not in again:
            out.append(_infra(plugin, "%s: %s не перепроверен" % (L2_NOT_RUN, name), file))
            continue
        runs = ([] if first[name] is None else [first[name]]) + again[name]
        if not runs:       # ни первый прогон, ни повтор не дали чистой оценки: не вердикт, а сбой окружения
            out.append(_infra(plugin, "%s: %s — прогон с ошибкой" % (L2_FAILED, name), file))
            continue
        misses = sum(1 for s in runs if s < 1.0)
        if misses and len(runs) < 2:      # единственный чистый прогон — промах без подтверждения
            out.append(_infra(plugin, "%s: %s не перепроверен" % (L2_NOT_RUN, name), file))
            continue
        entries.append({"case": name, "score": 1 - misses / len(runs), "delta": None, "runs": len(runs), "ok": True})
        if not misses:
            continue
        text = "%s «%s» — ожидалось: %s; промах в %d из %d" % (
            q.skill, _short(q.query), "сработать" if q.should_trigger else "не срабатывать", misses, len(runs))
        level, prefix = (FAIL, L2_MISFIRE) if misses >= 2 else (INFO, L2_FLAKY)
        out.append(Finding(plugin.name, CHECK, level, "%s: %s" % (prefix, text), file, 0, FIX_TRIGGER))
    return out


def _quality(plugin, ctx, manifest, src, copy, tmp, claude, env, past, entries, keeper=None):
    quick = _quick()
    invocable = {name: s.invocable for name, s in src.skills.items()}
    meta = evalgen.write_quality(copy, plugin.name, src.quality, invocable, _mocks(plugin),
                                 evalsrc.native_dir(plugin), tuple(src.native), routes=src.routes,
                                 **({"runs": 1} if quick else {}))
    if not meta:
        return []
    if quick:    # один прогон, без плеча «без плагина»: дельты нет, а прошлые медианы (3 прогона с/без) несравнимы
        _debug("%s: быстрый режим качества (1 прогон, без сравнения)" % plugin.name)
    res, out = _call(plugin, ctx, "качество", claude, copy, evalgen.QUALITY_DIR, os.path.join(tmp, "out-quality"),
                     env, keeper, "quality",
                     **({"ablation": "none", "runs": 1} if quick else {"ablation": "with-without"}))
    if res is None:
        return out
    got = evalrun.cases(res.data)
    for name in sorted(meta):
        m = meta[name]
        if m["kind"] == "quality":
            file = plugin.rel(src.skills[m["skill"]].evals_path)
        else:
            file = plugin.rel(os.path.join(evalsrc.native_dir(plugin), m["id"]))
        entry = got.get(name)
        if entry is None:
            out.append(_infra(plugin, "%s: кейс %s без оценки" % (L2_FAILED, name), file))
            continue
        runs = entry["with"]
        errors = evalrun.error_runs(entry)
        if runs and errors == len(runs):
            _debug("%s: %s" % (name, _first_error([entry], False)[:120]))
            out.append(_infra(plugin, "%s: %s — %s с ошибкой" % (L2_FAILED, name, _runs_phrase(len(runs))), file))
            continue
        good = evalrun.clean_runs(entry)
        if errors:
            _debug("%s: %s: %d из %d прогонов с ошибкой: %s" % (plugin.name, name, errors, len(runs),
                                                                _first_error([entry], False)[:120]))
            if not quick and len(good) < 2:     # из чистых прогонов оценку не собрать: не вердикт, а сбой окружения
                out.append(_infra(plugin, "%s: %s — чистых прогонов меньше двух из %d" % (L2_FAILED, name, len(runs)),
                                  file))
                continue
        if any(r.get("skippedPaidGraders") for r in good):
            out.append(_infra(plugin, "%s: %s — судья пропущен, оценка несравнима" % (L2_FAILED, name), file))
            continue
        # оценка и дельта считаются по чистым прогонам, если ошибка была в любом плече: агрегат CLI считает её нулём
        score = _mean(evalrun.clean_scores(entry)) if errors else entry["score"]
        if score is None:
            out.append(_infra(plugin, "%s: кейс %s без оценки" % (L2_FAILED, name), file))
            continue
        delta = entry["delta"]
        if quick:
            delta = None
        elif errors or evalrun.error_runs(entry, "without"):
            bare = _mean(evalrun.clean_scores(entry, "without"))
            delta = None if bare is None else score - bare
        threshold = manifest.threshold_for(name)
        previous = past.get(name, [])
        if not quick:      # оценка одного прогона в историю не идёт: следующие медианы считаются по полным
            entries.append({"case": name, "score": score, "delta": delta, "runs": len(good), "ok": True})
        if score < threshold - EPS:
            out.append(Finding(plugin.name, CHECK, FAIL, "%s: %s — %.2f < %.2f" % (L2_BELOW, name, score, threshold),
                               file, 0, FIX_QUALITY))
        median = None if quick else history.regressed(previous, score)
        if median is not None:
            out.append(Finding(plugin.name, CHECK, FAIL, "%s: %s — %.2f, медиана последних %d — %.2f"
                               % (L2_REGRESS, name, score, len(previous[-history.WINDOW:]), median),
                               file, 0, FIX_QUALITY))
        if delta is not None and delta <= 0:
            out.append(Finding(plugin.name, CHECK, INFO, "%s: %s — с плагином %.2f, без %.2f"
                               % (L2_UNHELPFUL, name, score, score - delta), file, 0,
                               "skill не добавляет к ответу без него: усиль skill или замени кейс"))
    return out
