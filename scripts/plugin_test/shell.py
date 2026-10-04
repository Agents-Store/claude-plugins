"""Разбор bash-блоков для cli-flags и api-paths: логические строки и отдельные команды.

Разбор нарочно простой — shlex, а не парсер bash. Строка, которую shlex не
осилил, пропускается: проверка, которая молчит на сложной строке, лучше
проверки, которая выдумывает находку.
"""
from __future__ import annotations

import re
import shlex

SEPARATORS = set(";&|")
PREFIX_WORDS = {"sudo", "env", "exec", "time", "command", "nohup"}
RE_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _complete(text):
    try:
        shlex.split(text, comments=True)
        return True
    except ValueError:
        return False


def logical_lines(body):
    """[(смещение первой строки от начала блока, текст)]: `\\`-продолжения и
    многострочные кавычки склеены, строки-комментарии и пустые выброшены."""
    out, buf, start = [], "", 0
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if not buf:
            start = i
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
            continue
        buf += line
        if not _complete(buf) and i + 1 < len(lines):
            buf += "\n"
            continue
        if buf.strip() and not buf.lstrip().startswith("#"):
            out.append((start, buf))
        buf = ""
    return out


def commands(line):
    """Токены отдельных команд строки: разделители ; && || | &, начало $( … )."""
    try:
        lex = shlex.shlex(line, posix=True, punctuation_chars=";&|")
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return []
    cmds, cur = [], []
    for tok in tokens:
        if tok and set(tok) <= SEPARATORS:
            if cur:
                cmds.append(cur)
            cur = []
            continue
        if "$(" in tok:
            head, _, tail = tok.partition("$(")
            if head and not RE_ASSIGNMENT.match(head):
                cur.append(head)
            if cur:
                cmds.append(cur)
            cur = []
            if any(ch.isspace() for ch in tail):  # "$(cmd args)" в кавычках — один токен
                cmds.extend(commands(tail[:-1] if tail.endswith(")") else tail))
            elif tail:
                cur = [tail]
            continue
        cur.append(tok.rstrip(")") if tok.endswith(")") and "(" not in tok else tok)
    if cur:
        cmds.append(cur)
    return [c for c in cmds if c]


def strip_prefix(tokens):
    """Убирает sudo / env / VAR=значение перед именем программы."""
    i = 0
    while i < len(tokens) and (tokens[i] in PREFIX_WORDS or RE_ASSIGNMENT.match(tokens[i])):
        i += 1
    return tokens[i:]
