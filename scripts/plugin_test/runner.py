"""Прогон проверок одного плагина: манифест, [skip], падение проверки → infra."""
from __future__ import annotations

import fnmatch
import os

from . import manifest as manifest_mod
from .checks import REGISTRY
from .model import INFRA, Finding


def skipped_by(finding, plugin, globs):
    """Глоб [skip] — путь от каталога плагина; находка без файла снимается только "*"."""
    if not finding.file:
        return "*" in globs
    rel = os.path.relpath(os.path.join(plugin.repo, finding.file), plugin.dir)
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def run_plugin(plugin, ctx, checks):
    loaded, findings = manifest_mod.load(plugin)
    findings = list(findings)
    suppressed = 0
    for cid in checks:
        fn = REGISTRY.get(cid)
        if fn is None:
            continue
        try:
            got = list(fn(plugin, ctx, loaded))
        except Exception as exc:  # одна сломанная проверка не роняет прогон
            got = [Finding(plugin.name, cid, INFRA, "проверка упала: %s: %s" % (type(exc).__name__, exc),
                           fix="это дефект runner-а: заведи задачу с этим текстом")]
        globs = loaded.skip.get(cid, [])
        for f in got:
            if globs and skipped_by(f, plugin, globs):
                suppressed += 1
            else:
                findings.append(f)
    return findings, suppressed
