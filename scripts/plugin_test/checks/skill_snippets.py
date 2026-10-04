"""skill-snippets: json / yaml / bash блоки кода в Markdown разбираются (spec §5)."""
from __future__ import annotations

import json
import os
import re
import subprocess

from ..markdown import blocks, iter_markdown, read
from ..model import CHECK_TIMEOUT, FAIL, INFRA, Finding

try:
    import yaml
except ImportError:  # CI ставит PyYAML; без него yaml-блоки — одна находка infra
    yaml = None

CHECK = "skill-snippets"
SHELL = {"bash", "sh", "shell"}
RE_PLACEHOLDER = re.compile(r"(?<!<)<(?![<(])([A-Za-z][^<>\n]{0,120})>")
RE_BASH_LINE = re.compile(r"line (\d+):")
SKIP_HINT = "намеренно неполный пример — поставь <!-- plugin-test: skip --> строкой выше блока"


def run(plugin, ctx, manifest):
    out = []
    yaml_reported = False
    for path in iter_markdown(plugin.dir):
        rel = plugin.rel(path)
        for b in blocks(read(path)):
            if b.skip:
                continue
            if b.info == "json":
                out.extend(_json(plugin, b, rel))
            elif b.info in ("yaml", "yml"):
                if yaml is None:
                    if not yaml_reported:
                        out.append(Finding(plugin.name, CHECK, INFRA, "PyYAML не установлен — yaml-блоки не проверены",
                                           fix="python3 -m pip install 'PyYAML>=6,<7'"))
                        yaml_reported = True
                    continue
                out.extend(_yaml(plugin, b, rel))
            elif b.info in SHELL:
                out.extend(_bash(plugin, b, rel))
    return out


def _json(plugin, b, rel):
    if not b.body.strip():
        return []
    try:
        json.loads(b.body)
    except json.JSONDecodeError as exc:
        return [Finding(plugin.name, CHECK, FAIL, "json-блок не парсится: %s" % exc.msg, rel,
                        b.line + exc.lineno - 1,
                        "исправь JSON; пример с комментариями или «...» помечай ```jsonc; " + SKIP_HINT)]
    return []


def _yaml(plugin, b, rel):
    try:
        list(yaml.safe_load_all(b.body))
    except (yaml.YAMLError, ValueError) as exc:  # ValueError — невозможная дата вроде 2024-13-45, без problem_mark
        mark = getattr(exc, "problem_mark", None)
        problem = getattr(exc, "problem", None) or str(exc).split("\n")[0]
        return [Finding(plugin.name, CHECK, FAIL, "yaml-блок не парсится: %s" % problem, rel,
                        b.line + (mark.line if mark else 0),
                        "исправь YAML; шаблон (Helm, {{ }}) — " + SKIP_HINT)]
    return []


def _bash_n(body):
    return subprocess.run(["bash", "-n"], input=body, capture_output=True, text=True,
                          env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")}, timeout=CHECK_TIMEOUT)


def _bash(plugin, b, rel):
    if any(line.startswith("$ ") for line in b.body.split("\n")):
        return []  # транскрипт сессии, а не скрипт
    try:
        proc = _bash_n(b.body)  # сначала как есть: подстановка плейсхолдеров сама ломает кавычки
        if proc.returncode == 0:
            return []
        proc = _bash_n(RE_PLACEHOLDER.sub("PLACEHOLDER", b.body))
    except subprocess.TimeoutExpired:
        return [Finding(plugin.name, CHECK, INFRA, "bash -n не уложился в %d с" % CHECK_TIMEOUT, rel, b.line)]
    if proc.returncode == 0:
        return []
    err = (proc.stderr.strip().split("\n") or [""])[0]
    m = RE_BASH_LINE.search(err)
    detail = err.split(":", 2)[-1].strip() if m else err
    return [Finding(plugin.name, CHECK, FAIL, "bash-блок не проходит bash -n: %s" % detail, rel,
                    b.line + (int(m.group(1)) - 1 if m else 0),
                    "исправь синтаксис; не-bash помечай своим языком (```text, ```console, ```powershell); " + SKIP_HINT)]
