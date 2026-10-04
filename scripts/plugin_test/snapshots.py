"""Снимки реальности в tests/plugins/<каталог>/snapshots/.

mcp/<server>.tools.json — ответ tools/list в формате, который `claude plugin eval`
принимает как `_tools.json` для заглушек MCP (spec §4.2, §10): {"tools": [{name,
description, inputSchema}]}, по имени, без полей, меняющихся от запуска к запуску.
cli/<tool>.json — дерево --help: {tool, version, global, subcommands, commands}.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass


class SnapshotError(ValueError):
    def __init__(self, path, msg):
        super().__init__("%s: %s" % (path, msg))
        self.path = path
        self.msg = msg


def mcp_path(plugin, server):
    return os.path.join(plugin.tests_dir, "snapshots", "mcp", "%s.tools.json" % server)


def cli_path(plugin, tool):
    return os.path.join(plugin.tests_dir, "snapshots", "cli", "%s.json" % tool)


def _sort_required(schema):
    if isinstance(schema, dict):
        return {k: sorted(v) if k == "required" and isinstance(v, list) and all(isinstance(x, str) for x in v)
                else _sort_required(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_sort_required(x) for x in schema]
    return schema


def normalize_tools(tools):
    out = []
    for t in tools:
        if not isinstance(t, dict) or not isinstance(t.get("name"), str):
            continue
        out.append({"name": t["name"], "description": t.get("description") or "",
                    "inputSchema": _sort_required(t.get("inputSchema") or {"type": "object"})})
    return {"tools": sorted(out, key=lambda t: t["name"])}


def _read(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        raise SnapshotError(path, "не JSON: %s" % exc) from exc


def load(path):
    data = _read(path)
    if data is None:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("tools"), list) \
            or not all(isinstance(t, dict) and isinstance(t.get("name"), str) for t in data["tools"]):
        raise SnapshotError(path, "ожидался объект {\"tools\": [{\"name\": …}]}")
    return data


def _strings(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def load_cli(path):
    data = _read(path)
    if data is None:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("commands"), dict):
        raise SnapshotError(path, "ожидался объект с картой commands")
    for key in ("global", "subcommands"):
        if key in data and not _strings(data[key]):
            raise SnapshotError(path, "%s — ожидался список строк" % key)
    for key in ("commands", "children"):
        value = data.get(key, {})
        if not isinstance(value, dict) or not all(_strings(v) for v in value.values()):
            raise SnapshotError(path, "%s — ожидалась карта команда → список строк" % key)
    return data


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def required_of(tool):
    req = (tool.get("inputSchema") or {}).get("required") or []
    return sorted(req) if isinstance(req, list) else []


def names_only(data):
    """Снимок без описаний и схем — для серверов, чей tools/list зависит от данных инстанса."""
    return {"tools": [{"name": t["name"], "description": "",
                       "inputSchema": {"type": "object", "required": required_of(t)}} for t in data["tools"]]}


@dataclass
class ToolDiff:
    missing: list              # были в снимке, на сервере пропали
    extra: list                # новые на сервере
    required_changed: list     # [(имя, было, стало)]
    description_changed: list


def diff_tools(old, new):
    o = {t["name"]: t for t in old["tools"]}
    n = {t["name"]: t for t in new["tools"]}
    required, described = [], []
    for name in sorted(set(o) & set(n)):
        if required_of(o[name]) != required_of(n[name]):
            required.append((name, required_of(o[name]), required_of(n[name])))
        if (o[name].get("description") or "") != (n[name].get("description") or ""):
            described.append(name)
    return ToolDiff(sorted(set(o) - set(n)), sorted(set(n) - set(o)), required, described)
