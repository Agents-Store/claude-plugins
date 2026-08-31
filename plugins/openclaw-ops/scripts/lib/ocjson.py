#!/usr/bin/env python3
"""Tolerant reader for OpenClaw CLI output, plus the exit-code contracts.

Two invariants this module exists to enforce:

1. **Parse stdout only.** The CLI writes update banners, progress and warnings to
   stderr. A ``2>&1`` concatenation glues a banner onto the JSON document (or
   onto a token) and every downstream consumer then fails with a misleading
   error. stderr is kept for diagnosis, never fed to the parser.
2. **A non-zero exit is data, not failure.** Several subcommands use the exit
   code as the finding channel: ``doctor --lint`` and ``models status --check``
   both return 1 and 2 for meaningful, expected states. Treating "rc != 0" as an
   error throws away the answer.
"""

import json
import re

__all__ = [
    "OcResult", "EXIT_CONTRACTS", "strip_banner", "parse_json",
    "exit_meaning", "interpret", "findings", "worst_severity",
]


# --------------------------------------------------------------------------- #
# exit-code contracts
# --------------------------------------------------------------------------- #
#
# Keyed by a stable command key (the subcommand plus the flag that selects the
# contract). Anything not listed here follows the ordinary "0 = success"
# convention and MUST NOT be assumed to encode severity in its exit code.
#
EXIT_CONTRACTS = {
    "doctor --lint": {
        0: ("clean", "no findings"),
        1: ("error", "at least one error-level finding"),
        2: ("warn", "warn-level findings only"),
    },
    "doctor --post-upgrade": {
        0: ("clean", "post-upgrade checks passed"),
        1: ("error", "at least one error-level finding"),
        2: ("warn", "warn-level findings only"),
    },
    "models status --check": {
        0: ("healthy", "credentials valid"),
        1: ("expired", "expired or missing credentials"),
        2: ("expiring", "credentials expiring inside the warning window"),
    },
    "security audit": {
        0: ("clean", "no findings"),
        1: ("error", "at least one error-level finding"),
        2: ("warn", "warn-level findings only"),
    },
}

# Severity ranking used when rolling findings up into one verdict.
SEVERITY_ORDER = ["info", "notice", "warn", "warning", "error", "critical", "fatal"]


def exit_meaning(command_key, rc):
    """Translate an exit code into ``(label, explanation)`` for a known contract."""
    table = EXIT_CONTRACTS.get(command_key)
    if table and rc in table:
        return table[rc]
    if rc == 0:
        return ("ok", "command succeeded")
    if rc == 127:
        return ("missing", "command not found inside the target")
    if rc in (124, 137, 143):
        return ("timeout", "command was killed (timeout or OOM)")
    return ("failed", "exit code %s (no documented contract)" % rc)


# --------------------------------------------------------------------------- #
# tolerant JSON extraction
# --------------------------------------------------------------------------- #

_JSON_START = re.compile(r"[\[{]")


def strip_banner(text):
    """Drop leading non-JSON noise so a stray banner on stdout is survivable.

    This is a fallback, not a licence to merge stderr into stdout: it only helps
    when the CLI itself printed a line before the document.
    """
    if not text:
        return ""
    m = _JSON_START.search(text)
    return text[m.start():] if m else text


def parse_json(stdout, allow_ndjson=True):
    """Parse a CLI JSON document. Returns ``(value, error)``; never raises.

    Accepts, in order: a plain document, a document preceded by banner lines,
    and — when ``allow_ndjson`` — newline-delimited JSON, which is returned as a
    list of the parsed lines.
    """
    if stdout is None:
        return None, "no stdout"
    text = stdout.strip()
    if not text:
        return None, "empty stdout"
    try:
        return json.loads(text), None
    except ValueError as first:
        stripped = strip_banner(text).strip()
        if stripped and stripped != text:
            try:
                return json.loads(stripped), None
            except ValueError:
                pass
        if allow_ndjson and "\n" in text:
            rows, bad = [], 0
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    bad += 1
            if rows and bad == 0:
                return rows, None
        return None, "not JSON: %s" % first


# --------------------------------------------------------------------------- #
# findings
# --------------------------------------------------------------------------- #
#
# The documented lint finding shape is
#   {checkId, severity, message, path, ocPath, fixHint}
# and it is the contract between diagnostics, the report, /repair and the
# auditor: a finding without a checkId + fixHint has no sanctioned fix and must
# be escalated to live documentation before anything is changed.
#
FINDING_KEYS = ("checkId", "severity", "message", "path", "ocPath", "fixHint")


def findings(doc):
    """Extract lint/audit findings from a parsed document, whatever wraps them."""
    if doc is None:
        return []
    if isinstance(doc, list):
        out = []
        for item in doc:
            out.extend(findings(item))
        return out
    if isinstance(doc, dict):
        for key in ("findings", "issues", "results", "checks", "problems"):
            val = doc.get(key)
            if isinstance(val, list):
                return [f for f in val if isinstance(f, dict)]
        if "checkId" in doc or "severity" in doc:
            return [doc]
    return []


def worst_severity(items):
    """Highest severity present in a finding list, or ``None`` when empty."""
    worst, rank = None, -1
    for f in items:
        sev = str(f.get("severity", "")).lower()
        if sev in SEVERITY_ORDER and SEVERITY_ORDER.index(sev) > rank:
            worst, rank = sev, SEVERITY_ORDER.index(sev)
    return worst


class OcResult(object):
    """One CLI invocation: raw streams, exit code, parsed document, verdict."""

    __slots__ = ("argv", "rc", "stdout", "stderr", "json", "parse_error",
                 "command_key", "label", "explanation", "scrubbed")

    def __init__(self, argv, rc, stdout, stderr, command_key=None, scrubbed=0):
        self.argv = list(argv)
        self.rc = rc
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.command_key = command_key
        self.scrubbed = scrubbed
        self.json, self.parse_error = parse_json(self.stdout)
        self.label, self.explanation = exit_meaning(command_key, rc)

    @property
    def ok(self):
        """True when the exit code carries no failure under the command's contract."""
        return self.label in ("ok", "clean", "healthy")

    def findings(self):
        return findings(self.json)

    def as_dict(self):
        return {
            "argv": self.argv,
            "rc": self.rc,
            "label": self.label,
            "explanation": self.explanation,
            "json": self.json,
            "parse_error": self.parse_error,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "scrubbed": self.scrubbed,
        }


def interpret(command_key, rc, stdout, stderr, argv=None, scrubbed=0):
    """Build an :class:`OcResult` from raw streams."""
    return OcResult(argv or [], rc, stdout, stderr, command_key, scrubbed)
