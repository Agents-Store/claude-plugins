"""Источник кейсов L2 — файлы формата skill-creator рядом со skill (spec очереди 2 §5.1).

skills/<s>/evals/evals.json    — кейсы качества: {skill_name, evals: [{id, prompt, expected_output, files,
                                  expectations: [str] | assertions: [{text}]}]}
skills/<s>/evals/triggers.json — запросы срабатывания: [{query, should_trigger}]
tests/plugins/<p>/evals/<case>/ — родные кейсы `claude plugin eval` (редко: точные грейдеры, свои моки)

Модуль только читает и проверяет файлы: ни сети, ни модели. Ошибки — строки без абсолютных путей:
их печатает отчёт, а он уходит в публичный issue.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

MIN_TRUE = 5          # запросов «должен сработать» на skill (spec §5.1)
MIN_FALSE = 5         # запросов «почти, но не должен»
MAX_QUERIES = 20      # потолок skill-creator; больше — прогон дороже без пользы
TRIGGER_KEYS = {"query", "should_trigger"}
RE_CASE_ID = re.compile(r"[A-Za-z0-9_.-]+")
RE_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
NATIVE_SKIP = {"mocks", "results"}


@dataclass(frozen=True)
class Skill:
    name: str          # каталог skills/<name> — по нему его вызывает модель
    dir: str           # абсолютный путь каталога skill
    invocable: bool    # False — disable-model-invocation: true, модель сама его не вызывает

    @property
    def skill_md(self) -> str:
        return os.path.join(self.dir, "SKILL.md")

    @property
    def evals_path(self) -> str:
        return os.path.join(self.dir, "evals", "evals.json")

    @property
    def triggers_path(self) -> str:
        return os.path.join(self.dir, "evals", "triggers.json")


@dataclass(frozen=True)
class QualityCase:
    skill: str
    id: str
    prompt: str
    criteria: tuple            # тексты ожиданий; () — судят по expected_output
    expected_output: str
    has_files: bool            # входные файлы skill-creator: L2 их не подкладывает, кейс пропускается


@dataclass(frozen=True)
class TriggerQuery:
    skill: str
    query: str
    should_trigger: bool


def skills(plugin_dir):
    """Каталоги skills/* с SKILL.md, по алфавиту."""
    root = os.path.join(plugin_dir, "skills")
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        md = os.path.join(root, name, "SKILL.md")
        if not os.path.isfile(md):
            continue
        with open(md, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        out.append(Skill(name=name, dir=os.path.join(root, name), invocable=_invocable(text)))
    return out


def _invocable(text):
    m = RE_FRONTMATTER.match(text)
    if not m:
        return True
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "disable-model-invocation":
            return value.strip().strip("\"'").lower() != "true"
    return True


def _encodable(text):
    """JSON допускает \\ud800 — одиночный суррогат; в UTF-8 его не записать (prompt.md, sha1 имени кейса)."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _read_json(path):
    """(данные, ошибка). В ошибке нет абсолютного пути: str(OSError) его несёт."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), ""
    except OSError as exc:
        return None, "файл не читается: %s" % (exc.strerror or type(exc).__name__)
    except (ValueError, RecursionError) as exc:  # JSONDecodeError, UnicodeDecodeError, глубокая вложенность
        return None, "JSON не разбирается: %s" % exc


def load_quality(skill):
    """(кейсы, ошибки). Кейс с ошибкой не попадает в список, остальные — попадают."""
    data, err = _read_json(skill.evals_path)
    if err:
        return [], [err]
    if not isinstance(data, dict):
        return [], ["ожидается объект {skill_name, evals}"]
    errors = []
    if data.get("skill_name") != skill.name:
        errors.append("skill_name %r != каталог %r" % (data.get("skill_name"), skill.name))
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        return [], errors + ["evals — непустой массив кейсов"]
    cases, seen = [], set()
    for i, ev in enumerate(evals):
        where = "evals[%d]" % i
        if not isinstance(ev, dict):
            errors.append("%s: ожидается объект" % where)
            continue
        cid = ev.get("id")
        if isinstance(cid, bool) or not isinstance(cid, (int, str)):
            errors.append("%s: id — число или строка" % where)
            continue
        cid = str(cid)
        if not RE_CASE_ID.fullmatch(cid):
            errors.append("%s: id %r — только латиница, цифры и _ . -" % (where, cid))
            continue
        if cid in seen:
            errors.append("%s: id %s повторяется" % (where, cid))
            continue
        seen.add(cid)
        prompt = ev.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append("%s: prompt — непустая строка" % where)
            continue
        expected = ev.get("expected_output", "")
        if not isinstance(expected, str):
            errors.append("%s: expected_output — строка" % where)
            continue
        criteria, bad = _criteria(ev)
        if bad:
            errors.append("%s: %s" % (where, bad))
            continue
        if not all(_encodable(t) for t in (prompt, expected, *criteria)):
            errors.append("%s: недопустимый символ (одиночный суррогат \\ud800–\\udfff)" % where)
            continue
        if not criteria and not expected.strip():
            errors.append("%s: нет ни expectations/assertions, ни expected_output — судить не по чему" % where)
            continue
        files = ev.get("files", [])
        if not isinstance(files, list):
            errors.append("%s: files — массив" % where)
            continue
        cases.append(QualityCase(skill.name, cid, prompt, tuple(criteria), expected, bool(files)))
    return cases, errors


def _criteria(ev):
    if "expectations" in ev and "assertions" in ev:
        return [], "и expectations, и assertions — оставь одно"
    if "expectations" in ev:
        items = ev["expectations"]
        if not isinstance(items, list) or not all(isinstance(x, str) and x.strip() for x in items):
            return [], "expectations — массив непустых строк"
        return [x.strip() for x in items], ""
    if "assertions" in ev:
        items = ev["assertions"]
        if not isinstance(items, list) or not all(
                isinstance(x, dict) and isinstance(x.get("text"), str) and x["text"].strip() for x in items):
            return [], "assertions — массив объектов с непустым text"
        return [x["text"].strip() for x in items], ""
    return [], ""


def load_triggers(skill):
    """(запросы, ошибки) из skills/<s>/evals/triggers.json."""
    data, err = _read_json(skill.triggers_path)
    if err:
        return [], [err]
    if not isinstance(data, list) or not data:
        return [], ["ожидается непустой массив [{query, should_trigger}]"]
    errors, out, seen = [], [], set()
    for i, item in enumerate(data):
        where = "[%d]" % i
        if not isinstance(item, dict) or set(item) != TRIGGER_KEYS:
            errors.append("%s: ровно ключи query и should_trigger" % where)
            continue
        query, flag = item["query"], item["should_trigger"]
        if not isinstance(query, str) or not query.strip() or not isinstance(flag, bool):
            errors.append("%s: query — непустая строка, should_trigger — true или false" % where)
            continue
        if not _encodable(query):
            errors.append("%s: недопустимый символ (одиночный суррогат \\ud800–\\udfff)" % where)
            continue
        key = " ".join(query.split()).lower()
        if key in seen:
            errors.append("%s: запрос повторяется" % where)
            continue
        seen.add(key)
        out.append(TriggerQuery(skill.name, query.strip(), flag))
    if len(data) > MAX_QUERIES:
        errors.append("%d запросов — больше %d: прогон дороже без пользы" % (len(data), MAX_QUERIES))
    if not skill.invocable and any(q.should_trigger for q in out):
        errors.append("skill с disable-model-invocation: true модель не вызывает — should_trigger: true невозможен")
    return out, errors


def native_dir(plugin):
    return os.path.join(plugin.tests_dir, "evals")


def native_cases(plugin):
    """(имена кейсов, [(путь каталога, ошибка)]) родного набора tests/plugins/<p>/evals/."""
    root = native_dir(plugin)
    if not os.path.isdir(root):
        return [], []
    names, errors = [], []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if name in NATIVE_SKIP or not os.path.isdir(path):
            continue
        has_prompt = os.path.isfile(os.path.join(path, "prompt.md"))
        has_yaml = os.path.isfile(os.path.join(path, "case.yaml"))
        if not has_prompt and not has_yaml:
            continue
        graders = os.path.join(path, "graders")
        has_graders = os.path.isdir(graders) and any(f.endswith(".md") for f in os.listdir(graders))
        if has_prompt and not has_yaml and not has_graders:
            errors.append((path, "кейс без graders/*.md — claude plugin eval его не загрузит"))
            continue
        names.append(name)
    return names, errors
