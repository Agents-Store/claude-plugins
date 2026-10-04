"""skill-budget: всегда-загружаемые токены плагина и длина SKILL.md — только warn (spec §5)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

from ..model import CHECK_TIMEOUT, INFRA, WARN, Finding

CHECK = "skill-budget"
MAX_SKILL_LINES = 500
RE_ALWAYS_ON = re.compile(r"Always-on:\s*~?([\d.,]+)\s*(k)?\s*tok", re.I)


def parse_tokens(text):
    m = RE_ALWAYS_ON.search(text or "")
    if not m:
        return None
    number = float(m.group(1).replace(",", ""))
    return int(round(number * 1000)) if m.group(2) else int(number)


def run(plugin, ctx, manifest):
    out = []
    skills = os.path.join(plugin.dir, "skills")
    if os.path.isdir(skills):
        for d in sorted(os.listdir(skills)):
            path = os.path.join(skills, d, "SKILL.md")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                count = sum(1 for _ in fh)
            if count > MAX_SKILL_LINES:
                out.append(Finding(plugin.name, CHECK, WARN, "SKILL.md — %d строк (> %d)" % (count, MAX_SKILL_LINES),
                                   plugin.rel(path), 0,
                                   "вынеси детали в references/: SKILL.md грузится целиком при каждом вызове"))
    out.extend(_always_on(plugin, manifest))
    return out


def _always_on(plugin, manifest):
    claude = shutil.which("claude")
    if not claude:
        return [Finding(plugin.name, CHECK, INFRA, "нет CLI claude — бюджет токенов не посчитан",
                        fix="npm install -g @anthropic-ai/claude-code")]
    with tempfile.TemporaryDirectory() as home:
        try:
            proc = subprocess.run([claude, "--plugin-dir", plugin.dir, "plugin", "details", plugin.name],
                                  capture_output=True, text=True, timeout=CHECK_TIMEOUT, cwd=home,
                                  env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home})
        except subprocess.TimeoutExpired:
            return [Finding(plugin.name, CHECK, INFRA, "claude plugin details не ответил за %d с" % CHECK_TIMEOUT)]
    tokens = parse_tokens(proc.stdout)
    if tokens is None:
        return [Finding(plugin.name, CHECK, INFRA,
                        "в выводе claude plugin details нет строки Always-on (код %d)" % proc.returncode,
                        fix="формат вывода CLI изменился — обнови RE_ALWAYS_ON")]
    if tokens > manifest.always_on_tokens:
        meta = os.path.join(plugin.dir, ".claude-plugin", "plugin.json")
        return [Finding(plugin.name, CHECK, WARN,
                        "всегда-загружаемая часть плагина ~%d токенов (> %d)" % (tokens, manifest.always_on_tokens),
                        plugin.rel(meta), 0,
                        "сократи description у skills, агентов и команд или подними [budget] always_on_tokens с причиной")]
    return []
