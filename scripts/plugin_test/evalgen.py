"""Деревья кейсов `claude plugin eval` из файлов skill-creator (spec очереди 2 §5.2, §5.3, §3a).

Всё пишется во временную копию плагина, в каталоги рядом с его skills/ (--eval-dir):
  evals-trigger/  срабатывание: 1 прогон, 1 ход, только Skill, без моков — моки уводят модель в ToolSearch
  evals-quality/  качество: 3 прогона в каждом плече, Read/Grep/Glob/Skill, моки MCP из снимков L1
  evals-rerun/    повтор проваленных кейсов срабатывания
Генерация детерминирована: одинаковый вход — байт-в-байт одинаковое дерево. Frontmatter — только
ключи, которые знает claude plugin eval (неизвестный ключ — ошибка загрузки); строки — JSON, он валидный YAML.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil

TRIGGER_DIR = "evals-trigger"
QUALITY_DIR = "evals-quality"
RERUN_DIR = "evals-rerun"
GENERATED = (TRIGGER_DIR, QUALITY_DIR, RERUN_DIR)
QUALITY_TOOLS = ["Read", "Grep", "Glob", "Skill"]
QUALITY_RUNS = 3
RE_JS_SPECIAL = re.compile(r"[\\^$.*+?()\[\]{}|/]")
MOCK_RULES = ('You are the MCP server "%s". Answer each call with a realistic result that matches the tool\'s '
              "description and input schema. If required inputs are missing, or a destructive call lacks the "
              "fields it needs, answer with an error that names what is missing.")


def quality_name(skill, case_id):
    return "q-%s-%s" % (skill, case_id)


def trigger_name(skill, query):
    return "t-%s-%s" % (skill, hashlib.sha1(query.encode("utf-8")).hexdigest()[:8])


def native_name(name):
    return "n-%s" % name


def _js(text):
    return RE_JS_SPECIAL.sub(lambda m: "\\" + m.group(0), text)


def input_match(plugin_name, skill):
    """Регулярка JavaScript по JSON-входу Skill: {"skill":"<плагин>:<skill>"} или {"skill":"<skill>"}."""
    return r'"skill"\s*:\s*"(?:%s:)?%s"' % (_js(plugin_name), _js(skill))


def copy_plugin(plugin_dir, dest):
    shutil.copytree(plugin_dir, dest, symlinks=True, ignore=shutil.ignore_patterns(".git", *GENERATED))
    return dest


def _scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _doc(fields, body=""):
    lines = ["---"] + ["%s: %s" % (k, _scalar(v)) for k, v in fields] + ["---", ""]
    if body:
        lines.append(body if body.endswith("\n") else body + "\n")
    return "\n".join(lines) if body else "\n".join(lines) + "\n"


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_triggers(copy_dir, eval_dir, plugin_name, queries, only=None):
    """Кейсы срабатывания в <копия>/<eval_dir>/; only — подмножество имён (повтор). → {имя: запрос}."""
    root = os.path.join(copy_dir, eval_dir)
    out = {}
    for q in queries:
        name = trigger_name(q.skill, q.query)
        if only is not None and name not in only:
            continue
        out[name] = q
        case = os.path.join(root, name)
        _write(os.path.join(case, "prompt.md"), _doc(
            [("tags", ["trigger", "skill:%s" % q.skill]), ("runs", 1), ("max_turns", 1), ("allowed_tools", ["Skill"])],
            q.query))
        bounds = [("min", 1)] if q.should_trigger else [("min", 0), ("max", 0)]
        _write(os.path.join(case, "graders", "fired.md"), _doc(
            [("type", "tool_used"), ("tool", "Skill"), ("input_match", input_match(plugin_name, q.skill))]
            + bounds + [("arm", "both")]))
    os.makedirs(root, exist_ok=True)
    return out


def write_quality(copy_dir, plugin_name, cases, invocable, mocks, native_root="", native_names=()):
    """Кейсы качества, моки MCP и родной набор в <копия>/evals-quality/. → {имя: {kind, skill, id}}."""
    root = os.path.join(copy_dir, QUALITY_DIR)
    out = {}
    for c in cases:
        if c.has_files:
            continue
        name = quality_name(c.skill, c.id)
        out[name] = {"kind": "quality", "skill": c.skill, "id": c.id}
        case = os.path.join(root, name)
        can_call = invocable.get(c.skill, True)
        prompt = c.prompt if can_call else "/%s:%s %s" % (plugin_name, c.skill, c.prompt)
        _write(os.path.join(case, "prompt.md"), _doc(
            [("tags", ["quality", "skill:%s" % c.skill]), ("runs", QUALITY_RUNS), ("allowed_tools", QUALITY_TOOLS)],
            prompt))
        if c.criteria:
            for i, criterion in enumerate(c.criteria, 1):
                _write(os.path.join(case, "graders", "e%d.md" % i), _doc(
                    [("type", "llm")],
                    "PASS if the response satisfies this requirement: %s\n"
                    "FAIL if the response does not satisfy it or contradicts it." % criterion))
        else:
            _write(os.path.join(case, "graders", "expected.md"), _doc(
                [("type", "llm")],
                "PASS if the response substantially matches this expected outcome: %s\n"
                "FAIL if it misses the outcome or contradicts it." % c.expected_output))
        if can_call:
            _write(os.path.join(case, "graders", "fired.md"), _doc(
                [("type", "tool_used"), ("tool", "Skill"), ("input_match", input_match(plugin_name, c.skill)),
                 ("arm", "with-only")]))
    for server in sorted(mocks):
        names = _tool_names(mocks[server])
        if not names:
            continue
        with open(mocks[server], "rb") as fh:
            raw = fh.read()
        _write(os.path.join(root, "mocks", server, "_server.md"),
               _doc([("type", "agent"), ("tools", names)], MOCK_RULES % server))
        os.makedirs(os.path.join(root, "mocks", server), exist_ok=True)
        with open(os.path.join(root, "mocks", server, "_tools.json"), "wb") as fh:
            fh.write(raw)
    for name in native_names:
        shutil.copytree(os.path.join(native_root, name), os.path.join(root, native_name(name)), symlinks=True)
        out[native_name(name)] = {"kind": "native", "skill": "", "id": name}
    native_mocks = os.path.join(native_root, "mocks") if native_root else ""
    if native_mocks and os.path.isdir(native_mocks):
        shutil.copytree(native_mocks, os.path.join(root, "mocks"), symlinks=True, dirs_exist_ok=True)
    os.makedirs(root, exist_ok=True)
    return out


def _tool_names(path):
    """Имена инструментов снимка L1 ({"tools": [{name, …}]}) по алфавиту; нет файла или битый — []."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError, RecursionError):
        return []
    tools = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(tools, list):
        return []
    return sorted({t["name"] for t in tools if isinstance(t, dict) and isinstance(t.get("name"), str)})
