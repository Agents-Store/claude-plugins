"""mcp-list: запустить MCP-сервер плагина, снять tools/list, сравнить со снимком (spec §5)."""
from __future__ import annotations

import os
import tempfile

from .. import envfile, snapshots
from ..mcp_client import McpError, list_tools_http, list_tools_stdio
from ..mcp_config import McpConfigError
from ..mcp_config import servers as mcp_servers
from ..model import CI, FAIL, INFO, INFRA, MCP_START_TIMEOUT, SERVER, SKIPPED, WARN, Finding
from ..report import Redactor

CHECK = "mcp-list"


def run(plugin, ctx, manifest):
    try:
        configured = mcp_servers(plugin)
    except McpConfigError as exc:
        return [Finding(plugin.name, CHECK, FAIL, "MCP-конфиг не читается: %s" % exc.msg,
                        plugin.rel(exc.path), 0, "исправь JSON в .mcp.json")]
    out = []
    for name, cfg in sorted(configured.items()):
        out.extend(_server(plugin, ctx, manifest.mcp_spec(name), name, cfg))
    return out


def _server(plugin, ctx, spec, name, cfg):
    snap_path = snapshots.mcp_path(plugin, name)
    rel_snap = plugin.rel(snap_path)

    def finding(level, message, fix="", file=""):
        return Finding(plugin.name, CHECK, level, "сервер %s: %s" % (name, message), file, 0, fix)

    kind = "http" if cfg.get("type") in ("http", "sse") or "url" in cfg else "stdio"
    if spec.start == "never":
        return [finding(SKIPPED, "start = never")]
    if cfg.get("type") == "sse":
        return [finding(SKIPPED, "транспорт sse не поддержан")]
    if ctx.mode == CI and not (kind == "stdio" and spec.start == "ci"):
        return [finding(SKIPPED, "только в режиме server")]

    values = {}
    if ctx.mode == SERVER:
        values.update(spec.env)
        values.update(ctx.env)
    else:
        values.update(spec.env)
    values["CLAUDE_PLUGIN_ROOT"] = plugin.dir
    expanded, missing = envfile.expand_obj(cfg, values)
    if missing:
        if ctx.mode == SERVER:
            return [finding(INFRA, "нет значения для %s" % ", ".join(missing), "добавь переменные в env-файл сервера")]
        return [finding(WARN, "нет значения для %s" % ", ".join(missing),
                        "добавь фиктивные значения в [mcp.%s].env файла plugin-test.toml" % name)]

    try:
        try:
            tools = _list(kind, expanded, plugin)
        except McpError as first:
            if first.kind != "infra":
                return [finding(FAIL, str(first), "проверь команду, аргументы и URL сервера в .mcp.json")]
            try:
                tools = _list(kind, expanded, plugin)  # spec §6: старт повторяется один раз
            except McpError as exc:
                return [finding(INFRA if exc.kind == "infra" else FAIL, str(exc))]
    except Exception as exc:  # noqa: BLE001 — клиент упал не по протоколу (RecursionError и т.п.): остальные серверы идут дальше
        return [finding(INFRA, "клиент упал: %s" % type(exc).__name__)]

    redactor = Redactor(ctx.env)
    current = redactor.obj(snapshots.normalize_tools(tools))
    if spec.snapshot == "names":
        current = snapshots.names_only(current)
    if ctx.update_snapshots:
        snapshots.write(snap_path, current)
        return [finding(INFO, "снимок записан, инструментов: %d" % len(current["tools"]), file=rel_snap)]
    try:
        old = snapshots.load(snap_path)
    except snapshots.SnapshotError as exc:
        return [finding(FAIL, "снимок не читается: %s" % exc.msg, "перезапиши: --update-snapshots", rel_snap)]
    if old is None:
        return [finding(WARN, "отвечает (инструментов: %d), но снимка нет" % len(current["tools"]),
                        "сними: --update-snapshots", rel_snap)]
    d = snapshots.diff_tools(old, current)
    out = []
    if d.missing:
        out.append(finding(FAIL, "пропали инструменты: %s" % ", ".join(d.missing),
                           "убери их из skills и обнови снимок (--update-snapshots)", rel_snap))
    for tool, was, now in d.required_changed:
        out.append(finding(FAIL, "%s: обязательные параметры %s → %s" % (tool, was, now),
                           "обнови примеры вызова в skills и снимок", rel_snap))
    if d.extra:
        out.append(finding(WARN, "новые инструменты: %s" % ", ".join(d.extra), "обнови снимок (--update-snapshots)", rel_snap))
    if d.description_changed:
        shown = ", ".join(d.description_changed[:10])
        out.append(finding(WARN, "изменились описания: %s" % shown, "обнови снимок (--update-snapshots)", rel_snap))
    return out


def _list(kind, cfg, plugin):
    if kind == "http":
        headers = {k: str(v) for k, v in (cfg.get("headers") or {}).items()}
        return list_tools_http(cfg["url"], headers, MCP_START_TIMEOUT)
    with tempfile.TemporaryDirectory() as home:
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home}
        env.update({k: str(v) for k, v in (cfg.get("env") or {}).items()})
        args = [str(a) for a in cfg.get("args") or []]
        return list_tools_stdio(cfg["command"], args, env, plugin.dir, MCP_START_TIMEOUT)
