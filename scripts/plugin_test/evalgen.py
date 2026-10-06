"""Деревья кейсов `claude plugin eval` из файлов skill-creator (spec очереди 2 §5.2, §5.3, §3a).

Всё пишется во временную копию плагина, в каталоги рядом с его skills/ (--eval-dir):
  evals-trigger/  срабатывание: 1 прогон, 1 ход, только Skill, без моков — моки уводят модель в ToolSearch
  evals-quality/  качество: 3 прогона в каждом плече, Read/Grep/Glob/Skill, моки MCP из снимков L1
  evals-rerun/    повтор проваленных кейсов срабатывания
Из plugin.json копии убран ключ dependencies: с ним плагин в песочнице не грузится. Копия L2 — ещё и без
agents/ (copy_plugin drop_agents): L2 меряет skills, агент плагина забирает ход у Skill и портит ответ.
Команда плагина, которая ведёт к skill (skill_routes), засчитывается как срабатывание этого skill.
Генерация детерминирована: одинаковый вход — байт-в-байт одинаковое дерево. Frontmatter — только
ключи, которые знает claude plugin eval (неизвестный ключ — ошибка загрузки); строки — JSON, он валидный YAML.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil

from . import evalsrc

TRIGGER_DIR = "evals-trigger"
QUALITY_DIR = "evals-quality"
RERUN_DIR = "evals-rerun"
GENERATED = (TRIGGER_DIR, QUALITY_DIR, RERUN_DIR)
QUALITY_TOOLS = ["Read", "Grep", "Glob", "Skill"]
QUALITY_RUNS = 3
MAX_ROUTES_PER_COMMAND = 2     # команда, ведущая к большему числу skills, — хаб, а не alias
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


def input_match(plugin_name, skill, aliases=()):
    """Регулярка JavaScript по JSON-входу Skill: {"skill":"<плагин>:<skill>"} или {"skill":"<skill>"}.
    aliases — команды плагина, которые ведут к этому skill: модель часто зовёт команду вместо skill,
    и это то же срабатывание. Якорение прежнее: чужой плагин и более длинное имя не подходят."""
    names = "|".join(_js(n) for n in (skill, *aliases))
    return r'"skill"\s*:\s*"(?:%s:)?(?:%s)"' % (_js(plugin_name), names)


def skill_routes(plugin_dir, plugin_name):
    """{skill: [команды]} — какие commands/*.md плагина ведут к skill. Команда (имя — stem файла) ведёт к skill,
    если её текст называет его как skills/<skill>/ или <плагин>:<skill> с границами токена: skill `api`
    не находится в `skills/api-reference/` и `p-dev:api-reference`. Команда не берётся в alias, если
    - её имя совпадает с именем ЛЮБОГО skill плагина: вход Skill {"skill":"<плагин>:<имя>"} один и тот же
      для skill и для команды, и по нему не отличить, что сработало;
    - она ведёт к более чем MAX_ROUTES_PER_COMMAND skills: это хаб (check, update, optimize), его запуск
      не говорит ничего о конкретном skill и проваливал бы «не должен срабатывать» у каждого.
    Списки отсортированы, у skill без команд ключа нет."""
    commands = os.path.join(plugin_dir, "commands")
    if not os.path.isdir(commands):
        return {}
    skills = [s.name for s in evalsrc.skills(plugin_dir)]
    routes = {}
    for entry in sorted(os.listdir(commands)):
        command, ext = os.path.splitext(entry)
        if ext != ".md" or command in skills or not os.path.isfile(os.path.join(commands, entry)):
            continue
        with open(os.path.join(commands, entry), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        named = [skill for skill in skills if _names_skill(text, plugin_name, skill)]
        if len(named) > MAX_ROUTES_PER_COMMAND:
            continue
        for skill in named:
            routes.setdefault(skill, []).append(command)
    return {skill: sorted(routes[skill]) for skill in sorted(routes)}


def _names_skill(text, plugin_name, skill):
    start, end = r"(?<![A-Za-z0-9_.-])", r"(?![A-Za-z0-9_-])"
    return bool(re.search(start + r"skills/" + re.escape(skill) + "/", text)
                or re.search(start + re.escape(plugin_name) + ":" + re.escape(skill) + end, text))


def _strip_manifest_keys(dest, keys):
    """Убрать keys из plugin.json КОПИИ. Файл без этих ключей, нечитаемый, не объект или лежащий вне копии
    не трогается; ссылка заменяется обычным файлом — запись сквозь неё изменила бы источник."""
    path = os.path.join(dest, ".claude-plugin", "plugin.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError, RecursionError):
        return
    if not isinstance(data, dict) or not any(key in data for key in keys):
        return
    if not (os.path.realpath(os.path.dirname(path)) + os.sep).startswith(os.path.realpath(dest) + os.sep):
        return
    for key in keys:
        data.pop(key, None)
    if os.path.islink(path):
        os.remove(path)
    _write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _remove_agents(dest):
    """Каталог agents/ копии (ссылку — саму ссылку, не её цель)."""
    path = os.path.join(dest, "agents")
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def copy_plugin(plugin_dir, dest, drop_agents=False):
    """Временная копия плагина для eval. В ней нет GENERATED-деревьев, .git и ключа dependencies в plugin.json:
    с ним плагин в песочнице не грузится. drop_agents — без agents/ и без ключа agents: агенты плагина
    предлагаются модели через Agent, забирают единственный ход срабатывания у Skill и портят ответы качества
    (L2 меряет skills); behavior всегда копирует с drop_agents=True."""
    shutil.copytree(plugin_dir, dest, symlinks=True, ignore=shutil.ignore_patterns(".git", *GENERATED))
    _strip_manifest_keys(dest, ("dependencies", "agents") if drop_agents else ("dependencies",))
    if drop_agents:
        _remove_agents(dest)
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


def write_triggers(copy_dir, eval_dir, plugin_name, queries, only=None, routes=None):
    """Кейсы срабатывания в <копия>/<eval_dir>/; only — подмножество имён (повтор); routes — skill_routes
    (команда, ведущая к skill, засчитывается как его срабатывание). → {имя: запрос}."""
    routes = routes or {}
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
            [("type", "tool_used"), ("tool", "Skill"),
             ("input_match", input_match(plugin_name, q.skill, routes.get(q.skill, [])))]
            + bounds + [("arm", "both")]))
    os.makedirs(root, exist_ok=True)
    return out


def write_quality(copy_dir, plugin_name, cases, invocable, mocks, native_root="", native_names=(), routes=None):
    """Кейсы качества, моки MCP и родной набор в <копия>/evals-quality/. → {имя: {kind, skill, id}}.
    routes — skill_routes: индикатор fired.md засчитывает и команду, ведущую к skill."""
    routes = routes or {}
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
                [("type", "tool_used"), ("tool", "Skill"),
                 ("input_match", input_match(plugin_name, c.skill, routes.get(c.skill, []))), ("arm", "with-only")]))
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
