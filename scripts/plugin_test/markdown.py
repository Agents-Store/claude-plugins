"""Markdown плагина: какие файлы читать, fenced-блоки кода, ссылки."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "workspace"}
# История, а не инструкция: в них законно упоминаются удалённые файлы.
SKIP_FILES = {"CHANGELOG.md", "LEARNINGS.md"}
SKIP_MARKER = re.compile(r"<!--\s*plugin-test:\s*skip\s*-->")
RE_FENCE = re.compile(r"^\s{0,3}(?P<fence>`{3,}|~{3,})(?P<info>[^`]*)$")
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")
RE_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_REF_DEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$")


@dataclass(frozen=True)
class Block:
    info: str
    body: str
    line: int
    skip: bool


def iter_markdown(plugin_dir):
    for dirpath, dirnames, filenames in os.walk(plugin_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".md") and name not in SKIP_FILES:
                yield os.path.join(dirpath, name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _closes(line, fence):
    stripped = line.strip()
    return stripped.startswith(fence) and set(stripped) == {fence[0]}


def blocks(text):
    lines = text.split("\n")
    out, i, prev = [], 0, ""
    while i < len(lines):
        m = RE_FENCE.match(lines[i])
        if not m:
            if lines[i].strip():
                prev = lines[i]
            i += 1
            continue
        fence = m.group("fence")
        words = m.group("info").strip().split()
        start = j = i + 1
        while j < len(lines) and not _closes(lines[j], fence):
            j += 1
        out.append(Block(info=words[0].lower() if words else "", body="\n".join(lines[start:j]),
                         line=start + 1, skip=bool(SKIP_MARKER.search(prev))))
        prev = ""
        i = j + 1
    return out


def links(text):
    fence = None
    for n, line in enumerate(text.split("\n"), 1):
        m = RE_FENCE.match(line)
        if fence is None and m:
            fence = m.group("fence")
            continue
        if fence is not None:
            if _closes(line, fence):
                fence = None
            continue
        visible = RE_INLINE_CODE.sub("", line)
        ref = RE_REF_DEF.match(visible)
        if ref:
            yield ref.group(1), n
            continue
        for lm in RE_LINK.finditer(visible):
            yield lm.group(1), n
