"""Разбор .env и подстановка ${VAR} / ${VAR:-default} — как Claude Code в .mcp.json.

Значения отсюда никогда не печатаются: вызывающий код получает их только для
передачи в процесс проверки, а в отчёт они попадают через report.Redactor.
"""
import re

RE_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
RE_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse(text):
    env = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not RE_KEY.fullmatch(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0]
        env[key] = value
    return env


def load(path):
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read())


def expand(text, env):
    """(строка с подстановками, [имена без значения и без default])."""
    missing = []

    def sub(m):
        name, default = m.group(1), m.group(2)
        if env.get(name):
            return env[name]
        if default is not None:
            return default
        missing.append(name)
        return ""

    return RE_VAR.sub(sub, text), missing


def expand_obj(obj, env):
    """expand() по всем строкам вложенных dict/list → (копия, отсортированные missing)."""
    missing = []

    def walk(o):
        if isinstance(o, str):
            s, miss = expand(o, env)
            missing.extend(miss)
            return s
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        return o

    return walk(obj), sorted(set(missing))
