#!/usr/bin/env python3
"""Tolerant reader for OpenClaw CLI output, plus the exit-code contracts.

Two invariants this module exists to enforce:

1. **Parse stdout only.** The CLI writes update banners, progress and warnings to
   stderr. A ``2>&1`` concatenation glues a banner onto the JSON document (or
   onto a token) and every downstream consumer then fails with a misleading
   error. stderr is kept for diagnosis, never fed to the parser.
2. **A non-zero exit is data, not failure — but only where upstream says so.**
   Several subcommands use the exit code as the finding channel: ``doctor
   --lint`` returns 1 for "a finding at or above the threshold" and
   ``models status --check`` returns 1 and 2 for credential states. Treating
   "rc != 0" as an error throws away the answer. The converse is the trap this
   module already fell into once: reading a code nobody documented as a verdict.
   ``doctor --lint`` exits 2 when the command itself failed before its checks
   completed; that used to be filed as "warnings only" and a broken run read as
   a pass. A command with no documented table gets none here — the canary run
   that would justify one is the owner's, not an assumption.
"""

import json
import re

__all__ = [
    "OcResult", "EXIT_CONTRACTS", "strip_banner", "parse_json",
    "exit_meaning", "interpret", "findings", "worst_severity", "finding_severity",
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
    # 0 = nothing at or above --severity-min, 1 = at least one finding at or above it,
    # 2 = the command or its runtime failed before the checks completed. The threshold
    # is the caller's: the same instance exits 0 or 1 depending on --severity-min, so
    # a caller that wants exit codes comparable across versions pins the threshold.
    # Source: the upstream "Lint and post-upgrade modes" page, "Explicit lint exit codes".
    "doctor --lint": {
        0: ("clean", "no findings at or above the severity threshold"),
        1: ("findings", "at least one finding at or above the severity threshold"),
        2: ("failed", "the command or its runtime failed before the health checks "
                      "completed — a failure, not a finding"),
    },
    # 1 only when a finding carries level "error"; a warning (plugin version drift is
    # one) does not change the code. 2 is not part of the documented contract.
    "doctor --post-upgrade": {
        0: ("clean", "no error-level finding (warnings do not change the exit code)"),
        1: ("error", "at least one finding with level error"),
    },
    "models status --check": {
        0: ("healthy", "credentials valid"),
        1: ("expired", "expired or missing credentials, an incompatible route, an unavailable "
                       "runtime, or indeterminate readiness"),
        2: ("expiring", "credentials expiring inside the warning window"),
    },
    # Documented for CI gates: 1 on findings, 2 for unresolved references (regardless of
    # --check) and for store validation failures.
    "secrets audit --check": {
        0: ("clean", "no plaintext, shadowed reference or residue found"),
        1: ("findings", "plaintext, shadowed references or residues found"),
        2: ("unresolved", "unresolved references or a store validation failure"),
    },
    # `security audit` is deliberately absent: upstream documents its severities
    # (critical / warn / info) and its JSON shape, but no exit-code table. Asserting one
    # here would be inventing a contract. Add it only after a canary run confirms it.
}

# Severity ranking used when rolling findings up into one verdict. ``warn`` and
# ``warning`` are one rank: lint spells it ``warning``, the security audit ``warn``.
SEVERITY_ORDER = ["info", "notice", "warn", "warning", "error", "critical", "fatal"]
_RANK = {"info": 0, "notice": 1, "warn": 2, "warning": 2, "error": 3, "critical": 4, "fatal": 5}


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
# be escalated to live documentation before anything is changed. (Current builds
# print ``path`` as a config path and may omit ``ocPath``; both are read.) The
# document around the findings is ``{schemaVersion, ok, checksRun, checksSkipped,
# findings}``, and an id has the shape ``core/doctor/<check>`` or ``<plugin>/<check>``.
#
# ``doctor --post-upgrade --json`` is a different envelope, ``{probesRun,
# findings}``, and names the severity ``level`` — not ``severity``.
#
FINDING_KEYS = ("checkId", "severity", "message", "path", "ocPath", "fixHint")
SEVERITY_FIELDS = ("severity", "level")


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
        if "checkId" in doc or "severity" in doc or "level" in doc:
            return [doc]
    return []


def finding_severity(item):
    """The severity word of one finding, whichever field the command names it in."""
    for key in SEVERITY_FIELDS:
        value = item.get(key)
        if value is not None:
            return str(value).lower()
    return ""


def worst_severity(items):
    """Highest severity present in a finding list, or ``None`` when empty."""
    worst, rank = None, -1
    for f in items:
        sev = finding_severity(f)
        if sev in _RANK and _RANK[sev] > rank:
            worst, rank = sev, _RANK[sev]
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
