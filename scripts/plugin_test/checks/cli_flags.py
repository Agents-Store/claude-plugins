"""cli-flags: подкоманды и --флаги CLI в bash-блоках есть в снимке --help (opt-in, spec §5)."""
from __future__ import annotations

import re
import subprocess

from .. import cli_snapshot, snapshots
from ..manifest import path_of
from ..markdown import blocks, iter_markdown, read
from ..model import FAIL, INFO, INFRA, SKIPPED, WARN, Finding
from ..shell import commands, logical_lines, strip_prefix

CHECK = "cli-flags"
SHELL = {"bash", "sh", "shell"}
RE_FLAG = re.compile(r"^--[a-z0-9][a-z0-9-]*")
ALWAYS = {"--help", "--version"}


def run(plugin, ctx, manifest):
    if not manifest.cli:
        return []
    out, live = [], {}
    for tool, spec in sorted(manifest.cli.items()):
        data = _snapshot(plugin, ctx, tool, spec, out)
        if data:
            live[spec.bin] = data
    if not live:
        return out
    for md in iter_markdown(plugin.dir):
        rel = plugin.rel(md)
        for b in blocks(read(md)):
            if b.skip or b.info not in SHELL:
                continue
            for offset, line in logical_lines(b.body):
                for tokens in commands(line):
                    tokens = strip_prefix(tokens)
                    if tokens and tokens[0] in live:
                        out.extend(_check(plugin, live[tokens[0]], tokens, rel, b.line + offset))
    return out


def _snapshot(plugin, ctx, tool, spec, out):
    path = snapshots.cli_path(plugin, tool)
    rel = plugin.rel(path)
    if ctx.update_snapshots:
        try:
            data = cli_snapshot.build(spec.bin, spec.commands)
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            out.append(Finding(plugin.name, CHECK, INFRA, "CLI %s: снимок не снят (%s)" % (tool, exc),
                               fix="поставь официальный релиз %s" % spec.bin))
            return None
        snapshots.write(path, data)
        out.append(Finding(plugin.name, CHECK, INFO, "CLI %s %s: снимок записан" % (tool, data["version"]), rel))
        if spec.version and data["version"] and spec.version != data["version"]:
            out.append(Finding(plugin.name, CHECK, WARN,
                               "CLI %s: в манифесте версия %s, снимок снят с %s" % (tool, spec.version, data["version"]),
                               plugin.rel(path_of(plugin)), 0, "обнови version в [cli.%s]" % tool))
        return data
    try:
        data = snapshots.load_cli(path)
    except snapshots.SnapshotError as exc:
        out.append(Finding(plugin.name, CHECK, FAIL, "снимок не читается: %s" % exc.msg, rel, 0,
                           "перезапиши: --update-snapshots"))
        return None
    if data is None:
        out.append(Finding(plugin.name, CHECK, SKIPPED, "нет снимка CLI %s" % tool,
                           fix="сними: plugin_test.py --plugin %s --check cli-flags --update-snapshots" % plugin.dirname))
    return data


def _placeholder(word):
    return any(c in word for c in "<>${}") or word.isupper()


def _check(plugin, snap, tokens, rel, line):
    args = tokens[1:]
    words = []
    for t in args:
        if t == "--" or t.startswith("-"):
            break
        words.append(t)
    path = next((" ".join(words[:n]) for n in range(len(words), 0, -1)
                 if " ".join(words[:n]) in snap["commands"]), "")
    tool, version = snap.get("tool", tokens[0]), snap.get("version") or "?"
    subs = snap.get("subcommands") or []
    if not path and words and subs and words[0] not in subs and not _placeholder(words[0]):
        return [Finding(plugin.name, CHECK, FAIL, "%s: нет подкоманды %r (снимок %s)" % (tool, words[0], version),
                        rel, line, "сверь с `%s --help`; есть: %s" % (tool, ", ".join(subs[:12])))]
    if words and not path:
        return []  # подкоманда существует, но её флаги не сняты — сравнивать не с чем
    depth = len(path.split())
    if path and len(words) > depth and words[depth] in (snap.get("children") or {}).get(path, []):
        return []  # дочерняя подкоманда снятой команды — её флаги не сняты
    known = (snap.get("children") or {}).get(path, []) if path else subs
    seen_flag, after = False, []
    for t in args:
        if t == "--":
            break
        if t.startswith("-"):
            seen_flag = True
        elif seen_flag:
            after.append(t)
    if any(t in known for t in after):
        return []  # флаг стоит перед подкомандой: чьи флаги — неясно, молчим
    allowed = ALWAYS | set(snap.get("global") or []) | set(snap["commands"].get(path, []))
    out = []
    for t in args:
        if t == "--":
            break
        m = RE_FLAG.match(t)
        if m and m.group(0) not in allowed:
            where = "%s %s" % (tool, path) if path else tool
            out.append(Finding(plugin.name, CHECK, FAIL, "%s: нет флага %s (снимок %s)" % (where, m.group(0), version),
                               rel, line, "сверь с `%s --help`" % where))
    return out
