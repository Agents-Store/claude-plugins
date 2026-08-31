#!/usr/bin/env python3
"""clone.py — materialise a new instance from the reference one.

    clone.py <new-name> [--from <reference>] [--port auto|<n>] [--plan|--apply] [--yes]

Scope, stated up front
----------------------
This script owns the **deterministic** half of cloning: name validation, a free
port that is genuinely free, the isolation preflight, and copying the reference
layout with the instance name and port substituted. It writes files and creates
directories. It does not start anything, and it does not mint credentials.

Minting a machine identity, granting it read access to a secret project and
performing the provider logins are **not implemented here**. Two reasons, both
deliberate: those steps are deployment-specific, and every one of them handles
values this plugin has committed never to touch. If the fleet config names an
external provisioner, it is invoked with the resolved parameters; otherwise the
remaining manual steps are printed. A printed step is honest — a silently skipped
one is how a clone ends up looking finished while it has no credentials.

The isolation preflight
-----------------------
Upstream requires four things to be unique per gateway: ``OPENCLAW_CONFIG_PATH``,
``OPENCLAW_STATE_DIR``, ``agents.defaults.workspace`` and ``gateway.port``. Two
instances that share any of them do not fail loudly — gateway startup enforces
unique state-directory ownership, so the *second* one to start loses, which
usually means the clone appears to work and something else breaks tomorrow.

The port check is about the **published host port**. The in-container port may
repeat across instances because each container has its own network namespace —
unless the reference runs with host networking, which is checked explicitly,
because in that case the in-container port must differ too.

A free port means free by four measures, not one: not published by any container
on this host, not written into any compose file of the fleet (a stopped instance
still owns its port), not bindable-in-use right now, and not already claimed by
another instance in the fleet config.

Credentials are never copied
----------------------------
The reference's auth material is deliberately excluded from the copy set. An
``api_key`` or a static token would be portable; an OAuth profile is not, and
copying one gives two instances a single refresh chain — the exact configuration
that logs one of them out at the next token rotation.

Exit codes
----------
    0  plan rendered, or clone applied
    1  runtime error
    2  fleet config missing or invalid (required for --apply)
    3  refused: bad name, gate not satisfied, collision
    4  reference instance not found
    5  isolation preflight failed
"""

import argparse
import json
import os
import re
import shutil
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, HERE)

import config as cfgmod          # noqa: E402
import discovery                 # noqa: E402
import gate                      # noqa: E402
import redact                    # noqa: E402

EXIT_OK, EXIT_RUNTIME, EXIT_CONFIG, EXIT_REFUSED, EXIT_NO_REF, EXIT_PREFLIGHT = 0, 1, 2, 3, 4, 5

# Same shape the fleet-config schema accepts as an instance key, minus uppercase:
# the name becomes part of a compose project name and of several paths.
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{1,62}$")
RESERVED_NAMES = {"all", "managed", "reference", "canary", "standard", "legacy", "neighbour"}

# Mount roles that carry credentials. Never copied into a clone.
CREDENTIAL_ROLES = ("auth_secrets", "claude_dir", "claude_json", "codex_home",
                    "claude_share")
PORT_IN_TEXT = re.compile(r"(?:(\d{1,3}(?:\.\d{1,3}){3}|\[[0-9a-fA-F:]+\]):)?(\d{2,5}):\d{2,5}")


# --------------------------------------------------------------------------- #
# name
# --------------------------------------------------------------------------- #

def validate_name(name, records, cfg, prefix):
    """Every reason a name cannot be used, collected rather than short-circuited."""
    problems = []
    if not NAME_RE.match(name or ""):
        problems.append("%r is not a usable instance name: lowercase letters, digits, dot, dash "
                        "and underscore, 2-63 characters, starting with a letter or digit" % name)
    if name in RESERVED_NAMES:
        problems.append("%r is a selector keyword and would be unaddressable" % name)
    if prefix and name.startswith(prefix):
        problems.append("%r already starts with the fleet prefix %r — the name is the part AFTER "
                        "the prefix" % (name, prefix))
    lowered = {r["name"].lower() for r in records}
    if (name or "").lower() in lowered:
        problems.append("an instance named %r already exists on this host" % name)
    if cfg.present:
        for existing, spec in cfg.instances().items():
            if existing.lower() == (name or "").lower():
                problems.append("%r is already in the fleet config" % name)
            if name in ((spec or {}).get("aliases") or []):
                problems.append("%r is already an alias of %r" % (name, existing))
    return problems


# --------------------------------------------------------------------------- #
# ports
# --------------------------------------------------------------------------- #

def compose_file_ports(records, timeout=20):
    """Ports written into any compose file of the fleet, running or not.

    A stopped instance publishes nothing and still owns its port. Reading only
    the live container list is how a clone lands on the port of the instance
    somebody stopped last week.
    """
    ports, files = set(), set()
    for rec in records:
        for path in (rec.get("compose") or {}).get("config_files") or []:
            files.add(path)
    for path in sorted(files):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read(400000)
        except OSError:
            continue
        for match in PORT_IN_TEXT.finditer(text):
            try:
                ports.add(int(match.group(2)))
            except ValueError:
                continue
    return ports


def docker_published_ports(timeout=20):
    """Every host port published by any container on this host, ours or not."""
    ports = set()
    rc, out, _err = discovery.run(["docker", "ps", "-a", "--format", "{{json .}}"],
                                  timeout=timeout)
    if rc != 0:
        return ports
    for line in (out or "").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        for match in re.finditer(r"(?:^|,)\s*(?:[\d.]+|\[[0-9a-fA-F:]+\]):(\d{2,5})->",
                                 row.get("Ports") or ""):
            ports.add(int(match.group(1)))
    return ports


def port_in_use(port, host="127.0.0.1"):
    """Is something listening right now? The only measure that catches a
    non-container process squatting on the port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.4)
    try:
        sock.bind((host, port))
        return False
    except OSError:
        return True
    finally:
        sock.close()


def choose_port(requested, records, low, high):
    """Pick a host port, or explain precisely why the requested one is refused."""
    taken = {p for p in (
        [(r.get("port") or {}).get("host_port") for r in records]) if p}
    taken |= compose_file_ports(records)
    taken |= docker_published_ports()
    if requested and requested != "auto":
        port = int(requested)
        reasons = []
        if port in taken:
            reasons.append("already published or written into a compose file of this fleet")
        if port_in_use(port):
            reasons.append("something is listening on it right now")
        return (port, reasons, sorted(taken))
    for port in range(low, high + 1):
        if port in taken or port_in_use(port):
            continue
        return (port, [], sorted(taken))
    return (None, ["no free port in range %d-%d" % (low, high)], sorted(taken))


# --------------------------------------------------------------------------- #
# reference facts
# --------------------------------------------------------------------------- #

def container_env(record, names, timeout=20):
    """Read named environment variables from the reference container.

    Only the listed names are extracted and they are all paths. The rest of the
    environment is never materialised — it is the single richest source of secret
    values on the host.
    """
    cid = (record.get("container") or {}).get("id")
    out = {name: None for name in names}
    if not cid:
        return out, None
    rc, text, err = discovery.run(
        ["docker", "inspect", "--format", "{{json .Config.Env}}", cid], timeout=timeout)
    if rc != 0:
        return out, (err or "").strip().splitlines()[:1]
    try:
        rows = json.loads((text or "").strip() or "[]")
    except ValueError:
        return out, "container environment is not readable as JSON"
    for row in rows or []:
        key, _sep, value = str(row).partition("=")
        if key in out:
            out[key] = value
    return out, None


def network_mode(record, timeout=20):
    cid = (record.get("container") or {}).get("id")
    if not cid:
        return None
    rc, out, _err = discovery.run(
        ["docker", "inspect", "--format", "{{.HostConfig.NetworkMode}}", cid], timeout=timeout)
    return (out or "").strip() if rc == 0 else None


def read_config_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except (OSError, ValueError) as exc:
        return None, str(exc)


def workspace_of(config_doc):
    try:
        return ((config_doc or {}).get("agents") or {}).get("defaults", {}).get("workspace")
    except AttributeError:
        return None


# --------------------------------------------------------------------------- #
# isolation preflight
# --------------------------------------------------------------------------- #

def isolation_preflight(new_facts, records, ref_record, timeout=20):
    """The four uniqueness requirements, checked against every known instance.

    Returns ``(rows, problems)``. ``rows`` is shown in the plan whether or not it
    passes: a precheck that prints only its passes is decoration.
    """
    rows, problems = [], []
    existing = {}
    for rec in records:
        env, _err = container_env(rec, ["OPENCLAW_CONFIG_PATH", "OPENCLAW_STATE_DIR"],
                                  timeout=timeout)
        paths = rec.get("paths") or {}
        cfg_doc, _e = read_config_json(paths.get("config_file") or "")
        existing[rec["name"]] = {
            "OPENCLAW_CONFIG_PATH": env.get("OPENCLAW_CONFIG_PATH") or paths.get("config_file"),
            "OPENCLAW_STATE_DIR": env.get("OPENCLAW_STATE_DIR") or paths.get("state_dir"),
            "workspace": workspace_of(cfg_doc),
            "host_port": (rec.get("port") or {}).get("host_port"),
        }
    for key, label in (("OPENCLAW_CONFIG_PATH", "config path"),
                       ("OPENCLAW_STATE_DIR", "state directory"),
                       ("workspace", "agents.defaults.workspace"),
                       ("host_port", "published host port")):
        value = new_facts.get(key)
        clash = sorted(name for name, facts in existing.items()
                       if value is not None and facts.get(key) == value)
        rows.append({"requirement": label, "value": value,
                     "unique": not clash and value is not None,
                     "clashes_with": clash})
        if value is None:
            problems.append("%s for the clone is unknown — uniqueness cannot be asserted, and an "
                            "unasserted uniqueness requirement is a failed one" % label)
        elif clash:
            problems.append("%s %r is already used by: %s" % (label, value, ", ".join(clash)))
    mode = network_mode(ref_record, timeout=timeout)
    rows.append({"requirement": "network namespace", "value": mode or "unknown",
                 "unique": mode not in ("host",), "clashes_with": []})
    if mode == "host":
        problems.append("the reference runs with host networking, so the IN-CONTAINER gateway port "
                        "must differ too — the published-port check is not sufficient here")
    return rows, problems


# --------------------------------------------------------------------------- #
# materialisation
# --------------------------------------------------------------------------- #

def _name_pattern(name):
    """Match the instance name as a component, with dash and dot counting as boundaries.

    The name is embedded in compound identifiers — container names, file names,
    path segments — that join it with a dash. A word boundary that treats a dash
    as part of the word leaves those compounds pointing at the reference, so the
    clone inherits the reference's container name and refuses to start next to it.
    Only alphanumerics and the underscore block a match.
    """
    return r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(name)


def substitute(text, ref_name, new_name, ref_port, new_port):
    """Rewrite the reference's own name and port, counting every replacement.

    Two counts matter, in opposite directions. Zero name substitutions means the
    template never mentions the instance, so the clone would share every path with
    its source. A non-zero LEFTOVER count means the opposite failure: some spelling
    of the reference name survived and the clone carries a foreign identifier. Both
    are preflight failures rather than quiet successes.
    """
    changes = []
    pattern = _name_pattern(ref_name)
    out, count = re.subn(pattern, new_name, text)
    changes.append({"rule": "instance name %r -> %r" % (ref_name, new_name), "count": count})
    if ref_port and new_port:
        out, pcount = re.subn(r"(?<!\d)%d(?!\d)" % ref_port, str(new_port), out)
        changes.append({"rule": "host port %d -> %d" % (ref_port, new_port), "count": pcount})
    leftover = None if re.search(pattern, new_name) else len(re.findall(pattern, out))
    changes.append({"rule": "occurrences of %r surviving substitution" % ref_name,
                    "count": leftover})
    return out, changes


def plan_materialisation(ref_record, new_name, new_port, prefix, ref_name):
    """Build the list of file operations, without performing any of them."""
    ops, notes = [], []
    config_files = (ref_record.get("compose") or {}).get("config_files") or []
    if not config_files:
        return None, ["the reference has no compose file recorded; there is nothing to clone from"]
    ref_file = config_files[0]
    ref_dir = os.path.dirname(ref_file)
    compose_root = os.path.dirname(ref_dir)
    new_project = "%s%s" % (prefix, new_name)
    new_dir = os.path.join(compose_root, new_project)
    new_file = os.path.join(new_dir, os.path.basename(ref_file).replace(ref_name, new_name))
    ref_port = (ref_record.get("port") or {}).get("host_port")

    try:
        with open(ref_file, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, ["cannot read the reference compose file: %s" % exc]
    rendered, changes = substitute(text, ref_name, new_name, ref_port, new_port)
    warnings = []
    if changes[0]["count"] == 0:
        warnings.append("the reference compose file never names the instance, so nothing in it "
                        "diverges for the clone — the two would share every path. Templating the "
                        "deployment is a prerequisite for cloning it.")
    leftover = next((c["count"] for c in changes if c["rule"].startswith("occurrences")), None)
    if leftover:
        warnings.append("%d occurrence(s) of %r survive substitution in the rendered compose file: "
                        "the clone would carry an identifier belonging to the reference"
                        % (leftover, ref_name))
    ops.append({"op": "mkdir", "path": new_dir, "mode": "0755"})
    ops.append({"op": "write", "path": new_file, "source": ref_file,
                "bytes": len(rendered), "changes": changes})

    paths = ref_record.get("paths") or {}
    new_paths = {}
    for role, host_path in sorted(paths.items()):
        if role in ("extra", "config_file") or not isinstance(host_path, str):
            continue
        if role in CREDENTIAL_ROLES:
            notes.append("%s (%s) is credential material and is NOT copied: OAuth profiles are "
                         "not portable and a shared refresh chain logs one of the two instances "
                         "out" % (role, host_path))
            if ref_name in host_path:
                target = host_path.replace(ref_name, new_name)
                new_paths[role] = target
                ops.append({"op": "mkdir", "path": target, "mode": "0700",
                            "note": "empty: credentials are established later, never copied"})
            continue
        if ref_name not in host_path:
            notes.append("%s (%s) does not carry the instance name — treated as shared and left "
                         "as is" % (role, host_path))
            new_paths[role] = host_path
            continue
        target = host_path.replace(ref_name, new_name)
        new_paths[role] = target
        ops.append({"op": "mkdir", "path": target, "mode": "0700"})

    ref_config = paths.get("config_file")
    new_state = new_paths.get("state_dir")
    if ref_config and os.path.isfile(ref_config) and new_state:
        new_config = os.path.join(new_state, os.path.basename(ref_config))
        ops.append({"op": "copy-patch", "path": new_config, "source": ref_config,
                    "note": "instance name and port substituted; secret references are copied as "
                            "references and never resolved"})
        new_paths["config_file"] = new_config
    return {"project": new_project, "dir": new_dir, "file": new_file, "ops": ops,
            "paths": new_paths, "ref_file": ref_file, "ref_port": ref_port,
            "warnings": warnings}, notes


def apply_materialisation(material, ref_name, new_name, new_port):
    """Perform the planned operations. Returns the list of paths created."""
    created = []
    for op in material["ops"]:
        if op["op"] == "mkdir":
            os.makedirs(op["path"], mode=int(op.get("mode", "0700"), 8), exist_ok=True)
            created.append(op["path"])
        elif op["op"] == "write":
            with open(op["source"], "r", encoding="utf-8") as fh:
                text = fh.read()
            rendered, _changes = substitute(text, ref_name, new_name,
                                            material.get("ref_port"), new_port)
            with open(op["path"], "w", encoding="utf-8") as fh:
                fh.write(rendered)
            shutil.copymode(op["source"], op["path"])
            created.append(op["path"])
        elif op["op"] == "copy-patch":
            with open(op["source"], "r", encoding="utf-8") as fh:
                text = fh.read()
            rendered, _changes = substitute(text, ref_name, new_name,
                                            material.get("ref_port"), new_port)
            fd = os.open(op["path"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(rendered)
            shutil.copymode(op["source"], op["path"])
            created.append(op["path"])
    return created


# --------------------------------------------------------------------------- #
# provisioner and manual steps
# --------------------------------------------------------------------------- #

def provisioner_command(cfg, override, params):
    """Resolve the external provisioner, if the deployment named one.

    Placeholders ``{name} {reference} {project} {port} {state_dir} {compose_file}``
    are substituted. The provisioner owns credential minting; this script never
    does.
    """
    block = None
    if override:
        block = {"command": override, "args": []}
    elif cfg.present and isinstance(cfg.data.get("provisioner"), dict):
        block = cfg.data["provisioner"]
    if not block or not block.get("command"):
        return None
    argv = [block["command"]] + list(block.get("args") or [])
    return [str(a).format(**params) for a in argv]


MANUAL_STEPS = [
    "Mint the machine identity for the new instance and grant it read access to the same secret "
    "project the reference uses. This plugin never handles secret values, so this step is yours "
    "or the provisioner's.",
    "Create the per-instance secrets the reference declares. Compare by NAME: the delivered key "
    "names of the clone must match the reference's, and an instance receiving noticeably fewer "
    "keys than its siblings has the wrong project id, not a missing feature.",
    "Register the model backends for the new instance with its own login. Do not copy the "
    "reference's auth profiles: OAuth material is not portable and a shared refresh chain logs "
    "one of the two instances out at the next rotation.",
    "Give the instance its own embedding key rather than sharing one. Changing an embedding key "
    "later changes the index identity and forces a full reindex.",
    "Add the instance to the fleet config with a role and a criticality, then confirm "
    "'fleet.py config --diff' reports it in sync.",
    "Bring it up, then run the health battery against it before giving it any work.",
]


# --------------------------------------------------------------------------- #
# plan assembly
# --------------------------------------------------------------------------- #

def build_plan(new_name, ref_name, material, new_port, preflight_rows, preflight_problems,
               port_reasons, notes, provisioner):
    plan = gate.Plan("clone instance", "R2", new_name)
    plan.set("TARGET", ["new instance %r cloned from %r" % (new_name, ref_name),
                        "compose project %s" % material["project"],
                        "nothing existing is modified: every path below is created"])
    precheck = ["name accepted: %s" % new_name,
                "host port selected: %s%s" % (new_port,
                                              " (" + "; ".join(port_reasons) + ")"
                                              if port_reasons else "")]
    for row in preflight_rows:
        precheck.append("%-28s %-40s %s" % (
            row["requirement"], str(row["value"])[:40],
            "unique" if row["unique"] else "COLLIDES with %s" % ", ".join(row["clashes_with"])
            if row["clashes_with"] else "UNVERIFIED"))
    for problem in preflight_problems:
        precheck.append("FAIL: %s" % problem)
    for note in notes:
        precheck.append("note: %s" % note)
    plan.set("PRECHECK", precheck)

    change, deletions = [], 0
    for op in material["ops"]:
        if op["op"] == "mkdir":
            change.append("+ mkdir  %s%s" % (op["path"],
                                             "   # " + op["note"] if op.get("note") else ""))
        elif op["op"] == "write":
            detail = ", ".join("%s x%s" % (c["rule"], c["count"]) for c in op["changes"]
                               if c["count"])
            change.append("+ write  %s   (%d bytes from %s; %s)"
                          % (op["path"], op["bytes"], op["source"], detail))
        else:
            change.append("+ copy   %s   (from %s; %s)"
                          % (op["path"], op["source"], op.get("note", "")))
    change.append("deletions: %d" % deletions)
    plan.set("CHANGE", change)

    plan.set("BACKUP", [
        "not applicable: this operation only creates paths that do not exist yet, and no existing "
        "file is opened for writing. Verified by the collision checks above — a clash would have "
        "failed the preflight, not overwritten a file."])
    plan.set("IMPACT", [
        "no running instance is touched, restarted or reconfigured",
        "the clone is created stopped and without credentials; it cannot serve traffic until the "
        "remaining steps are done",
        "disk: one compose file plus empty state directories"])
    plan.set("VALIDATE", [
        "fleet.py discover --table   # the new project appears, state 'down', profile 'template'",
        "fleet.py config --diff      # reports the clone as present on the host, absent from the "
        "config"])
    plan.set("ROLLBACK", [
        "rm -rf %s %s" % (material["dir"],
                          " ".join(sorted(set(op["path"] for op in material["ops"]
                                              if op["op"] == "mkdir"
                                              and not op["path"].startswith(material["dir"])))))])
    apply_lines = ["clone.py %s --from %s --port %s --apply --yes"
                   % (new_name, ref_name, new_port)]
    if provisioner:
        apply_lines.append("then the configured provisioner: %s" % " ".join(provisioner))
    else:
        apply_lines.append("then the manual steps printed after the plan (no provisioner is "
                           "configured, so credential minting is not automated)")
    plan.set("APPLY", apply_lines)
    return plan


# --------------------------------------------------------------------------- #

def emit(text):
    result = redact.scrub_stream(text)
    sys.stdout.write(result.text.rstrip("\n") + "\n")
    if result.count:
        sys.stderr.write(result.marker() + "\n")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="clone.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="name of the new instance (without the fleet prefix)")
    ap.add_argument("--from", dest="reference", default=None,
                    help="reference instance to clone (default: the configured reference)")
    ap.add_argument("--port", default="auto", help="'auto' or an explicit host port")
    ap.add_argument("--port-range", default=None,
                    help="LOW-HIGH to search when --port is auto (default: the reference's port +1 "
                         "through +200)")
    ap.add_argument("--plan", action="store_true", help="render the plan and change nothing "
                                                        "(default)")
    ap.add_argument("--apply", action="store_true", help="perform the plan")
    ap.add_argument("--yes", action="store_true", help="required together with --apply")
    ap.add_argument("--provisioner", default=None,
                    help="command that mints credentials for the new instance; overrides the "
                         "fleet config's provisioner block")
    ap.add_argument("--run-provisioner", action="store_true",
                    help="with --apply, also run the provisioner instead of only printing it")
    ap.add_argument("--config", default=None, help="explicit fleet config path")
    ap.add_argument("--prefix", default=None, help="compose project prefix")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=30)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = cfgmod.load_config(args.config)
    for line in cfg.warnings:
        sys.stderr.write("warning: %s\n" % line)
    if args.apply:
        if not cfg.present:
            sys.stderr.write("error: --apply needs a fleet config: without one there is no record "
                             "of which host this is, and the wrong-host preflight cannot run.\n")
            return EXIT_CONFIG
        try:
            cfg.require_writable("clone --apply")
        except cfgmod.ConfigError as exc:
            sys.stderr.write("error: %s\n" % exc)
            return EXIT_CONFIG

    prefix = args.prefix or (cfg.prefix if cfg.present else "openclaw-")
    try:
        records = discovery.discover(prefix=prefix, cfg=cfg, probe=True)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME

    problems = validate_name(args.name, records, cfg, prefix)
    if problems:
        sys.stderr.write("refused:\n  - " + "\n  - ".join(problems) + "\n")
        return EXIT_REFUSED

    ref_name = args.reference or (cfg.reference if cfg.present else None)
    if ref_name and cfg.present:
        ref_name = cfg.canonical_name(ref_name)
    if not ref_name:
        sys.stderr.write("error: no reference instance. Pass --from, or mark one in the fleet "
                         "config so '@reference' resolves.\n")
        return EXIT_NO_REF
    ref_record = next((r for r in records if r["name"] == ref_name), None)
    if ref_record is None:
        sys.stderr.write("error: reference %r not found on this host. Known: %s\n"
                         % (ref_name, ", ".join(r["name"] for r in records) or "(none)"))
        return EXIT_NO_REF
    if ref_record.get("profile") != "template":
        sys.stderr.write("refused: %r has profile %r. Only a template-layout instance is a usable "
                         "clone source; a legacy layout is a migration project.\n"
                         % (ref_name, ref_record.get("profile")))
        return EXIT_REFUSED

    ref_port = (ref_record.get("port") or {}).get("host_port")
    if args.port_range:
        try:
            low, high = (int(p) for p in args.port_range.split("-", 1))
        except ValueError:
            sys.stderr.write("error: --port-range wants LOW-HIGH\n")
            return EXIT_REFUSED
    elif ref_port:
        low, high = ref_port + 1, ref_port + 200
    else:
        sys.stderr.write("error: the reference publishes no host port, so there is no range to "
                         "search. Pass --port or --port-range.\n")
        return EXIT_REFUSED
    new_port, port_reasons, taken = choose_port(args.port, records, low, high)
    if new_port is None or port_reasons:
        sys.stderr.write("refused: port %s unusable: %s\n"
                         % (args.port, "; ".join(port_reasons)))
        return EXIT_REFUSED

    material, notes = plan_materialisation(ref_record, args.name, new_port, prefix, ref_name)
    notes.insert(0, "port %d chosen from the range %d-%d; %d port(s) already claimed by a "
                    "container, a compose file of this fleet or a live listener were excluded"
                 % (new_port, low, high, len(taken)))
    if material is None:
        sys.stderr.write("error:\n  - " + "\n  - ".join(notes) + "\n")
        return EXIT_RUNTIME

    new_facts = {
        "OPENCLAW_CONFIG_PATH": material["paths"].get("config_file"),
        "OPENCLAW_STATE_DIR": material["paths"].get("state_dir"),
        "workspace": None,
        "host_port": new_port,
    }
    ref_cfg_doc, _err = read_config_json((ref_record.get("paths") or {}).get("config_file") or "")
    ref_workspace = workspace_of(ref_cfg_doc)
    if isinstance(ref_workspace, str):
        new_facts["workspace"] = ref_workspace.replace(ref_name, args.name)
    preflight_rows, preflight_problems = isolation_preflight(
        new_facts, records, ref_record, timeout=args.timeout)
    preflight_problems.extend(material.get("warnings") or [])

    params = {"name": args.name, "reference": ref_name, "project": material["project"],
              "port": new_port, "state_dir": material["paths"].get("state_dir") or "",
              "compose_file": material["file"]}
    provisioner = provisioner_command(cfg, args.provisioner, params)

    plan = build_plan(args.name, ref_name, material, new_port, preflight_rows,
                      preflight_problems, port_reasons, notes, provisioner)

    applying = bool(args.apply and args.yes)
    if args.json:
        payload = plan.as_dict()
        payload.update({"instance": args.name, "reference": ref_name, "port": new_port,
                        "material": material, "preflight": preflight_rows,
                        "preflight_problems": preflight_problems,
                        "provisioner": provisioner,
                        "manual_steps": None if provisioner else MANUAL_STEPS})
        emit(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        emit(plan.render())
        if applying:
            emit("APPLYING — the plan above was answered with --apply --yes, so the footer line "
                 "does not apply to this run.")

    if preflight_problems:
        sys.stderr.write("isolation preflight FAILED:\n  - "
                         + "\n  - ".join(preflight_problems) + "\n")
        return EXIT_PREFLIGHT

    if not args.apply:
        if not args.json:
            emit("\nRemaining steps this script does not perform:\n"
                 + "\n".join("  %d. %s" % (i + 1, s) for i, s in enumerate(MANUAL_STEPS)))
        return EXIT_OK

    try:
        # --plan is the offer; --apply --yes is the answer to it. The turn
        # separation is enforced by the command layer, not by re-refusing here.
        gate.gate(plan, yes=args.yes, first_offer=False)
    except gate.GateError as exc:
        sys.stderr.write("refused: %s\n" % exc)
        return EXIT_REFUSED

    try:
        created = apply_materialisation(material, ref_name, args.name, new_port)
    except OSError as exc:
        sys.stderr.write("error: materialisation failed after creating %s: %s\n"
                         % (material["dir"], exc))
        sys.stderr.write("rollback: rm -rf %s\n" % material["dir"])
        return EXIT_RUNTIME
    emit("created:\n" + "\n".join("  %s" % p for p in created))

    if provisioner and args.run_provisioner:
        rc, out, err = discovery.run(provisioner, timeout=max(120, args.timeout))
        emit("provisioner exit %d\n%s" % (rc, redact.scrub(out or err or "")))
        if rc != 0:
            sys.stderr.write("provisioner failed. One failure is a stop, not a retry: a partial "
                             "credential write is worse than none.\n")
            return EXIT_RUNTIME
    elif provisioner:
        emit("\nProvisioner configured but not run. Execute it yourself:\n  %s"
             % " ".join(provisioner))
    if provisioner:
        notes_text = (cfg.data.get("provisioner") or {}).get("notes") if cfg.present else None
        emit("\nThe provisioner covers: %s\nEverything it does not claim stays manual:\n%s"
             % (notes_text or "(the fleet config records no description)",
                "\n".join("  %d. %s" % (i + 1, s) for i, s in enumerate(MANUAL_STEPS))))
    else:
        emit("\nRemaining steps this script does not perform:\n"
             + "\n".join("  %d. %s" % (i + 1, s) for i, s in enumerate(MANUAL_STEPS)))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
