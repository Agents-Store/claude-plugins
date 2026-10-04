"""hook-fixtures: command-hooks плагина на фикстурах tests/plugins/<p>/hooks/*.json (spec §5)."""
from __future__ import annotations

import glob
import json
import os
import subprocess
import tempfile

from ..model import CHECK_TIMEOUT, FAIL, SKIPPED, Finding
from ..proc import run_group

CHECK = "hook-fixtures"
NO_FIELD = "<нет поля>"


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def hooks_config(plugin):
    meta = _load_json(os.path.join(plugin.dir, ".claude-plugin", "plugin.json"))
    ref = meta.get("hooks") if isinstance(meta, dict) else None
    if isinstance(ref, dict):
        data = ref
    else:
        rel = ref if isinstance(ref, str) else os.path.join("hooks", "hooks.json")
        data = _load_json(os.path.join(plugin.dir, rel)) or {}
    hooks = data.get("hooks", data) if isinstance(data, dict) else {}
    return hooks if isinstance(hooks, dict) else {}


def run(plugin, ctx, manifest):
    fixtures = sorted(glob.glob(os.path.join(plugin.tests_dir, "hooks", "*.json")))
    if not fixtures:
        return []
    config = hooks_config(plugin)
    out = []
    for path in fixtures:
        try:
            out.extend(_fixture(plugin, config, path))
        except Exception as exc:  # одна кривая фикстура не должна прятать остальные
            out.append(Finding(plugin.name, CHECK, FAIL, "фикстура не обработана: %s" % type(exc).__name__,
                               plugin.rel(path), 0, "формат — tests/README.md, раздел «Фикстуры hooks»"))
    return out


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _field_problems(fx):
    """Типы полей фикстуры: по одной находке на нарушение, с именем поля."""
    problems = []
    if not isinstance(fx.get("event"), str):
        problems.append("event должен быть строкой, получено %r" % (fx.get("event"),))
    if "stdin" in fx and not isinstance(fx["stdin"], dict):
        problems.append("stdin должен быть объектом, получено %r" % (fx["stdin"],))
    if "expect" not in fx:
        return problems
    expect = fx["expect"]
    if not isinstance(expect, dict):
        return problems + ["expect должен быть объектом, получено %r" % (expect,)]
    if "exit" in expect and not _is_int(expect["exit"]):
        problems.append("expect.exit должен быть целым числом, получено %r" % (expect["exit"],))
    if "json" in expect and not isinstance(expect["json"], dict):
        problems.append("expect.json должен быть объектом «путь.через.точку: значение», получено %r" % (expect["json"],))
    if "stdout_contains" in expect and not isinstance(expect["stdout_contains"], str):
        problems.append("expect.stdout_contains должен быть строкой, получено %r" % (expect["stdout_contains"],))
    if "stdout_empty" in expect and not isinstance(expect["stdout_empty"], bool):
        problems.append("expect.stdout_empty должен быть true или false, получено %r" % (expect["stdout_empty"],))
    return problems


def _fixture(plugin, config, path):
    rel = plugin.rel(path)
    format_fix = "формат — tests/README.md, раздел «Фикстуры hooks»"

    def fail(message, fix="", level=FAIL):
        return [Finding(plugin.name, CHECK, level, message, rel, 0, fix)]

    fx = _load_json(path)
    if not isinstance(fx, dict):
        return fail("фикстура не JSON-объект", format_fix)
    problems = _field_problems(fx)
    if problems:
        return [f for message in problems for f in fail(message, format_fix)]
    event = fx["event"]
    entries = config.get(event) or []
    if not isinstance(entries, list) or not entries:
        return fail("в hooks.json нет события %r" % event, "event фикстуры — ключ в hooks.json")
    if "matcher" in fx:
        entries = [e for e in entries if isinstance(e, dict) and e.get("matcher", "") == fx["matcher"]]
        if not entries:
            return fail("у события %s нет записи с matcher %r" % (event, fx["matcher"]),
                        "matcher фикстуры должен буквально совпадать с matcher в hooks.json")
    elif len(entries) > 1:
        return fail("у события %s записей: %d — укажи matcher" % (event, len(entries)))
    if not isinstance(entries[0], dict):
        return fail("запись события %s в hooks.json — не объект" % event)
    hooks = entries[0].get("hooks") or []
    index = fx.get("index", 0)
    if not isinstance(hooks, list) or not _is_int(index) or not 0 <= index < len(hooks):
        return fail("в записи нет hook-а с index %r" % (index,))
    hook = hooks[index]
    if not isinstance(hook, dict):
        return fail("hook %d события %s в hooks.json — не объект" % (index, event))
    if hook.get("type") != "command":
        return fail("hook типа %r локально не запускается" % hook.get("type"), level=SKIPPED)
    command = hook.get("command")
    if not isinstance(command, str) or not command.strip():
        return fail("у command-hook-а нет непустого command", "command — строка в hooks.json")
    timeout = hook.get("timeout", CHECK_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not timeout > 0:
        return fail("timeout hook-а должен быть положительным числом, получено %r" % (timeout,),
                    "timeout — секунды, число больше нуля")
    timeout = min(timeout, CHECK_TIMEOUT)
    with tempfile.TemporaryDirectory() as tmp:
        project, home = os.path.join(tmp, "project"), os.path.join(tmp, "home")
        os.makedirs(project)
        os.makedirs(home)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home,
               "CLAUDE_PLUGIN_ROOT": plugin.dir, "CLAUDE_PROJECT_DIR": project}
        stdin = dict(fx.get("stdin", {}))
        stdin.setdefault("cwd", project)
        try:
            proc = run_group(["bash", "-c", command], input=json.dumps(stdin), env=env, cwd=project,
                             timeout=timeout)
        except subprocess.TimeoutExpired:
            return fail("hook не завершился за %g с" % timeout, "hook обязан укладываться в свой timeout")
    out = []
    for message in _compare(fx.get("expect", {}), proc):
        out.extend(fail(message))
    return out


def _dig(data, dotted):
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return NO_FIELD
        cur = cur[part]
    return cur


def _compare(expect, proc):
    problems = []
    want = expect.get("exit", 0)
    if proc.returncode != want:
        problems.append("код выхода %d, ожидался %d; stderr: %s" % (proc.returncode, want, proc.stderr.strip()[-200:]))
    stdout = proc.stdout.strip()
    if expect.get("stdout_empty") and stdout:
        problems.append("ожидался пустой stdout, получено: %s" % stdout[:200])
    if "stdout_contains" in expect and expect["stdout_contains"] not in stdout:
        problems.append("в stdout нет %r" % expect["stdout_contains"])
    if expect.get("json"):
        try:
            data = json.loads(stdout)
        except ValueError:
            return problems + ["stdout не JSON: %s" % stdout[:200]]
        for dotted, value in expect["json"].items():
            got = _dig(data, dotted)
            if got != value:
                problems.append("%s = %r, ожидалось %r" % (dotted, got, value))
    return problems
