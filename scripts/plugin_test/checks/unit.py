"""unit: собственные тесты плагина из [[unit]] манифеста (spec §5).

Тестам не нужен ни один секрет: окружение — PATH, временный HOME, LANG и CI=1.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from ..model import FAIL, INFRA, Finding
from ..proc import run_group

CHECK = "unit"
TAIL_LINES = 20


def run(plugin, ctx, manifest):
    out = []
    for spec in manifest.unit:
        label = spec.name or spec.run
        missing = [n for n in spec.needs if not shutil.which(n)]
        if missing:
            out.append(Finding(plugin.name, CHECK, INFRA, "%s: нет %s" % (label, ", ".join(missing)),
                               fix="поставь toolchain (в CI — шаг setup в plugin-test.yml)"))
            continue
        cwd = os.path.join(plugin.repo, spec.cwd) if spec.cwd else plugin.dir
        if not os.path.isdir(cwd):
            out.append(Finding(plugin.name, CHECK, FAIL, "%s: нет каталога %s" % (label, spec.cwd),
                               fix="cwd в [[unit]] — путь от корня репозитория"))
            continue
        with tempfile.TemporaryDirectory() as home:
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home, "LANG": "C.UTF-8", "CI": "1"}
            try:
                done = run_group(["bash", "-c", spec.run], env=env, cwd=cwd, timeout=spec.timeout)
            except subprocess.TimeoutExpired:
                out.append(Finding(plugin.name, CHECK, FAIL, "%s: не завершился за %d с" % (label, spec.timeout),
                                   fix="ускорь тесты или подними timeout в [[unit]]"))
                continue
        if done.returncode != 0:
            tail = "\n".join((done.stdout + done.stderr).strip().split("\n")[-TAIL_LINES:])
            out.append(Finding(plugin.name, CHECK, FAIL, "%s: код %d\n%s" % (label, done.returncode, tail),
                               fix="локально: cd %s && %s" % (os.path.relpath(cwd, plugin.repo), spec.run)))
    return out
