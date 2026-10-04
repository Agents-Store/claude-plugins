"""api-paths: метод и путь curl-рецептов есть в OpenAPI-спецификации (opt-in, spec §5)."""
from __future__ import annotations

import json
import os
import re

from ..markdown import blocks, iter_markdown, read
from ..model import FAIL, INFRA, Finding
from ..shell import commands, logical_lines, strip_prefix

CHECK = "api-paths"
SHELL = {"bash", "sh", "shell"}
METHODS = ("get", "put", "post", "delete", "patch", "head", "options")
DATA_FLAGS = {"-d", "--data", "--data-raw", "--data-binary", "--data-urlencode", "-F", "--form", "--json"}
UPLOAD_FLAGS = {"-T", "--upload-file"}
# опции curl, чьё значение — следующий токен (или остаток токена: -XPOST, -sSo/dev/null)
ARG_LONG = {"--data", "--data-raw", "--data-binary", "--data-urlencode", "--json", "--header", "--form", "--user",
            "--output", "--referer", "--user-agent", "--cookie", "--cookie-jar", "--request", "--upload-file",
            "--write-out", "--config", "--url"}
ARG_SHORT = set("dHFuoeAbcXTwK")


def load_spec(path):
    with open(path, encoding="utf-8") as fh:
        if path.endswith((".yaml", ".yml")):
            import yaml
            data = yaml.safe_load(fh)
        else:
            data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("спецификация — не объект")
    servers = data.get("servers")
    if servers is not None and not isinstance(servers, list):
        raise ValueError("servers — ожидался список")
    raw_paths = data.get("paths")
    if raw_paths is None:
        raw_paths = {}
    if not isinstance(raw_paths, dict) or not all(isinstance(k, str) for k in raw_paths):
        raise ValueError("paths — ожидалась таблица с ключами-строками")
    prefixes = {""}
    for server in servers or []:
        url = server.get("url") if isinstance(server, dict) else None
        if not isinstance(url, str):
            continue
        p = re.sub(r"^[a-z][a-z0-9+.-]*://[^/]*", "", url).rstrip("/")
        if p.startswith("/"):
            prefixes.add(p)
    if isinstance(data.get("basePath"), str):
        prefixes.add(data["basePath"].rstrip("/"))
    paths = []
    for p, item in raw_paths.items():
        if isinstance(item, dict):
            segments = p.rstrip("/").split("/") if p.strip("/") else [""]
            paths.append((segments, {m.upper() for m in item if m in METHODS}))
    return sorted(prefixes), paths


def _options(tokens):
    """(опции, позиционные): опции — [(имя, значение | None)]; -sSX POST, -XPOST, --request=PUT, --url U разобраны."""
    opts, positional, i = [], [], 0
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t == "--":
            positional.extend(tokens[i:])
            break
        if t.startswith("--"):
            name, eq, value = t.partition("=")
            if eq:
                opts.append((name, value))
            elif name in ARG_LONG:
                opts.append((name, tokens[i] if i < len(tokens) else ""))
                i += 1
            else:
                opts.append((name, None))
        elif t.startswith("-") and len(t) > 1:
            for j, ch in enumerate(t[1:], 1):
                if ch in ARG_SHORT:
                    value = t[j + 1:]
                    if not value:
                        value = tokens[i] if i < len(tokens) else ""
                        i += 1
                    opts.append(("-" + ch, value))
                    break
                opts.append(("-" + ch, None))
        else:
            positional.append(t)
    return opts, positional


def method_of(tokens):
    """Метод запроса; "" — метод неизвестен (`-X "$METHOD"`): такой вызов не проверяется."""
    method, has_data, upload, get, head = None, False, False, False, False
    for name, value in _options(tokens)[0]:
        if name in ("-X", "--request"):
            word = (value or "").upper()
            method = word if re.fullmatch(r"[A-Z]+", word) else ""
        elif name in DATA_FLAGS:
            has_data = True
        elif name in UPLOAD_FLAGS:
            upload = True
        elif name in ("-G", "--get"):
            get = True
        elif name in ("-I", "--head"):
            head = True
    if method is not None:
        return method
    if head:
        return "HEAD"
    if upload:
        return "PUT"
    if get:
        return "GET"
    return "POST" if has_data else "GET"


def url_path(tokens, base_vars):
    """(переменная, путь) первого URL curl с базовой переменной; значения флагов (-d, -H, -o …) — не URL."""
    opts, positional = _options(tokens)
    urls = [value for name, value in opts if name == "--url" and value]
    for t in urls or positional:
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
        except ImportError:
            out.append(Finding(plugin.name, CHECK, INFRA, "PyYAML не установлен — %s не проверена" % api.spec,
                               plugin.rel(path), 0, "pip install 'PyYAML>=6,<7'"))
            continue
        except Exception as exc:  # noqa: BLE001 — любая форма битой спецификации — находка, а не падение runner-а
            out.append(Finding(plugin.name, CHECK, FAIL, "спецификация не читается: %s" % _describe(exc),
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


def _describe(exc):
    """ИмяКласса: первая строка сообщения; у OSError — без абсолютного пути."""
    text = exc.strerror if isinstance(exc, OSError) and exc.strerror else str(exc)
    lines = text.strip().splitlines()
    return "%s: %s" % (type(exc).__name__, (lines[0] if lines else "")[:200])


def _curl(plugin, specs, tokens, rel, line):
    for api, prefixes, paths, spec_name in specs:
        var, path = url_path(tokens, api.base_vars)
        if not var:
            continue
        method = method_of(tokens)
        if not method:
            return []  # -X "$METHOD": метод неизвестен, сравнивать не с чем
        found, methods = match(path, prefixes, paths)
        if not found:
            return [Finding(plugin.name, CHECK, FAIL, "%s %s нет в %s" % (method, path, spec_name), rel, line,
                            "сверь путь со спецификацией; устаревший API замени актуальным")]
        if method not in methods:
            return [Finding(plugin.name, CHECK, FAIL, "%s не определён для %s в %s" % (method, path, spec_name),
                            rel, line, "у пути есть: %s" % ", ".join(sorted(methods)))]
        return []
    return []
