"""MCP-серверы плагина: .mcp.json ({"mcpServers": {...}} или плоская карта) и plugin.json."""
from __future__ import annotations

import json
import os


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


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
    except (OSError, ValueError, AttributeError):
        ref = None
    if isinstance(ref, dict):
        out.update(_servers_of(ref))
    elif isinstance(ref, str) and os.path.isfile(os.path.join(plugin.dir, ref)):
        out.update(_servers_of(_load(os.path.join(plugin.dir, ref))))
    path = os.path.join(plugin.dir, ".mcp.json")
    if os.path.isfile(path):
        out.update(_servers_of(_load(path)))
    return out
