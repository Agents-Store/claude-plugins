"""Триаж L2: ответы модели и вердикты судьи — локально, рядом с прогоном (PLUGIN_TEST_L2_KEEP=<каталог>).

Зачем: `claude plugin eval` с --keep-temp оставляет трейсы в <tmp>/claude-eval-*, а runner удаляет их сразу после
чтения (evalrun._cleanup) — агент триажа правит проваленный кейс вслепую, не видя ни ответа, ни того, какое ожидание
судья не засчитал. Переменная окружения runner-а (читается на каждый плагин, не при импорте; ночной прогон идёт под
`env -i` и её не ставит) включает копию ДО очистки: <каталог>/<плагин>/<кейс>.json, по файлу на кейс, прогоны списком.

Откуда что берётся. Оценки и вердикты судьи — из aggregate-result.json (evalrun уже его разбирает): у прогона
graders[] с name, passed, weight, scored, withOnly, judgeVotes (голоса судьи, список bool), explanation и evidence,
у кейса — graders[] с type и graderMarkdown (текст ожидания из evals.json репозитория). Причины судьи CLI НЕ пишет:
explanation llm-грейдера — только «judge votes: PASS FAIL PASS», так что видно, какое ожидание провалено и сколькими
голосами, но не почему. Ответ модели — из трейса прогона (stream-json, tracePath): итоговое событие result, а если
его нет (обрыв по max_turns) — текст последнего сообщения ассистента; нет трейса — evidence llm-грейдера (то, что
судья увидел как ответ; answer_source говорит, откуда он). Среда, заголовки, учётные данные, тела запросов и вызовы
инструментов не копируются: из трейса читаются только текст ответа и имена вызванных Skill. Всё, что попадает в файл
как свободный текст (ответ, пояснение судьи, ошибка прогона), проходит report.Redactor и ещё узкий фильтр
секретоподобных строк.

Ничего из этих файлов не уходит в находки, историю, l2-latest, issue и stdout: наружу идёт одна строка stderr на плагин.
Файлы содержат ответы модели — держать вне репозитория и удалить после триажа.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
import tempfile

from . import report

KEEP_VAR = "PLUGIN_TEST_L2_KEEP"
MAX_ANSWER = 60000
MAX_REASON = 1000
MAX_ERROR = 500
MAX_CRITERION = 2000
RE_NAME = re.compile(r"[A-Za-z0-9_.-]{1,80}")
RE_FILE_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]")
RE_IDENT = re.compile(r"[A-Za-z0-9_.:/-]{1,80}")
RE_FIRED_EXPLANATION = re.compile(r"Skill called \d{1,3}x \(expected [0-9.\u221e]{1,12}\)")   # фиксированная форма tool_used
LLM_TYPES = ("llm", "baseline")
HIDDEN = "<скрыто: похоже на секрет>"
# Узкий фильтр поверх Redactor: он ловит ключи известных форм целой строкой, но не Bearer-заголовок, не пару
# имя=значение и не длинный токен посреди текста
RE_SECRET = re.compile(
    r"(?i)(?:\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,})"
    r"|(?:\b[A-Za-z0-9_.-]*(?:token|secret|passw(?:or)?d|api[_-]?key|authorization|credential)[A-Za-z0-9_.-]*"
    r"\s*[:=]\s*\S{6,})"
    r"|(?:(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}(?![A-Za-z0-9_-]))")


def _debug(text):
    print("[keep] %s" % " ".join(str(text).split())[:400], file=sys.stderr)


def keep_dir():
    """Абсолютный каталог из PLUGIN_TEST_L2_KEEP; переменной нет или она пустая — "" (ничего не сохраняется)."""
    raw = os.environ.get(KEEP_VAR, "").strip()
    return os.path.abspath(os.path.expanduser(raw)) if raw else ""


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _ident(value):
    return value if isinstance(value, str) and RE_IDENT.fullmatch(value) else None


def _answer_text(message):
    """Текст text-блоков сообщения ассистента; иное содержимое (tool_use, thinking) — не копируется."""
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    parts = [b["text"] for b in content or [] if isinstance(b, dict) and b.get("type") == "text"
             and isinstance(b.get("text"), str)]
    return "\n".join(parts)


def read_trace(path):
    """(ответ | None, [имена вызванных Skill] | None, если трейс не открылся) из трейса stream-json. Читается построчно; битые строки пропускаются.

    Ответ — result итогового события; нет его (обрыв по max_turns) — текст последнего сообщения ассистента с текстом."""
    final, last_text, skills = None, None, []
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    with fh:
        for line in fh:
            if '"type"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind == "result" and isinstance(event.get("result"), str) and event["result"].strip():
                final = event["result"]
            elif kind == "assistant":
                message = event.get("message")
                text = _answer_text(message)
                if text.strip():
                    last_text = text
                for block in (message.get("content") if isinstance(message, dict) else None) or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                        inp = block.get("input")
                        name = _ident(inp.get("skill")) if isinstance(inp, dict) else None
                        skills.append(name or "?")
    return (final if final is not None else last_text), skills


def _run(r, arm, index, trace_root, graders):
    """Прогон → запись для файла. Сырые тексты здесь ещё не очищены: это делает Keeper.add."""
    answer, skills, source = None, None, "trace"
    path = r.get("tracePath")
    if trace_root(path):
        answer, skills = read_trace(path)
    has_trace = skills is not None
    kinds = {g["name"]: g for g in graders}
    verdicts = []
    for g in r.get("graders") or []:
        if not isinstance(g, dict) or not isinstance(g.get("name"), str):
            continue
        meta = kinds.get(g["name"], {})
        llm = meta.get("type") in LLM_TYPES
        item = {"name": g["name"], "type": meta.get("type") if _ident(meta.get("type")) else None,
                "passed": g.get("passed") if isinstance(g.get("passed"), bool) else None,
                "weight": _number(g.get("weight")), "scored": g.get("scored") if isinstance(g.get("scored"), bool)
                else None, "with_only": g.get("withOnly") if isinstance(g.get("withOnly"), bool) else None}
        explanation = g.get("explanation") if isinstance(g.get("explanation"), str) else None
        if llm:     # текст ожидания, голоса и пояснение судьи — только у llm-грейдеров
            votes = g.get("judgeVotes")
            item["criterion"] = meta.get("text")
            item["explanation"] = explanation
            item["judge_votes"] = [v for v in votes if isinstance(v, bool)] if isinstance(votes, list) else None
            if answer is None and isinstance(g.get("evidence"), str) and g["evidence"].strip():
                answer, source = g["evidence"], "judge_evidence"
        elif explanation and RE_FIRED_EXPLANATION.fullmatch(explanation):     # иное пояснение tool_used несёт кусок вызова
            item["explanation"] = explanation
        verdicts.append(item)
    return {"arm": arm, "index": index, "answer": answer, "answer_source": source if answer is not None else None,
            "skill_fired": bool(skills) if has_trace else None, "skills_called": skills if has_trace else None,
            "score": _number(r.get("score")), "error": r.get("error") if r.get("error") else None,
            "skipped_paid_graders": bool(r.get("skippedPaidGraders")), "graders": verdicts}


def collect(data, trace_root):
    """Записи по кейсам aggregate-result.json, пока каталоги трейсов ещё есть (вызывать до evalrun._cleanup).

    trace_root — evalrun._temp_root: трейс читается только внутри <tmp>/claude-eval-*. → [{case, prompt, score, delta,
    runs: [прогон…]}]; без cases — []."""
    out = []
    for case in data.get("cases") or []:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str):
            continue
        graders = []
        for g in case.get("graders") or []:
            if isinstance(g, dict) and isinstance(g.get("name"), str):
                text = g.get("graderMarkdown")
                graders.append({"name": g["name"], "type": g.get("type"),
                                "text": text[:MAX_CRITERION] if isinstance(text, str) else None})
        arms = case.get("arms") if isinstance(case.get("arms"), dict) else {}
        agg = case.get("aggregates") if isinstance(case.get("aggregates"), dict) else {}
        runs = []
        for arm in ("with", "without"):
            for index, r in enumerate(x for x in arms.get(arm) or [] if isinstance(x, dict)):
                runs.append(_run(r, arm, index, trace_root, graders))
        prompt = case.get("promptMarkdown")
        out.append({"case": case["name"], "prompt": prompt if isinstance(prompt, str) else None,
                    "score": _number(agg.get("score")), "delta": _number(agg.get("delta")), "runs": runs})
    return out


def _file_name(case):
    """Безопасное имя файла по имени кейса; изменённое имя получает суффикс из хеша — два кейса не сольются."""
    safe = RE_FILE_UNSAFE.sub("_", case)[:80].strip(".") or "case"
    if safe != case:
        safe += "-" + hashlib.sha1(case.encode("utf-8")).hexdigest()[:8]
    return safe + ".json"


class Keeper:
    """Копии ответов одного плагина за один вызов behavior.run: кейс → файл <каталог>/<плагин>/<кейс>.json.

    Прогоны разных вызовов claude (срабатывание, повтор, качество) копятся в файле кейса — повтор не стирает
    первый прогон; новый запуск runner-а начинает файл заново. Сбой записи — строка в stderr, прогон L2 идёт дальше."""

    def __init__(self, root, plugin, redactor):
        self.dir = os.path.join(root, plugin)
        self.plugin = plugin
        self.redactor = redactor
        self.cases = {}
        self.written = 0
        self.failed = False

    def _clean(self, text, limit):
        if not isinstance(text, str):
            return None
        text = self.redactor.text(text[:limit * 2])
        text = "\n".join(HIDDEN if RE_SECRET.search(line) else line for line in text.split("\n"))
        return text[:limit]

    def _record(self, run, call):
        run = dict(run, call=call)
        run["answer"] = self._clean(run["answer"], MAX_ANSWER)
        run["error"] = self._clean(run["error"], MAX_ERROR)
        graders = []
        for g in run["graders"]:
            g = dict(g)
            if "explanation" in g:
                g["explanation"] = self._clean(g["explanation"], MAX_REASON)
            if "criterion" in g:
                g["criterion"] = self._clean(g["criterion"], MAX_CRITERION)
            graders.append(g)
        run["graders"] = graders
        return run

    def add(self, call, tree, records):
        """Прогоны вызова `call` дерева `tree` («trigger» | «quality») → файлы кейсов."""
        for rec in records or []:
            entry = self.cases.setdefault(rec["case"], {
                "plugin": self.plugin, "case": rec["case"], "tree": tree, "prompt": None, "calls": {}, "runs": []})
            entry["prompt"] = self._clean(rec["prompt"], MAX_CRITERION)
            entry["calls"][call] = {"score": rec["score"], "delta": rec["delta"]}
            entry["runs"] += [self._record(r, call) for r in rec["runs"]]
            entry["written"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._write(rec["case"], entry)

    def _write(self, case, entry):
        tmp = ""
        try:
            os.makedirs(self.dir, mode=0o700, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=".keep-", dir=self.dir)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(entry, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp, os.path.join(self.dir, _file_name(case)))
            self.written += 1
        except OSError as exc:
            if not self.failed:      # одна строка на плагин: тот же сбой повторится на каждом кейсе
                _debug("%s: ответы не сохранены: %s" % (self.plugin, exc.strerror or type(exc).__name__))
            self.failed = True
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def announce(self):
        """Одна строка stderr на плагин, если что-то записано."""
        if self.written:
            print("[behavior] %s: ответы сохранены в %s" % (self.plugin, self.dir), file=sys.stderr)


def open_keeper(plugin, env, repo):
    """Keeper для плагина, если задана PLUGIN_TEST_L2_KEEP; иначе None. Имя плагина — только безопасное для пути."""
    root = keep_dir()
    if not root:
        return None
    if not RE_NAME.fullmatch(plugin) or plugin in (".", ".."):
        _debug("имя плагина не годится для имени каталога — ответы не сохраняются")
        return None
    return Keeper(root, plugin, report.Redactor(env, repo=repo))
