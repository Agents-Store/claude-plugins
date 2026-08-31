#!/usr/bin/env python3
"""Structural lint for the public plugin marketplace.

The scrub gate answers "does this tree carry deployment data". This module
answers the other half of the level-1 acceptance list: "is the plugin built the
way the conventions say it is". Three checks, each of which has already been a
real defect here:

  mutation-plan   a command that mutates, or that takes --yes, must print the
                  full eight-block dry-run plan and its ROLLBACK must be an
                  executable line — a sentence describing a rollback cannot be
                  pasted into a terminal at 3am.
  skill-name      the name in SKILL.md frontmatter, the directory name and
                  skill_name in evals/evals.json must be one and the same
                  string, or the skill is invoked under one name and evaluated
                  under another.
  version-parity  plugins/<p>/.claude-plugin/plugin.json version must equal the
                  version of that plugin's entry in .claude-plugin/marketplace.json,
                  or the marketplace advertises a build nobody can install.

Severity ladder mirrors the scrub gate: mutation-plan is a hard fail anywhere,
because an unrollbackable mutation is dangerous in any plugin. The two hygiene
checks warn repository-wide and hard-fail inside a plugin that opted into the
strict scope with a .scrub-strict marker, so a new plugin is held to the full
standard without a pre-existing defect elsewhere blocking unrelated merges.

There is no baseline file: these findings are fixed, not excused.

Exit codes: 0 clean, 1 hard fail, 2 warnings only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(REPO_ROOT, "plugins")
MARKETPLACE = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
STRICT_MARKER = ".scrub-strict"

FAIL, WARN = "fail", "warn"

# The dry-run contract. Order is the order a human reads them in.
DRY_RUN_BLOCKS = (
    "TARGET", "PRECHECK", "CHANGE", "BACKUP",
    "IMPACT", "VALIDATE", "ROLLBACK", "APPLY",
)

# How many of the eight names a command must already use before it counts as
# speaking the dry-run contract. Read-only commands here name at most three.
DRY_RUN_VOCABULARY_TRIGGER = 5

# Third trigger: what the command actually DOES. The first two triggers are
# both self-declarations — `--yes` in the argument-hint, or the block names
# already being used — so a command that mutates while declaring neither was
# never checked at all, and simply deleting `--yes` from the hint took it out
# of the contract. These patterns read the body instead: each entry is one
# independent kind of write, matched only inside a code span or a fenced block
# so that prose ("this restarts the gateway") does not count.
MUTATION_SIGNALS = (
    # The flag has to sit on the same line as the program it is passed to;
    # `\s` here would span the newlines between separate code spans and turn a
    # documentation list of flags into evidence of a write.
    ("apply-flag", re.compile(
        r"(?:^|[ \t|(&;$])[^\s|(&;$]+[ \t]+--(?:yes|apply|force|confirm|write|"
        r"no-dry-run|prune|purge)\b", re.M)),
    ("http-write", re.compile(r"\bcurl\b[^\n]{0,120}?-X\s*(?:POST|PUT|PATCH|DELETE)\b", re.I)),
    ("container", re.compile(
        r"\bdocker\b[^\n]{0,80}?\b(?:rm|kill|prune)\b"
        r"|\bdocker\s+compose\b[^\n]{0,80}?\b(?:up|down|restart|stop)\b"
        r"|\bdocker\s+(?:restart|stop|start)\b")),
    ("service", re.compile(r"\bsystemctl\s+(?:restart|start|stop|reload|enable|disable)\b")),
    ("filesystem", re.compile(r"\brm\s+-[a-zA-Z]*[rf]|\bsed\s+-i\b|\btruncate\s+-s\b")),
    ("vcs", re.compile(r"\bgit\s+(?:push|reset\s+--hard|clean\s+-[a-z]*f)\b")),
    ("orchestrator", re.compile(r"\bkubectl\s+(?:apply|delete|scale|rollout|patch)\b")),
    ("database", re.compile(
        r"\b(?:DROP|TRUNCATE|DELETE\s+FROM|ALTER\s+TABLE|UPDATE\s+\w+\s+SET)\b")),
    ("permissions", re.compile(r"\bchmod\s+[0-7]{3,4}\b|\bchown\s+\S+:")),
)

# One apply-flag is conclusive on its own; anything else needs a second,
# different kind of write before the command is treated as a mutator, so a
# read-only command that happens to show one example line stays out.
MUTATION_EVIDENCE_TRIGGER = 2

FENCED_BLOCK = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)```", re.S)


def mutation_evidence(text: str):
    """Which kinds of write the command's own code blocks perform."""
    runnable = "\n".join(FENCED_BLOCK.findall(text) + CODE_SPAN.findall(text))
    return {name for name, rx in MUTATION_SIGNALS if rx.search(runnable)}


def body_mutates(text: str) -> bool:
    kinds = mutation_evidence(text)
    return "apply-flag" in kinds or len(kinds) >= MUTATION_EVIDENCE_TRIGGER

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\s*$", re.S | re.M)
FM_NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
FM_ARG_HINT = re.compile(r"^argument-hint:\s*(.+?)\s*$", re.M)

# An inline `code span`. re.S because a long command in markdown prose is
# routinely wrapped across two lines inside one pair of backticks, and a
# rollback line is exactly the kind of long command that wraps.
CODE_SPAN = re.compile(r"`([^`]{3,}?)`", re.S)

# A code span that could actually be run: a program name followed by an
# argument, or a shell pipeline. Prose such as "restore the previous config"
# does not match — which is the entire point of the check.
EXECUTABLE = re.compile(
    r"(?:\A|[\s|(&;$])"
    r"(?:cp|mv|rm|ln|tar|gzip|gunzip|zcat|cat|install|mkdir|rmdir|chmod|chown|"
    r"sed|awk|tee|docker|podman|git|python3?|bash|sh|zsh|node|npm|pnpm|yarn|"
    r"systemctl|journalctl|service|curl|wget|kubectl|helm|make|rsync|scp|ssh|"
    r"openclaw|restic|psql|sqlite3|"
    r"[\w./${}-]*[\w-]\.(?:py|sh|bash|mjs|js))"
    r"\b\s+\S"
)


class Finding:
    __slots__ = ("path", "line", "rule", "severity", "excerpt", "message")

    def __init__(self, path, line, rule, severity, excerpt, message):
        self.path = path
        self.line = line
        self.rule = rule
        self.severity = severity
        self.excerpt = excerpt
        self.message = message


def rel(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT)


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def line_of(text: str, needle: str, default: int = 1) -> int:
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return default


def frontmatter(text: str) -> str:
    m = FRONTMATTER.search(text)
    return m.group(1) if m else ""


def is_strict(plugin_dir: str, force_strict: bool) -> bool:
    return force_strict or os.path.exists(os.path.join(plugin_dir, STRICT_MARKER))


def severity(rule: str, strict: bool) -> str:
    if rule == "mutation-plan":
        return FAIL
    return FAIL if strict else WARN


# ---------------------------------------------------------------------------
# 1. structural lint of mutating commands
# ---------------------------------------------------------------------------

def rollback_is_executable(text: str) -> bool:
    """Does at least one ROLLBACK mention carry a runnable command near it?

    ROLLBACK is named twice in a typical command file — once in the list of the
    eight blocks, once where the plan describes it — so every occurrence gets a
    window and any one of them may carry the command.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "ROLLBACK" not in line:
            continue
        window = "\n".join(lines[i:i + 5])
        for span in CODE_SPAN.findall(window):
            if EXECUTABLE.search(" ".join(span.split())):
                return True
        # a fenced block right under the mention counts as well
        for fenced in re.findall(r"```[a-z]*\n(.*?)```", window, re.S):
            if EXECUTABLE.search(fenced):
                return True
    return False


def check_mutation_plans(plugin_dir, strict):
    findings = []
    commands = os.path.join(plugin_dir, "commands")
    if not os.path.isdir(commands):
        return findings
    for name in sorted(os.listdir(commands)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(commands, name)
        text = read(path)
        fm = frontmatter(text)
        hint = FM_ARG_HINT.search(fm)
        hint = hint.group(1) if hint else ""
        present = [b for b in DRY_RUN_BLOCKS if re.search(r"\b%s\b" % b, text)]
        takes_yes = "--yes" in hint
        mutates = body_mutates(text)
        # Three independent triggers. The first two are self-declarations —
        # `--yes` in the grammar, or the block names already in use — and both
        # are removable by editing the declaration. The third reads the body,
        # so a command that mutates cannot opt out of the contract by staying
        # quiet about it. A read-only command that merely mentions BACKUP or
        # ROLLBACK in a sentence still does not qualify: the vocabulary trigger
        # asks for a majority of the eight names, and the body trigger only
        # counts writes inside code, not prose.
        declared = takes_yes or len(present) >= DRY_RUN_VOCABULARY_TRIGGER
        if not (declared or mutates):
            continue
        # A command that DECLARES the contract and then breaks it is a hard fail
        # anywhere, unchanged. A command caught only by what its body does is
        # pre-existing debt in this repository, so it follows the same ladder as
        # the hygiene checks — warn repo-wide, hard fail inside a plugin that
        # opted into the strict scope, which is every new plugin.
        sev = severity("mutation-plan", strict) if declared else (FAIL if strict else WARN)
        missing = [b for b in DRY_RUN_BLOCKS if b not in present]
        if missing:
            why = ("--yes in argument-hint" if takes_yes
                   else ("writes in its body: " + ", ".join(sorted(mutation_evidence(text)))
                         if mutates else "already speaks the dry-run vocabulary"))
            findings.append(Finding(
                rel(path), line_of(text, "argument-hint") if takes_yes else 1,
                "mutation-plan", sev,
                name,
                "mutating command (%s) is missing dry-run block(s): %s"
                % (why, ", ".join(missing))))
        elif not rollback_is_executable(text):
            findings.append(Finding(
                rel(path), line_of(text, "ROLLBACK"),
                "mutation-plan", sev,
                name,
                "ROLLBACK must be an executable line, not a description of one"))
    return findings


# ---------------------------------------------------------------------------
# 2. frontmatter / evals name parity
# ---------------------------------------------------------------------------

def check_skill_names(plugin_dir, strict):
    findings = []
    skills = os.path.join(plugin_dir, "skills")
    if not os.path.isdir(skills):
        return findings
    sev = severity("skill-name", strict)
    for dirname in sorted(os.listdir(skills)):
        skill_dir = os.path.join(skills, dirname)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        text = read(skill_md)
        m = FM_NAME.search(frontmatter(text))
        if not m:
            findings.append(Finding(
                rel(skill_md), 1, "skill-name", sev, dirname,
                "SKILL.md frontmatter has no name: field"))
        else:
            name = m.group(1).strip().strip("\"'")
            if name != dirname:
                findings.append(Finding(
                    rel(skill_md), line_of(text, "name:"), "skill-name", sev,
                    "%s != %s" % (name, dirname),
                    "frontmatter name must equal the skill directory name"))
        evals = os.path.join(skill_dir, "evals", "evals.json")
        if not os.path.isfile(evals):
            continue
        try:
            data = json.loads(read(evals))
        except ValueError as exc:
            findings.append(Finding(
                rel(evals), 1, "skill-name", sev, dirname,
                "evals.json is not valid JSON: %s" % exc))
            continue
        skill_name = data.get("skill_name")
        if skill_name != dirname:
            findings.append(Finding(
                rel(evals), line_of(read(evals), "skill_name"), "skill-name",
                sev, "%s != %s" % (skill_name, dirname),
                "evals.json skill_name must equal the skill directory name"))
    return findings


# ---------------------------------------------------------------------------
# 3. version parity plugin.json <-> marketplace.json
# ---------------------------------------------------------------------------

def marketplace_versions():
    if not os.path.isfile(MARKETPLACE):
        return None, "missing"
    try:
        data = json.loads(read(MARKETPLACE))
    except ValueError as exc:
        return None, "unparsable: %s" % exc
    entries = {}
    for entry in data.get("plugins", []):
        if isinstance(entry, dict) and entry.get("name"):
            entries[entry["name"]] = entry.get("version")
    return entries, None


def check_version_parity(plugin_dir, strict, entries, market_error):
    findings = []
    manifest = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.isfile(manifest):
        return findings
    sev = severity("version-parity", strict)
    name = os.path.basename(plugin_dir)
    try:
        data = json.loads(read(manifest))
    except ValueError as exc:
        return [Finding(rel(manifest), 1, "version-parity", sev, name,
                        "plugin.json is not valid JSON: %s" % exc)]
    if market_error:
        return [Finding(rel(MARKETPLACE), 1, "version-parity", sev, name,
                        ".claude-plugin/marketplace.json is %s" % market_error)]
    declared = data.get("name") or name
    version = data.get("version")
    text = read(manifest)
    if declared not in entries:
        findings.append(Finding(
            rel(manifest), line_of(text, '"name"'), "version-parity", sev,
            declared, "plugin is not registered in .claude-plugin/marketplace.json"))
    elif entries[declared] != version:
        findings.append(Finding(
            rel(manifest), line_of(text, '"version"'), "version-parity", sev,
            "%s != %s" % (version, entries[declared]),
            "plugin.json version and the marketplace.json entry must match"))
    return findings


# ---------------------------------------------------------------------------


def plugins_for(targets):
    """Which plugin directories a set of scan targets covers."""
    if not os.path.isdir(PLUGINS_DIR):
        return []
    everything = sorted(
        os.path.join(PLUGINS_DIR, n) for n in os.listdir(PLUGINS_DIR)
        if os.path.isdir(os.path.join(PLUGINS_DIR, n)))
    selected, seen = [], set()
    for target in targets:
        abs_target = os.path.abspath(
            target if os.path.isabs(target) else os.path.join(REPO_ROOT, target))
        for plugin in everything:
            if plugin in seen:
                continue
            if abs_target == REPO_ROOT or abs_target == PLUGINS_DIR:
                seen.add(plugin)
                selected.append(plugin)
            elif abs_target == plugin or abs_target.startswith(plugin + os.sep):
                seen.add(plugin)
                selected.append(plugin)
            elif plugin.startswith(abs_target + os.sep):
                seen.add(plugin)
                selected.append(plugin)
    return selected


def run(targets, force_strict=False):
    entries, market_error = marketplace_versions()
    findings = []
    for plugin_dir in plugins_for(targets):
        strict = is_strict(plugin_dir, force_strict)
        findings += check_mutation_plans(plugin_dir, strict)
        findings += check_skill_names(plugin_dir, strict)
        findings += check_version_parity(plugin_dir, strict, entries, market_error)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="plugin_lint.py",
        description="Structural lint for the public plugin marketplace.")
    ap.add_argument("targets", nargs="*", help="paths to lint (default: every plugin)")
    ap.add_argument("--strict", action="store_true",
                    help="apply the strict severity regardless of the %s marker" % STRICT_MARKER)
    ap.add_argument("--format", choices=("text", "json"), default="text")
    # accepted so the wrapper can forward the scrub gate's argument list verbatim
    ap.add_argument("--baseline", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--no-baseline", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    findings = run(args.targets or ["."], args.strict)
    fails = [f for f in findings if f.severity == FAIL]
    warns = [f for f in findings if f.severity == WARN]

    if args.format == "json":
        print(json.dumps({
            "fail": len(fails), "warn": len(warns),
            "findings": [{"path": f.path, "line": f.line, "rule": f.rule,
                          "severity": f.severity, "excerpt": f.excerpt,
                          "message": f.message} for f in findings],
        }, indent=2))
    else:
        for group, label in ((fails, "FAIL"), (warns, "WARN")):
            for f in group:
                print("%s %s:%d [%s] %s — %s"
                      % (label, f.path, f.line, f.rule, f.excerpt, f.message))
        print("plugin-lint: %d fail, %d warn" % (len(fails), len(warns)))
        if fails or warns:
            print("Fix the structure: every eight-block name and an executable "
                  "ROLLBACK in a mutating command, one name across SKILL.md / "
                  "directory / evals.json, and the same version in plugin.json "
                  "and .claude-plugin/marketplace.json.")

    if fails:
        return 1
    return 2 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
