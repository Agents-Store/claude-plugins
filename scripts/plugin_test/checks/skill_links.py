"""skill-links: относительные ссылки Markdown и указатели `плагин:компонент` (spec §5)."""
from __future__ import annotations

import difflib
import os
import re
from urllib.parse import unquote

from ..markdown import iter_markdown, links, read
from ..model import FAIL, WARN, Finding

CHECK = "skill-links"
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)
PLACEHOLDER = re.compile(r"[<>{}$]|\.\.\.")
RE_POINTER = re.compile(r"`([a-z][a-z0-9-]*):([a-z][a-z0-9-]*)`")
PLUGIN_NAME = re.compile(r"^(?:stack-[a-z0-9-]+|[a-z0-9-]+-(?:dev|ops|provision))$")
# Официальные и сторонние плагины, на которые skills ссылаются намеренно.
EXTERNAL_PLUGINS = frozenset({
    "plugin-dev", "superpowers", "skill-creator", "code-simplifier",
    "frontend-design", "claude-code-setup",
})


def run(plugin, ctx, manifest):
    out = []
    root = plugin.dir + os.sep
    for path in iter_markdown(plugin.dir):
        text = read(path)
        rel = plugin.rel(path)
        for target, line in links(text):
            if EXTERNAL.match(target) or PLACEHOLDER.search(target):
                continue
            clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not clean:
                continue
            if clean.startswith("/"):
                out.append(Finding(plugin.name, CHECK, FAIL, "абсолютный путь в ссылке: %s" % target,
                                   rel, line, "ссылайся относительно файла"))
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), clean))
            if not os.path.exists(dest):
                out.append(Finding(plugin.name, CHECK, FAIL, "ссылка ведёт в пустоту: %s" % target,
                                   rel, line, "поправь путь или убери ссылку"))
            elif not (dest + os.sep).startswith(root):
                out.append(Finding(plugin.name, CHECK, FAIL, "ссылка выходит за пределы плагина: %s" % target,
                                   rel, line, "у пользователя этого файла не будет — перенеси нужное в плагин"))
        for n, line_text in enumerate(text.split("\n"), 1):
            for m in RE_POINTER.finditer(line_text):
                out.extend(_pointer(plugin, ctx, m.group(1), m.group(2), rel, n))
    return out


def _pointer(plugin, ctx, target, component, rel, line):
    if target not in ctx.catalog.plugins:
        if target in EXTERNAL_PLUGINS or not PLUGIN_NAME.match(target):
            return []
        return [Finding(plugin.name, CHECK, WARN, "указатель на неизвестный плагин `%s:%s`" % (target, component),
                        rel, line, "проверь имя; внешний плагин внеси в EXTERNAL_PLUGINS")]
    known = ctx.catalog.components(target)
    if component in known:
        return []
    close = difflib.get_close_matches(component, sorted(known), n=3)
    return [Finding(plugin.name, CHECK, FAIL, "в плагине %s нет skill, команды или агента `%s`" % (target, component),
                    rel, line, "похожие: %s" % ", ".join(close) if close else "есть: %s" % ", ".join(sorted(known)[:10]))]
