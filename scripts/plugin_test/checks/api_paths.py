"""api-paths: метод и путь curl-рецептов есть в OpenAPI-спецификации (opt-in, spec §5)."""
from __future__ import annotations

import json
import os
import re

from ..markdown import blocks, iter_markdown, read
from ..model import FAIL, Finding
from ..shell import commands, logical_lines, strip_prefix

CHECK = "api-paths"
SHELL = {"bash", "sh", "shell"}
METHODS = ("get", "put", "post", "delete", "patch", "head", "options")
DATA_FLAGS = {"-d", "--data", "--data-raw", "--data-binary", "--data-urlencode",
              "-F", "--form", "--json", "-T", "--upload-file"}


def load_spec(path):
    with open(path, encoding="utf-8") as fh:
        if path.endswith((".yaml", ".yml")):
            import yaml
            data = yaml.safe_load(fh)
        else:
            data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("спецификация — не объект")
    prefixes = {""}
    for server in data.get("servers") or []:
        url = server.get("url", "") if isinstance(server, dict) else ""
        p = re.sub(r"^[a-z][a-z0-9+.-]*://[^/]*", "", url).rstrip("/")
        if p.startswith("/"):
            prefixes.add(p)
    if isinstance(data.get("basePath"), str):
        prefixes.add(data["basePath"].rstrip("/"))
    paths = []
    for p, item in (data.get("paths") or {}).items():
        if isinstance(item, dict):
            segments = p.rstrip("/").split("/") if p.strip("/") else [""]
            paths.append((segments, {m.upper() for m in item if m in METHODS}))
    return sorted(prefixes), paths


def method_of(tokens):
    method, has_data, get, head = None, False, False, False
    for i, t in enumerate(tokens):
        if t in ("-X", "--request") and i + 1 < len(tokens):
            method = tokens[i + 1].upper()
        elif t.startswith("-X") and len(t) > 2:
            method = t[2:].upper()
        elif t.startswith("--request="):
            method = t.split("=", 1)[1].upper()
        elif t in DATA_FLAGS or t.split("=", 1)[0] in DATA_FLAGS:
            has_data = True
        elif t in ("-G", "--get"):
            get = True
        elif t in ("-I", "--head"):
            head = True
    if method:
        return method
    if head:
        return "HEAD"
    if get:
        return "GET"
    return "POST" if has_data else "GET"


def url_path(tokens, base_vars):
    for t in tokens:
        for var, prefix in base_vars.items():
            m = re.search(r"\$\{?%s\}?(?![A-Za-z0-9_])(/[^?#\s\"')]*)?" % re.escape(var), t)
            if m:
                return var, prefix + (m.group(1) or "")
    return None, None


def match(path, prefixes, paths):
    segs = path.rstrip("/").split("/") if path.strip("/") else [""]
    found, methods = False, set()
    for prefix in prefixes:
        pre = prefix.split("/") if prefix else []
        if pre and segs[:len(pre)] != pre:
            continue
        rest = [""] + segs[len(pre):] if pre else segs
        for spec_segs, spec_methods in paths:
            if len(spec_segs) == len(rest) and all(s.startswith("{") or s == r for s, r in zip(spec_segs, rest)):
                found = True
                methods |= spec_methods
    return found, methods


def run(plugin, ctx, manifest):
    if not manifest.api:
        return []
    out, specs = [], []
    for api in manifest.api:
        path = os.path.join(plugin.dir, api.spec)
        try:
            prefixes, paths = load_spec(path)
        except (OSError, ValueError, ImportError) as exc:
            out.append(Finding(plugin.name, CHECK, FAIL, "спецификация не читается: %s" % exc,
                               plugin.rel(path), 0, "проверь путь [api].spec и формат файла"))
            continue
        specs.append((api, prefixes, paths, os.path.basename(api.spec)))
    if not specs:
        return out
    for md in iter_markdown(plugin.dir):
        rel = plugin.rel(md)
        for b in blocks(read(md)):
            if b.skip or b.info not in SHELL:
                continue
            for offset, line in logical_lines(b.body):
                for tokens in commands(line):
                    tokens = strip_prefix(tokens)
                    if tokens and tokens[0] == "curl":
                        out.extend(_curl(plugin, specs, tokens, rel, b.line + offset))
    return out


def _curl(plugin, specs, tokens, rel, line):
    for api, prefixes, paths, spec_name in specs:
        var, path = url_path(tokens, api.base_vars)
        if not var:
            continue
        method = method_of(tokens)
        found, methods = match(path, prefixes, paths)
        if not found:
            return [Finding(plugin.name, CHECK, FAIL, "%s %s нет в %s" % (method, path, spec_name), rel, line,
                            "сверь путь со спецификацией; устаревший API замени актуальным")]
        if method not in methods:
            return [Finding(plugin.name, CHECK, FAIL, "%s не определён для %s в %s" % (method, path, spec_name),
                            rel, line, "у пути есть: %s" % ", ".join(sorted(methods)))]
        return []
    return []
