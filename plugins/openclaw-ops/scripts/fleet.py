#!/usr/bin/env python3
"""fleet.py — discover the fleet, resolve a selector, manage the fleet config.

    fleet.py discover [--json|--table] [--prefix P] [--no-probe] [--config PATH]
    fleet.py resolve <selector> [--json|--table] [--mutation] [--no-probe]
    fleet.py config (--init | --show | --validate | --diff) [options]

Selector grammar
----------------
    (empty)            every managed instance
    managed            same, written explicitly
    all                everything, alien and unmanaged included — READ ONLY
    @reference         the configured reference instance
    @canary            the configured canary
    @<role>            every instance with that role
    alpha,beta         an explicit list (aliases accepted)
    web-*              a glob over instance names
    managed,-beta      subtraction: managed except beta

A mutation must name its targets. ``all`` is refused for mutations, because a
selector that silently widens as the fleet grows is how a one-instance fix
becomes a fleet-wide incident.

Exit codes
----------
    0  success
    1  runtime error (docker unreachable, sweep failed)
    2  fleet config missing or invalid
    3  selector refused (mutation scope, unmanaged or alien target)
    4  selector matched nothing
"""

import argparse
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import config as cfgmod          # noqa: E402
import discovery                 # noqa: E402
import redact                    # noqa: E402

EXIT_OK, EXIT_RUNTIME, EXIT_CONFIG, EXIT_REFUSED, EXIT_EMPTY = 0, 1, 2, 3, 4


# --------------------------------------------------------------------------- #
# selector
# --------------------------------------------------------------------------- #

class SelectorError(Exception):
    pass


def _matches_term(record, term, cfg):
    name = record["name"]
    if term in ("", "managed"):
        return record.get("managed", False) and record.get("profile") != "alien"
    if term == "all":
        return True
    if term.startswith("@"):
        role = term[1:]
        if role == "reference":
            return name == (cfg.reference if cfg.present else None) or record.get("role") == "reference"
        if role == "canary":
            return name == (cfg.canary if cfg.present else None) or record.get("role") == "canary"
        return record.get("role") == role
    if any(ch in term for ch in "*?["):
        return fnmatch.fnmatch(name, term)
    return name == term or name == cfg.canonical_name(term)


def parse_selector(selector):
    """Split a selector into ``(include_terms, exclude_terms)``."""
    raw = (selector or "").strip()
    if not raw:
        return ["managed"], []
    include, exclude = [], []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("-"):
            exclude.append(part[1:].strip())
        else:
            include.append(part)
    if not include:
        include = ["managed"]
    return include, exclude


def resolve(records, selector, cfg, mutation=False):
    """Apply a selector to discovered records. Raises :class:`SelectorError` on refusal."""
    include, exclude = parse_selector(selector)
    if mutation:
        if not (selector or "").strip():
            raise SelectorError(
                "a mutation must name its targets explicitly. 'all' and the empty selector "
                "are read-only, so a fix cannot silently widen as the fleet grows.")
        if "all" in include:
            raise SelectorError(
                "'all' is a read-only selector: it includes alien, legacy and unmanaged "
                "instances. Name the instances, or use 'managed'.")
    picked = []
    for rec in records:
        if not any(_matches_term(rec, t, cfg) for t in include):
            continue
        if any(_matches_term(rec, t, cfg) for t in exclude):
            continue
        picked.append(rec)
    if mutation:
        refused = []
        for rec in picked:
            if rec.get("profile") == "alien":
                refused.append("%s: failed the layout fingerprint (alien) — inventory only"
                               % rec["name"])
            elif not rec.get("managed", False):
                reason = ("legacy layout — a migration project, not a maintenance target"
                          if rec.get("role") == "legacy" else "manage:false in the fleet config")
                refused.append("%s: %s" % (rec["name"], reason))
        if refused:
            raise SelectorError("mutation refused for:\n  - " + "\n  - ".join(refused))
    return picked


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #

_COLUMNS = [
    ("NAME", lambda r: r.get("name") or "?"),
    ("STATE", lambda r: r.get("state") or "?"),
    ("PROFILE", lambda r: r.get("profile") or "?"),
    ("ROLE", lambda r: r.get("role") or "-"),
    ("MANAGED", lambda r: "yes" if r.get("managed") else "no"),
    ("PORT", lambda r: _port(r)),
    ("VERSION", lambda r: (r.get("capabilities") or {}).get("cli_version") or "-"),
    ("HEALTH", lambda r: (r.get("container") or {}).get("health") or "-"),
    ("LOG-AGE", lambda r: _age(r)),
    ("NOTE", lambda r: _note(r)),
]


def _port(rec):
    port = rec.get("port") or {}
    if not port.get("host_port"):
        return "-"
    mark = "" if port.get("loopback") else "  EXPOSED"
    return "%s:%s%s" % (port.get("host_ip") or "?", port["host_port"], mark)


def _age(rec):
    age = (rec.get("signals") or {}).get("log_age_hours")
    return "-" if age is None else "%.1fh" % age


def _note(rec):
    if rec.get("error"):
        return rec["error"]
    bits = list(rec.get("state_reasons") or []) + list(rec.get("notes") or [])
    return "; ".join(bits) if bits else ""


def render_table(records):
    rows = [[fn(r) for _h, fn in _COLUMNS] for r in records]
    heads = [h for h, _fn in _COLUMNS]
    widths = [max(len(heads[i]), *(len(str(row[i])) for row in rows)) if rows else len(heads[i])
              for i in range(len(heads))]
    out = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(heads)).rstrip()]
    out.append("  ".join("-" * widths[i] for i in range(len(heads))))
    for row in rows:
        out.append("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(heads))).rstrip())
    return "\n".join(out)


def emit(text, as_json=False, payload=None):
    """Everything leaving this process is scrubbed first."""
    body = json.dumps(payload, indent=2, ensure_ascii=False) if as_json else text
    result = redact.scrub_stream(body)
    sys.stdout.write(result.text.rstrip("\n") + "\n")
    if result.count and not as_json:
        sys.stderr.write(result.marker() + "\n")


def warn(cfg):
    for line in cfg.warnings:
        sys.stderr.write("warning: %s\n" % line)
    if cfg.readonly:
        sys.stderr.write("READ-ONLY: %s\n" % cfg.readonly_reason)


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_discover(args):
    cfg = cfgmod.load_config(args.config)
    warn(cfg)
    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=not args.no_probe)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    if args.json:
        emit(None, True, {"config": cfg.as_dict(), "instances": records})
    else:
        emit(render_table(records))
    return EXIT_OK


def cmd_resolve(args):
    cfg = cfgmod.load_config(args.config)
    warn(cfg)
    if args.mutation and cfg.readonly:
        sys.stderr.write("error: mutations refused: %s\n" % cfg.readonly_reason)
        return EXIT_REFUSED
    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=not args.no_probe)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    try:
        picked = resolve(records, args.selector, cfg, mutation=args.mutation)
    except SelectorError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_REFUSED
    if not picked:
        sys.stderr.write("error: selector %r matched no instance\n" % (args.selector or "managed"))
        return EXIT_EMPTY
    if args.json:
        emit(None, True, {"selector": args.selector or "managed",
                          "mutation": bool(args.mutation),
                          "count": len(picked),
                          "names": [r["name"] for r in picked],
                          "instances": picked})
    elif args.table:
        emit(render_table(picked))
    else:
        emit("\n".join(r["name"] for r in picked))
    return EXIT_OK


def cmd_config(args):
    if args.init:
        return _config_init(args)
    cfg = cfgmod.load_config(args.config)
    if args.validate:
        if not cfg.present:
            sys.stderr.write("error: no fleet config found on the resolution ladder\n")
            return EXIT_CONFIG
        warn(cfg)
        if cfg.errors:
            sys.stderr.write("invalid:\n  - " + "\n  - ".join(cfg.errors) + "\n")
            return EXIT_CONFIG
        emit("valid: %s (source: %s)" % (cfg.path, cfg.source))
        return EXIT_OK
    if args.show:
        if not cfg.present:
            sys.stderr.write("error: no fleet config found on the resolution ladder\n")
            return EXIT_CONFIG
        warn(cfg)
        emit(None, True, {"meta": cfg.as_dict(), "config": cfg.data})
        return EXIT_OK
    if args.diff:
        return _config_diff(args, cfg)
    sys.stderr.write("error: choose one of --init / --show / --validate / --diff\n")
    return EXIT_CONFIG


def _config_init(args):
    existing = cfgmod.load_config(args.config)
    if existing.present and not args.force:
        sys.stderr.write("error: %s already exists; pass --force to rewrite it\n" % existing.path)
        return EXIT_CONFIG
    try:
        records = discovery.discover(prefix=args.prefix or "openclaw-", cfg=None,
                                     probe=not args.no_probe)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    compose_root = next((os.path.dirname((r.get("compose") or {}).get("root") or "")
                         for r in records if (r.get("compose") or {}).get("root")), None) or None
    data_root = None
    for rec in records:
        state_dir = (rec.get("paths") or {}).get("state_dir")
        if state_dir:
            data_root = os.path.dirname(os.path.dirname(state_dir)) or None
            break
    draft = cfgmod.init_config(
        records, prefix=args.prefix or "openclaw-", compose_root=compose_root,
        data_root=data_root, reference=args.reference, canary=args.canary,
        host_label=args.host_label, update_channel=args.update_channel,
        soak_days=args.soak_days, stale_log_hours=args.stale_log_hours)
    if args.detect_only:
        emit(None, True, {"draft": draft, "instances": records})
        return EXIT_OK
    path = args.out or cfgmod.default_config_path()
    try:
        written = cfgmod.write_config(draft, path, force=args.force)
    except cfgmod.ConfigError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_CONFIG
    emit("wrote %s (mode 0600, %d instances)\n"
         "Review it: role, criticality, canary and the secret project ids are defaults, "
         "not detections." % (written, len(draft["instances"])))
    return EXIT_OK


def _config_diff(args, cfg):
    if not cfg.present:
        sys.stderr.write("error: no fleet config to compare against\n")
        return EXIT_CONFIG
    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=not args.no_probe)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    live = {r["name"]: r for r in records}
    listed = set(cfg.instances())
    added = sorted(set(live) - listed)
    removed = sorted(listed - set(live))
    changed = []
    for name in sorted(set(live) & listed):
        rec, spec = live[name], cfg.instance(name)
        want_role = spec.get("role", "standard")
        if rec.get("profile") == "legacy" and want_role != "legacy":
            changed.append("%s: layout fingerprint is legacy but the config says role=%s"
                           % (name, want_role))
        if rec.get("profile") == "alien" and want_role != "neighbour":
            changed.append("%s: failed the layout fingerprint but the config manages it" % name)
        if (rec.get("port") or {}).get("loopback") is False and cfg.policy("loopback_only", True):
            changed.append("%s: gateway port is published off loopback (%s)"
                           % (name, (rec.get("port") or {}).get("host_ip")))
    payload = {"config": cfg.path, "added": added, "removed": removed, "changed": changed}
    if args.json:
        emit(None, True, payload)
        return EXIT_OK
    lines = ["config: %s" % cfg.path]
    lines += ["+ %s  (on the host, absent from the config)" % n for n in added]
    lines += ["- %s  (in the config, no compose project on this host)" % n for n in removed]
    lines += ["~ %s" % c for c in changed]
    if not (added or removed or changed):
        lines.append("in sync")
    emit("\n".join(lines))
    return EXIT_OK


# --------------------------------------------------------------------------- #

def build_parser():
    # Shared options live on the subcommands so they may be written after the
    # subcommand, which is where an operator reaches for them.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="explicit fleet config path (bypasses the ladder)")
    common.add_argument("--prefix", help="compose project prefix (default: from config)")
    common.add_argument("--no-probe", action="store_true",
                        help="skip the in-container capability probe and the log-age read")

    ap = argparse.ArgumentParser(
        prog="fleet.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    d = sub.add_parser("discover", parents=[common],
                       help="sweep the host and print every instance")
    d.add_argument("--json", action="store_true")
    d.add_argument("--table", action="store_true")
    d.set_defaults(func=cmd_discover)

    r = sub.add_parser("resolve", parents=[common],
                       help="turn a selector into instance names")
    r.add_argument("selector", nargs="?", default="")
    r.add_argument("--json", action="store_true")
    r.add_argument("--table", action="store_true")
    r.add_argument("--mutation", action="store_true",
                   help="apply mutation scope rules: refuse 'all', refuse unmanaged and alien")
    r.set_defaults(func=cmd_resolve)

    c = sub.add_parser("config", parents=[common],
                       help="create, show, validate or diff the fleet config")
    mode = c.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--show", action="store_true")
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--diff", action="store_true")
    c.add_argument("--out", help="where --init writes (default: /etc or ~/.config)")
    c.add_argument("--force", action="store_true", help="overwrite an existing config")
    c.add_argument("--detect-only", action="store_true",
                   help="print the draft config instead of writing it")
    c.add_argument("--reference", help="instance to mark as the reference")
    c.add_argument("--canary", help="instance to mark as the canary")
    c.add_argument("--host-label", help="free-text label for this host")
    c.add_argument("--update-channel", choices=("stable", "extended-stable", "beta", "dev"),
                   help="release channel the fleet follows (default: stable)")
    c.add_argument("--soak-days", type=int,
                   help="days a version must sit on the channel before it is eligible (default: 14)")
    c.add_argument("--stale-log-hours", type=float,
                   help="log silence after which a green instance is called a zombie (default: 24)")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_config)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except cfgmod.ConfigError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_CONFIG
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
