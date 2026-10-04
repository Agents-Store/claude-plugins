"""MCP-серверы плагина: .mcp.json ({"mcpServers": {...}} или плоская карта) и plugin.json."""
from __future__ import annotations

import json
import os


class McpConfigError(ValueError):
    """.mcp.json (или файл, на который ссылается plugin.json) не читается."""

    def __init__(self, path, msg):
        super().__init__("%s: %s" % (path, msg))
        self.path = path
        self.msg = msg


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:  # JSONDecodeError и UnicodeDecodeError
        raise McpConfigError(path, "не JSON: %s" % exc) from exc
    except OSError as exc:
        raise McpConfigError(path, "не читается: %s" % (exc.strerror or type(exc).__name__)) from exc


def _servers_of(data):
    if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict):
        data = data["mcpServers"]
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def servers(plugin):
    out = {}
    meta_path = os.path.join(plugin.dir, ".claude-plugin", "plugin.json")
    try:
        ref = _load(meta_path).get("mcpServers")
    except (McpConfigError, AttributeError):  # битый plugin.json — дело проверки manifest
        ref = None
    if isinstance(ref, dict):
        out.update(_servers_of(ref))
    elif isinstance(ref, str) and os.path.isfile(os.path.join(plugin.dir, ref)):
        out.update(_servers_of(_load(os.path.join(plugin.dir, ref))))
    path = os.path.join(plugin.dir, ".mcp.json")
    if os.path.isfile(path):
        out.update(_servers_of(_load(path)))
    return out
