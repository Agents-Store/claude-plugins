#!/usr/bin/env python3
"""PostToolUse guard: an instance config that was just edited into a file the gateway
would refuse to load.

Why a hook and not a check inside the edit command
-------------------------------------------------
The config is edited from several directions — a repair, a model-chain change, a hand
edit while reading a report — and every one of them can leave the file syntactically
fine and semantically rejected. The gateway validates the document against a strict
schema at startup: an unknown key at the root is not ignored, it is a refusal to start.
The distance between "the edit succeeded" and "the instance is down" is one restart,
and the restart usually happens later, in another session, for another reason.

What it checks, and what it deliberately does not
-------------------------------------------------
* **Parse.** JSON5 in, comments and trailing commas allowed, because that is what the
  runtime accepts. A file that does not parse here does not load there.
* **Unknown root keys.** The accepted key set is **derived from the sibling instances'
  own configs on this host**, never from a frozen list. A frozen list ages into false
  alarms the moment upstream adds a section, and a validator that cries wolf gets
  ignored exactly when it is right. With no readable sibling the check is skipped and
  says so.
* **Sections that disappeared.** Compared against the newest backup beside the file.
  Config surgery is additive; a vanished section is the signature of a rewrite that
  replaced the document instead of editing it.
* **Literal secrets.** A value shaped like a provider key belongs in the secret store
  and is referenced by name. Reported as key class and fingerprint — never the value.

It never mutates, never restarts anything, and never blocks the edit. It prints a
warning and exits 0. It is also silent unless the edited path is the config of an
instance this host's fleet config knows: a validator that comments on unrelated files
named ``openclaw.json`` trains the reader to skip it.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))

try:
    import config as cfgmod                                          # noqa: E402
    import redact                                                    # noqa: E402
except ImportError:                     # library missing: stay silent, never crash an edit
    sys.exit(0)

CONFIG_BASENAME = "openclaw.json"
BACKUP_RE = re.compile(r"^openclaw\.json\.bak(\.\d+)?$")
MAX_BYTES = 4 * 1024 * 1024


# --------------------------------------------------------------------------- #
# JSON5 -> JSON, enough of it
# --------------------------------------------------------------------------- #

def strip_json5(text):
    """Comments out, trailing commas out, single quotes and bare keys normalised.

    Not a full JSON5 implementation and not trying to be: it has to agree with the
    runtime on whether the document is loadable, not reproduce its parser.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'":
            quote, j = ch, i + 1
            buf = []
            while j < n:
                c = text[j]
                if c == "\\":
                    buf.append(text[j:j + 2])
                    j += 2
                    continue
                if c == quote:
                    break
                buf.append('\\"' if c == '"' else c)
                j += 1
            out.append('"' + "".join(buf) + '"')
            i = j + 1
            continue
        if text.startswith("//", i):
            i = text.find("\n", i)
            if i < 0:
                break
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        out.append(ch)
        i += 1
    body = "".join(out)
    body = re.sub(r",(\s*[}\]])", r"\1", body)                    # trailing commas
    body = re.sub(r"([{,]\s*)([A-Za-z_$][A-Za-z0-9_$]*)(\s*:)", r'\1"\2"\3', body)
    return body


def load(path):
    """(document, error). A parse failure is a finding, not an exception."""
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None, "file larger than %d bytes; not parsed" % MAX_BYTES
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        return None, "unreadable: %s" % exc.strerror
    if not raw.strip():
        return None, "empty file (finding fleet.config.empty)"
    try:
        return json.loads(strip_json5(raw)), None
    except ValueError as exc:
        return None, str(exc).split(":")[0] + " at " + str(exc).rsplit("(", 1)[-1].rstrip(")")


# --------------------------------------------------------------------------- #
# which instance is this, and who are its siblings
# --------------------------------------------------------------------------- #

def segments(path):
    return [s for s in os.path.abspath(path).split(os.sep) if s]


def identify(path, cfg):
    """(instance name, sibling config paths) or (None, []) when the file is not ours.

    An instance is recognised by its name appearing as a path segment, optionally
    constrained to the recorded data root. Sibling paths are the same path with that
    one segment swapped — which is exactly the assumption the fleet config already
    makes about the layout, and it is checked by opening the file, not by trusting it.
    """
    if os.path.basename(path) != CONFIG_BASENAME or not cfg.present:
        return None, []
    known = list(cfg.instances().keys())
    if not known:
        return None, []
    data_root = (cfg.data.get("data_root") or "").strip()
    if data_root and not os.path.abspath(path).startswith(os.path.abspath(data_root) + os.sep):
        return None, []
    parts = segments(path)
    index = name = None
    for pos, part in enumerate(parts):
        canonical = cfg.canonical_name(part)
        if canonical in known:
            index, name = pos, canonical
            break
    if name is None:
        return None, []
    siblings = []
    for other in known:
        if other == name:
            continue
        candidate = os.sep + os.path.join(*(parts[:index] + [other] + parts[index + 1:]))
        if os.path.isfile(candidate):
            siblings.append(candidate)
    return name, siblings


def newest_backup(path):
    directory = os.path.dirname(path)
    try:
        names = [n for n in os.listdir(directory) if BACKUP_RE.match(n)]
    except OSError:
        return None
    best, best_mtime = None, -1.0
    for name in names:
        full = os.path.join(directory, name)
        try:
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        if mtime > best_mtime:
            best, best_mtime = full, mtime
    return best


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #

def literal_secrets(doc, prefix="", found=None):
    """JSON paths carrying a value that looks like a key. Values never leave here."""
    found = [] if found is None else found
    if isinstance(doc, dict):
        for key, value in doc.items():
            where = "%s.%s" % (prefix, key) if prefix else str(key)
            if isinstance(value, str):
                klass = redact.classify_key(value, key)
                shaped = klass not in ("unclassified", "opaque-secret")
                named = bool(redact.SECRET_NAME_RE.search(str(key))) and len(value) >= 16
                if shaped or named:
                    found.append((where, klass if shaped else "opaque-secret",
                                  redact.fp(value)))
            else:
                literal_secrets(value, where, found)
    elif isinstance(doc, list):
        for pos, value in enumerate(doc):
            literal_secrets(value, "%s[%d]" % (prefix, pos), found)
    return found


def report(path, name, siblings, doc, error):
    lines = []
    if error:
        lines.append("PARSE FAILED (%s). The gateway validates this document at startup; a "
                     "file it cannot parse is a gateway that does not start. Restore from the "
                     "plugin snapshot or the backup ring before restarting — skill "
                     "config-surgery." % error)
        return lines
    if not isinstance(doc, dict):
        lines.append("The document root is not an object. The gateway expects an object and "
                     "will refuse this file.")
        return lines

    roots = set(doc.keys())
    accepted, readable = set(), 0
    for sibling in siblings:
        other, other_error = load(sibling)
        if other_error or not isinstance(other, dict):
            continue
        readable += 1
        accepted |= set(other.keys())
    if readable:
        unknown = sorted(roots - accepted)
        if unknown:
            lines.append("Root keys present here and in none of the %d sibling instance "
                         "config(s): %s. The schema is strict — an unknown root key is a "
                         "refusal to start, not an ignored field. Confirm the key against "
                         "this instance's own documentation (skill docs-research) before "
                         "restarting it." % (readable, ", ".join(unknown)))
    else:
        lines.append("Root-key check skipped: no sibling instance config was readable, so "
                     "there is nothing to derive the accepted key set from.")

    backup = newest_backup(path)
    if backup:
        old, old_error = load(backup)
        if not old_error and isinstance(old, dict):
            gone = sorted(set(old.keys()) - roots)
            if gone:
                lines.append("Sections present in the newest backup and absent now: %s "
                             "(finding fleet.config.deletions). Config surgery is additive; "
                             "a deletion count above zero is a separate red flag and needs a "
                             "line in the plan explaining each one." % ", ".join(gone))

    secrets = literal_secrets(doc)
    if secrets:
        rendered = ", ".join("%s [%s %s]" % (where, klass, mark or "fp:empty")
                             for where, klass, mark in secrets[:6])
        lines.append("Value-shaped secrets in the config (finding fleet.config.literal-secret, "
                     "critical): %s%s. Replace each with a reference by name, deliver the value "
                     "through the secret store — and rotate it: it has been on disk."
                     % (rendered, "" if len(secrets) <= 6 else
                        " and %d more" % (len(secrets) - 6)))
    return lines


def main():
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (ValueError, OSError):
        sys.exit(0)
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path or not os.path.isfile(path):
        sys.exit(0)

    cfg = cfgmod.load_config()
    name, siblings = identify(path, cfg)
    if name is None:
        sys.exit(0)                     # not a known instance's config: say nothing

    doc, error = load(path)
    lines = report(path, name, siblings, doc, error)
    if not lines or (len(lines) == 1 and lines[0].startswith("Root-key check skipped")):
        sys.exit(0)

    text = ("openclaw-ops: the file just edited is the config of instance %r. This is a "
            "warning only — nothing was changed.\n" % name)
    text += "\n".join("- " + line for line in lines)
    text += ("\nVerify before any restart: ocexec.py %s --json -- doctor --lint  "
             "(0 clean, 1 error, 2 warn)." % name)
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                      "additionalContext": redact.scrub(text)}},
              sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:                                               # noqa: BLE001
        sys.exit(0)                     # a hook that crashes on every edit gets disabled
