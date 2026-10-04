"""Снимок --help CLI: глобальные флаги, подкоманды верхнего уровня, флаги выбранных команд.

Бинарь — официальный релиз, запускается только с --help и --version, в env -i
с временным HOME: снимку не нужны ни вход, ни сеть.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

from .model import CHECK_TIMEOUT

RE_HELP_FLAG = re.compile(r"(?<![\w-])--[a-z0-9][a-z0-9-]*")
RE_SECTION = re.compile(r"^(available commands|commands|subcommands)\s*:?\s*$", re.I)
# cobra выравнивает по самому длинному имени + ОДИН пробел: между именем и описанием бывает один пробел
RE_SUBCOMMAND = re.compile(r"^\s{2,}([a-z][a-z0-9-]*)(?:,\s*[a-z][a-z0-9-]*)*(?:\s+\S|\s*$)")
RE_VERSION = re.compile(r"\d+\.\d+(?:\.\d+)?")


def parse_flags(text):
    return sorted(set(RE_HELP_FLAG.findall(text)))


def parse_subcommands(text):
    subs, inside = [], False
    for line in text.split("\n"):
        if RE_SECTION.match(line.strip()):
            inside = True
            continue
        if not inside:
            continue
        if not line.strip():
            if subs:
                inside = False
            continue
        m = RE_SUBCOMMAND.match(line)
        if m:
            subs.append(m.group(1))
        elif not line.startswith(" "):
            inside = False
    return sorted(set(subs))


def _run(path, args, home):
    proc = subprocess.run([path, *args], capture_output=True, text=True, timeout=CHECK_TIMEOUT, cwd=home,
                          env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home})
    return proc.stdout + "\n" + proc.stderr


def build(bin_name, commands):
    """{tool, version, global, subcommands, commands, children}; FileNotFoundError, если бинаря нет."""
    path = shutil.which(bin_name)
    if not path:
        raise FileNotFoundError(bin_name)
    with tempfile.TemporaryDirectory() as home:
        top = _run(path, ["--help"], home)
        version = RE_VERSION.search(_run(path, ["--version"], home))
        data = {"tool": bin_name, "version": version.group(0) if version else "",
                "global": parse_flags(top), "subcommands": parse_subcommands(top), "commands": {}, "children": {}}
        for command in commands:
            text = _run(path, [*command.split(), "--help"], home)
            data["commands"][command] = parse_flags(text)
            kids = parse_subcommands(text)
            if kids:
                data["children"][command] = kids
    return data
