"""mcp-names: каждое mcp__plugin_<плагин>_<сервер>__<инструмент> есть в снимке сервера (spec §5)."""
from __future__ import annotations

import difflib
import re

from .. import snapshots
from ..markdown import iter_markdown, read
from ..mcp_config import servers as mcp_servers
from ..model import FAIL, SKIPPED, Finding

CHECK = "mcp-names"
RE_NAME = re.compile(r"mcp__plugin_([a-z0-9][a-z0-9-]*)_([A-Za-z0-9-]+)__([A-Za-z0-9_.-]*)([*<{])?")


def run(plugin, ctx, manifest):
    allowed = {plugin.name, *plugin.dependencies}
    state = {}
    reported = set()
    out = []
    for path in iter_markdown(plugin.dir):
        rel = plugin.rel(path)
        for n, line in enumerate(read(path).split("\n"), 1):
            for m in RE_NAME.finditer(line):
                owner, server, tool, tail = m.group(1), m.group(2), m.group(3).rstrip(".-"), m.group(4)
                if not tool or tail:
                    continue
                if owner not in allowed:
                    out.append(Finding(plugin.name, CHECK, FAIL,
                                       "инструмент плагина %s, которого нет в dependencies: %s" % (owner, m.group(0)),
                                       rel, n, "добавь %s в dependencies plugin.json или возьми сервер своего плагина" % owner))
                    continue
                key = (owner, server)
                if key not in state:
                    state[key] = _snapshot(ctx, owner, server)
                kind, payload = state[key]
                if kind == "no-server":
                    out.append(Finding(plugin.name, CHECK, FAIL, "у плагина %s нет MCP-сервера %r" % (owner, server),
                                       rel, n, "имя сервера — ключ в .mcp.json плагина %s" % owner))
                elif kind in ("no-snapshot", "bad-snapshot"):
                    if key not in reported:
                        reported.add(key)
                        out.append(payload)
                elif tool not in payload:
                    close = difflib.get_close_matches(tool, sorted(payload), n=3)
                    out.append(Finding(plugin.name, CHECK, FAIL, "у сервера %s нет инструмента %r" % (server, tool),
                                       rel, n, "похожие: %s" % ", ".join(close) if close
                                       else "сверь со снимком tests/plugins/%s/snapshots/mcp/%s.tools.json" % (owner, server)))
    return out


def _snapshot(ctx, owner_name, server):
    owner = ctx.catalog.plugins.get(owner_name)
    if owner is None or server not in mcp_servers(owner):
        return "no-server", None
    path = snapshots.mcp_path(owner, server)
    try:
        data = snapshots.load(path)
    except snapshots.SnapshotError as exc:
        return "bad-snapshot", Finding(owner_name, CHECK, FAIL, "снимок не читается: %s" % exc.msg,
                                       owner.rel(path), 0, "перезапиши снимок: --mode server --update-snapshots")
    if data is None:
        return "no-snapshot", Finding(owner_name, CHECK, SKIPPED,
                                      "нет снимка tools/list сервера %s плагина %s" % (server, owner_name),
                                      fix="сними: plugin_test.py --mode server --env-file … --plugin %s "
                                          "--check mcp-list --update-snapshots" % owner_name)
    return "ok", {t["name"] for t in data["tools"]}
