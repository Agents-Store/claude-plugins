#!/usr/bin/env python3
"""report.py — one canonical report, and the delta against the last one.

    report.py [--input PATH|-] [--compare-with PATH|auto] [--versions PATH]
              [--format md|json] [--out PATH] [options]

Why this exists
---------------
A health run answers "what is wrong now". That is the less useful half. The
question an operator actually acts on is comparative:

    did this instance get worse since yesterday?
    is this finding new, or has nobody touched it for six weeks?
    did the thing we fixed last week stay fixed?

None of that survives if the report is prose regenerated from scratch each time.
So this module does two things and refuses to do more: it renders a **canonical**
document — the same sections in the same order with the same wording for the same
input — and it computes a **delta** against earlier snapshots.

Comparability rests entirely on stable finding ids. ``<instance>/<check-id>`` is
the join key; renaming a check id silently resets every age counter in the
history, which is why healthcheck.py treats those ids as a contract rather than
as labels.

Ages come from the snapshot history, not from a field somebody has to remember to
carry forward: the first snapshot in the directory that contains a finding id is
its ``first_seen``. A finding that has been present in every snapshot for six
weeks reports six weeks, whether or not anyone wrote that down.

Input is whatever ``healthcheck.py --snapshot`` wrote (schema
``openclaw-ops/health/1``); ``versions.py --json`` output can be folded in with
``--versions``. Everything printed passes the redactor first — a report is the
single most-copied artefact this plugin produces.

Severity is the four-name vocabulary the findings catalog declares —
``critical`` > ``high`` > ``warn`` > ``info`` — and it is read, never guessed: a
value outside it aborts the render with a named schema error rather than being
dropped from the output, because a critical finding that disappears silently is
worse than no report at all.

Exit codes
----------
    0  rendered, no critical or high finding
    1  runtime error (no input, unreadable input, unknown schema, incomplete snapshot)
    5  at least one critical- or high-severity finding
    6  warn-severity findings only
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, HERE)

import config as cfgmod          # noqa: E402
import redact                    # noqa: E402

HEALTH_SCHEMA = "openclaw-ops/health/1"
REPORT_SCHEMA = "openclaw-ops/report/1"
EXIT_OK, EXIT_RUNTIME, EXIT_BLOCKING_FINDINGS, EXIT_WARN_FINDINGS = 0, 1, 5, 6

# One vocabulary, ascending, and it is the one the findings catalog declares. A
# severity outside it used to be silently discarded here — a critical finding could
# vanish from the report with no message at all — so every read of it now goes
# through severity_rank() and fails loudly instead.
SEVERITIES = ("info", "warn", "high", "critical")
SEVERITY_RANK = {name: index for index, name in enumerate(SEVERITIES)}
SEVERITY_MARK = {"critical": "CRITICAL", "high": "HIGH", "warn": "warn", "info": "info"}
# The two classes that make a run "not clean" — exit 5, and the reason a monitor pages.
BLOCKING = ("critical", "high")


class SchemaError(Exception):
    """The input does not carry what this renderer is contractually given."""


def severity_rank(value, where):
    """Guarded lookup. An unknown severity is a schema error, never a silent drop."""
    try:
        return SEVERITY_RANK[value]
    except (KeyError, TypeError):
        raise SchemaError("unknown severity %r in %s: the vocabulary is %s"
                          % (value, where, ", ".join(SEVERITIES)))


def severity_mark(item):
    value = item.get("severity")
    severity_rank(value, "finding %r" % item.get("finding_id"))
    return SEVERITY_MARK[value]


def require(mapping, key, where):
    """Read a field the snapshot schema promises, or say which one is missing."""
    value = mapping.get(key)
    if value is None:
        raise SchemaError(
            "%s is missing the required field %r — the input is not a complete %s "
            "document; re-run healthcheck.py --snapshot to produce one"
            % (where, key, HEALTH_SCHEMA))
    return value


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #

def read_json(path):
    if path == "-":
        return json.loads(sys.stdin.read())
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def snapshot_dir(cfg, override=None):
    if override:
        return os.path.abspath(os.path.expanduser(override))
    configured = cfg.policy("snapshot_dir") if cfg.present else None
    base = configured or os.path.join(
        os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
        "openclaw-ops")
    return os.path.join(os.path.abspath(os.path.expanduser(base)), "health")


def list_snapshots(directory):
    """Every health snapshot in the directory, oldest first."""
    try:
        names = sorted(n for n in os.listdir(directory)
                       if n.startswith("health-") and n.endswith(".json"))
    except OSError:
        return []
    return [os.path.join(directory, n) for n in names]


def load_history(directory, before=None):
    """Load every snapshot, oldest first, optionally only those before a timestamp."""
    out = []
    for path in list_snapshots(directory):
        try:
            doc = read_json(path)
        except (OSError, ValueError):
            continue
        if doc.get("schema") != HEALTH_SCHEMA:
            continue
        if before and str(doc.get("generated_at", "")) >= before:
            continue
        doc["_path"] = path
        out.append(doc)
    out.sort(key=lambda d: str(d.get("generated_at", "")))
    return out


# --------------------------------------------------------------------------- #
# delta
# --------------------------------------------------------------------------- #

def index_findings(doc):
    """``finding_id -> finding`` for one snapshot."""
    out = {}
    for inst in doc.get("instances", []):
        for item in inst.get("findings", []):
            out[item["finding_id"]] = item
    return out


def index_instances(doc):
    return {inst["name"]: inst for inst in doc.get("instances", [])}


def _stamp(text):
    if not text:
        return None
    try:
        return datetime.datetime.strptime(str(text), "%Y-%m-%dT%H:%M:%SZ")\
            .replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def first_seen_map(history):
    """Earliest snapshot timestamp each finding id appeared in."""
    seen = {}
    for doc in history:
        stamp = doc.get("generated_at")
        for finding_id in index_findings(doc):
            seen.setdefault(finding_id, stamp)
    return seen


def compute_delta(current, previous, history):
    """New / resolved / persisting findings, plus per-instance transitions."""
    now_findings = index_findings(current)
    old_findings = index_findings(previous) if previous else {}
    seen = first_seen_map(history + [current])
    now_stamp = _stamp(current.get("generated_at"))

    for finding_id, item in now_findings.items():
        item["first_seen"] = seen.get(finding_id, current.get("generated_at"))
        first = _stamp(item["first_seen"])
        item["age_days"] = round((now_stamp - first).total_seconds() / 86400.0, 1) \
            if (now_stamp and first) else None

    new = sorted(set(now_findings) - set(old_findings))
    resolved = sorted(set(old_findings) - set(now_findings))
    persisting = sorted(set(now_findings) & set(old_findings))

    transitions = []
    now_inst = index_instances(current)
    old_inst = index_instances(previous) if previous else {}
    for name in sorted(set(now_inst) | set(old_inst)):
        before, after = old_inst.get(name), now_inst.get(name)
        if before is None:
            transitions.append({"instance": name, "field": "presence",
                                "from": "absent", "to": "present"})
            continue
        if after is None:
            transitions.append({"instance": name, "field": "presence",
                                "from": "present", "to": "absent"})
            continue
        for field in ("state", "health", "liveness"):
            if before.get(field) != after.get(field):
                transitions.append({"instance": name, "field": field,
                                    "from": before.get(field), "to": after.get(field)})
        for key in ("version", "plugins", "cron_total", "cron_duplicates", "memory_db_bytes",
                    "credentials", "embeddings"):
            was, now = (before.get("metrics") or {}).get(key), (after.get("metrics") or {}).get(key)
            if was != now and (was is not None or now is not None):
                transitions.append({"instance": name, "field": "metrics.%s" % key,
                                    "from": was, "to": now})
    return {
        "baseline": (previous or {}).get("generated_at"),
        "baseline_path": (previous or {}).get("_path"),
        "new": [now_findings[f] for f in new],
        "resolved": [old_findings[f] for f in resolved],
        "persisting": [now_findings[f] for f in persisting],
        "transitions": transitions,
    }


def stale_findings(delta, min_age_days=14.0):
    """Findings nobody has moved on. The quietest and most useful section."""
    rows = [f for f in delta["persisting"]
            if (f.get("age_days") or 0) >= min_age_days]
    return sorted(rows, key=lambda f: -(f.get("age_days") or 0))


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #

def _sev_rank(item):
    return -severity_rank(item.get("severity"),
                          "finding %r" % item.get("finding_id"))


def _table(heads, rows):
    if not rows:
        return ["_(none)_", ""]
    out = ["| " + " | ".join(heads) + " |",
           "|" + "|".join(["---"] * len(heads)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |")
    out.append("")
    return out


def _age(item):
    age = item.get("age_days")
    if age is None:
        return "new"
    if age < 1:
        return "today"
    return "%.0f day%s" % (age, "" if round(age) == 1 else "s")


def render_markdown(current, delta, versions=None, title=None, severity_min="info",
                    stale_days=14.0):
    counts = current.get("counts") or {}
    host = current.get("host") or {}
    lines = []
    lines.append("# %s" % (title or "OpenClaw fleet report"))
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| generated | %s |" % current.get("generated_at"))
    lines.append("| selector | `%s` |" % current.get("selector"))
    lines.append("| host | %s |" % (host.get("label") or host.get("fingerprint") or "unrecorded"))
    lines.append("| instances | %s |" % counts.get("instances"))
    lines.append("| findings | %s critical, %s high, %s warn, %s info |"
                 % (counts.get("critical", 0), counts.get("high", 0),
                    counts.get("warn", 0), counts.get("info", 0)))
    lines.append("| baseline | %s |" % (delta.get("baseline") or "none — first run, no delta"))
    lines.append("")

    # -- fleet ------------------------------------------------------------- #
    lines.append("## Fleet")
    lines.append("")
    lines.append("`HEALTH` is what the instance says about itself. `LIVENESS` is what it was "
                 "observed to do. They are computed from disjoint evidence, so a disagreement "
                 "between the two columns is a result, not a rendering artefact.")
    lines.append("")
    rows = []
    for inst in current.get("instances", []):
        metrics = inst.get("metrics") or {}
        where = "instance %r in the snapshot" % inst.get("name", "<unnamed>")
        liveness = require(inst, "liveness", where)
        rows.append([
            require(inst, "name", "an instance record in the snapshot"),
            inst.get("state") or "?", require(inst, "health", where),
            liveness + (" **diverges**" if inst.get("divergence") else ""),
            metrics.get("version") or "-",
            metrics.get("credentials") or "-",
            "-" if metrics.get("log_age_hours") is None else "%.1fh" % metrics["log_age_hours"],
            _count_findings(inst),
        ])
    lines += _table(["instance", "state", "health", "liveness", "version", "creds",
                     "log age", "findings"], rows)

    diverging = [i for i in current.get("instances", []) if i.get("divergence")]
    if diverging:
        lines.append("### Divergence")
        lines.append("")
        for inst in diverging:
            reason = next((f["message"] for f in inst.get("findings", [])
                           if f["id"].startswith("fleet.liveness.")), "")
            lines.append("- **%s** — health `%s`, liveness `%s`. %s"
                         % (inst["name"], inst.get("health"), inst.get("liveness"), reason))
        lines.append("")

    # -- delta ------------------------------------------------------------- #
    lines.append("## Change since %s" % (delta.get("baseline") or "the first run"))
    lines.append("")
    if not delta.get("baseline"):
        lines.append("No earlier snapshot to compare against. Every finding below is recorded as "
                     "first seen now; the next run will produce a real delta.")
        lines.append("")
    else:
        lines.append("**New (%d)**" % len(delta["new"]))
        lines.append("")
        lines += _table(["severity", "finding", "message"],
                        [[severity_mark(f), "`%s`" % f["finding_id"],
                          f["message"]] for f in sorted(delta["new"], key=_sev_rank)])
        lines.append("**Resolved (%d)**" % len(delta["resolved"]))
        lines.append("")
        lines += _table(["finding", "was"],
                        [["`%s`" % f["finding_id"], f["message"]] for f in delta["resolved"]])
        transitions = delta.get("transitions") or []
        lines.append("**Transitions (%d)**" % len(transitions))
        lines.append("")
        lines += _table(["instance", "field", "from", "to"],
                        [[t["instance"], "`%s`" % t["field"], t["from"], t["to"]]
                         for t in transitions])

    stale = stale_findings(delta, stale_days)
    if stale:
        lines.append("## Not moving")
        lines.append("")
        lines.append("Present in every snapshot for at least %.0f days. Age is measured from the "
                     "first snapshot containing the finding id, so it survives report regeneration."
                     % stale_days)
        lines.append("")
        lines += _table(["age", "severity", "finding", "message"],
                        [[_age(f), severity_mark(f),
                          "`%s`" % f["finding_id"], f["message"]] for f in stale])

    # -- findings ---------------------------------------------------------- #
    lines.append("## Findings")
    lines.append("")
    floor = severity_rank(severity_min, "--severity-min")
    printed = 0
    for severity in reversed(SEVERITIES):
        if SEVERITY_RANK[severity] < floor:
            continue
        group = [f for inst in current.get("instances", [])
                 for f in inst.get("findings", [])
                 if severity_rank(f.get("severity"),
                                  "finding %r" % f.get("finding_id")) == SEVERITY_RANK[severity]]
        if not group:
            continue
        lines.append("### %s (%d)" % (severity, len(group)))
        lines.append("")
        for item in sorted(group, key=lambda f: f["finding_id"]):
            printed += 1
            lines.append("- **`%s`** — %s" % (item["finding_id"], item["message"]))
            detail = ["seen %s" % _age(item), "source `%s`" % item.get("source", "unknown")]
            if item.get("evidence"):
                detail.append("evidence: %s" % str(item["evidence"])[:160])
            lines.append("  - %s" % " · ".join(detail))
            if item.get("fix"):
                lines.append("  - fix: %s" % item["fix"])
            lines.append("  - `/openclaw-ops:repair %s --issue %s`"
                         % (item["instance"], item["id"]))
        lines.append("")
    if not printed:
        lines.append("_No findings at or above `%s`._" % severity_min)
        lines.append("")

    # -- versions ---------------------------------------------------------- #
    if versions:
        lines += _render_versions(versions)

    lines.append("---")
    lines.append("")
    lines.append("Produced by `report.py` from a `healthcheck.py --snapshot` run. Finding ids are "
                 "stable across runs; that is what makes two reports comparable. Secret values are "
                 "never printed — presence, expiry and an `fp:` fingerprint are.")
    return "\n".join(lines).rstrip() + "\n"


def _count_findings(inst):
    counts = {}
    for item in inst.get("findings", []):
        severity_rank(item.get("severity"), "finding %r" % item.get("finding_id"))
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    if not counts:
        return "-"
    return " ".join("%s:%d" % (s, counts[s]) for s in SEVERITIES if s in counts)


def _render_versions(versions):
    lines = ["## Versions", ""]
    channel = versions.get("channel") or {}
    drift = versions.get("drift") or {}
    lines.append("Channel `%s` (dist-tag `%s`) points at **%s**. Installed: %d distinct version(s)."
                 % (channel.get("name"), channel.get("tag"),
                    channel.get("version") or "unresolved", drift.get("distinct", 0)))
    lines.append("")
    verdict = versions.get("gate")
    if verdict:
        lines.append("Target `%s`: **%s**" % (verdict["target"], verdict["verdict"]))
        lines.append("")
        for reason in verdict.get("reasons", []):
            lines.append("- %s" % reason)
        lines.append("")
    lines += _table(["instance", "version", "vs target", "image"],
                    [[r["name"], r.get("version") or "-", r.get("vs_target", "unknown"),
                      r.get("image") or "-"] for r in versions.get("instances", [])])
    if drift.get("moving_tags"):
        lines.append("Moving image tags on: %s. A moving tag is rebuilt under the same name, so "
                     "it cannot serve as a rollback target — pin a digest before upgrading."
                     % ", ".join(drift["moving_tags"]))
        lines.append("")
    return lines


# --------------------------------------------------------------------------- #

def build_parser():
    ap = argparse.ArgumentParser(
        prog="report.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=None,
                    help="health snapshot to render ('-' for stdin; default: the newest snapshot "
                         "in the state directory)")
    ap.add_argument("--compare-with", default="auto",
                    help="baseline snapshot: a path, 'auto' (newest older run), or 'none'")
    ap.add_argument("--versions", default=None, help="versions.py --json output to fold in")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out", default=None, help="write here instead of stdout")
    ap.add_argument("--title", default=None)
    ap.add_argument("--severity-min", choices=list(SEVERITIES), default="info",
                    help="lowest severity printed in the findings section (ascending: %s)"
                         % ", ".join(SEVERITIES))
    ap.add_argument("--stale-days", type=float, default=14.0,
                    help="age at which a persisting finding is listed as not moving")
    ap.add_argument("--state-dir", default=None, help="override the snapshot directory")
    ap.add_argument("--config", default=None, help="explicit fleet config path")
    ap.add_argument("--no-history", action="store_true",
                    help="do not scan older snapshots; ages become unknown")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = cfgmod.load_config(args.config)
    directory = snapshot_dir(cfg, args.state_dir)

    if args.input:
        try:
            current = read_json(args.input)
        except (OSError, ValueError) as exc:
            sys.stderr.write("error: cannot read %s: %s\n" % (args.input, exc))
            return EXIT_RUNTIME
    else:
        snaps = list_snapshots(directory)
        if not snaps:
            sys.stderr.write("error: no snapshot given and none found in %s. Run "
                             "'healthcheck.py --snapshot' first.\n" % directory)
            return EXIT_RUNTIME
        current = read_json(snaps[-1])
        current["_path"] = snaps[-1]

    if current.get("schema") != HEALTH_SCHEMA:
        sys.stderr.write("error: input is %r, expected %r\n"
                         % (current.get("schema"), HEALTH_SCHEMA))
        return EXIT_RUNTIME

    history = [] if args.no_history else load_history(
        directory, before=current.get("generated_at"))
    previous = None
    if args.compare_with == "auto":
        previous = history[-1] if history else None
    elif args.compare_with not in ("none", ""):
        try:
            previous = read_json(args.compare_with)
            previous["_path"] = args.compare_with
        except (OSError, ValueError) as exc:
            sys.stderr.write("error: cannot read baseline %s: %s\n" % (args.compare_with, exc))
            return EXIT_RUNTIME

    versions = None
    if args.versions:
        try:
            versions = read_json(args.versions)
        except (OSError, ValueError) as exc:
            sys.stderr.write("warning: cannot read %s: %s\n" % (args.versions, exc))

    try:
        body = build_body(args, current, previous, history, versions)
    except SchemaError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME

    scrubbed = redact.scrub_stream(body)
    if args.out:
        path = os.path.abspath(os.path.expanduser(args.out))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(scrubbed.text)
        sys.stderr.write("wrote %s\n" % path)
    else:
        sys.stdout.write(scrubbed.text)
    if scrubbed.count:
        sys.stderr.write(scrubbed.marker() + "\n")

    counts = current.get("counts") or {}
    if any(counts.get(name) for name in BLOCKING):
        return EXIT_BLOCKING_FINDINGS
    if counts.get("warn"):
        return EXIT_WARN_FINDINGS
    return EXIT_OK


def build_body(args, current, previous, history, versions):
    """Render the requested format. Raises SchemaError on an incomplete snapshot."""
    delta = compute_delta(current, previous, history)
    if args.format == "json":
        body = json.dumps({
            "schema": REPORT_SCHEMA,
            "generated_at": current.get("generated_at"),
            "source": current.get("_path") or args.input,
            "counts": current.get("counts"),
            "delta": {
                "baseline": delta["baseline"],
                "new": [f["finding_id"] for f in delta["new"]],
                "resolved": [f["finding_id"] for f in delta["resolved"]],
                "persisting": [{"finding_id": f["finding_id"], "age_days": f.get("age_days"),
                                "severity": f["severity"]} for f in delta["persisting"]],
                "transitions": delta["transitions"],
            },
            "instances": current.get("instances", []),
            "versions": versions,
        }, indent=2, ensure_ascii=False)
    else:
        body = render_markdown(current, delta, versions=versions, title=args.title,
                               severity_min=args.severity_min, stale_days=args.stale_days)
    return body


if __name__ == "__main__":
    sys.exit(main())
