#!/usr/bin/env python3
"""Fleet discovery from the live Docker state.

Every path this plugin uses is read from the container's own mount table. No
layout constant is hard-coded, because the previous generation of this tooling
was built on assumed paths and was wrong on every real deployment.

The sweep:

1. ``docker compose ls --format json --all`` -> projects matching the prefix.
   ``--all`` is mandatory: without it a stopped instance simply does not exist
   for the plugin, which is the one instance most likely to need attention.
2. gateway container via
   ``docker ps -a --filter label=com.docker.compose.project=<p> --filter name=gateway``.
3. published host port from ``docker inspect``, with an explicit loopback check.
4. **every path from ``.Mounts``**, mapped by container destination to a role.
5. ``ConfigFiles`` from step 1 -> the compose root and the compose file name.
6. a layout fingerprint that separates a template instance from a legacy one —
   the project prefix matches both.
7. a capability probe: is there a wrapper and which verbs does it carry, does
   the CLI answer, is the secret-injection wrapper present in the image.

Anything that looks like an instance but fails the fingerprint is reported as
``alien``. There are no invisible objects: an unrecognised neighbour is a row in
the inventory, not a silent omission.

A failing instance yields ``{"ok": false, "error": ...}`` and the sweep
continues. One broken instance must never blind the operator to the other seven.

Cost: discovery runs exactly one in-container command per running instance, and
only when ``probe=True`` — a read with no side effect. Every other CLI call in
the plugin goes through ``ocexec``, which is the single door.
"""

import json
import os
import re
import shutil
import subprocess
import time

__all__ = [
    "DockerError", "MOUNT_ROLES", "STATES", "PROFILES",
    "run", "docker_available", "compose_projects", "gateway_container",
    "inspect_container", "mount_map", "host_port", "layout_profile",
    "probe_capabilities", "classify_state", "discover_instance", "discover",
    "compose_exec_argv", "cold_run_argv", "instance_name",
]

DEFAULT_TIMEOUT = 30
STATES = ("ok", "degraded", "down", "alien")
PROFILES = ("template", "legacy", "alien")

# Container-side destinations documented by upstream. Host paths are whatever
# the mount table says they are.
MOUNT_ROLES = {
    "/home/node/.openclaw": "state_dir",
    "/home/node/.config/openclaw": "auth_secrets",
    "/home/node/.claude": "claude_dir",
    "/home/node/.claude.json": "claude_json",
    "/home/node/.codex": "codex_home",
    "/home/node/.local/share/claude": "claude_share",
    "/home/node/.local/bin": "claude_local_bin",
}

# Shared trees are recognised by the tail of the destination so the deployment
# is free to place them anywhere.
SHARED_SUFFIXES = {
    "shared-skills": "shared_skills",
    "shared-plugins": "shared_plugins",
}

RESTART_LOOP_THRESHOLD = 3


class DockerError(Exception):
    """Docker is unavailable or refused a command."""


# --------------------------------------------------------------------------- #
# process helpers
# --------------------------------------------------------------------------- #

def run(argv, timeout=DEFAULT_TIMEOUT, input_text=None):
    """Run a command without a shell. Returns ``(rc, stdout, stderr)``.

    stdout and stderr stay separate: banners belong to stderr and must never be
    concatenated into a document that will be parsed.
    """
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            input=input_text, check=False)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after %ss: %s" % (timeout, " ".join(argv[:4]))


def docker_available():
    """Is there a usable Docker daemon here?"""
    if shutil.which("docker") is None:
        return False, "docker binary not on PATH"
    rc, _out, err = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=15)
    if rc != 0:
        return False, (err or "docker daemon not reachable").strip().splitlines()[0]
    return True, None


def _json_lines(text):
    """``docker`` emits either a JSON array or one object per line, by version."""
    text = (text or "").strip()
    if not text:
        return []
    try:
        val = json.loads(text)
        return val if isinstance(val, list) else [val]
    except ValueError:
        pass
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


# --------------------------------------------------------------------------- #
# projects and containers
# --------------------------------------------------------------------------- #

def instance_name(project, prefix):
    """Instance name = compose project name with the fleet prefix removed."""
    if prefix and project.startswith(prefix):
        return project[len(prefix):]
    return project


def compose_projects(prefix=None, timeout=DEFAULT_TIMEOUT):
    """List compose projects, stopped ones included."""
    rc, out, err = run(["docker", "compose", "ls", "--format", "json", "--all"], timeout=timeout)
    if rc != 0:
        raise DockerError("docker compose ls failed: %s" % (err or "rc=%d" % rc).strip())
    rows = []
    for row in _json_lines(out):
        name = row.get("Name") or row.get("name")
        if not name:
            continue
        if prefix and not name.startswith(prefix):
            continue
        files = row.get("ConfigFiles") or row.get("configFiles") or ""
        rows.append({
            "project": name,
            "status": row.get("Status") or row.get("status") or "",
            "config_files": [f for f in str(files).split(",") if f],
        })
    return sorted(rows, key=lambda r: r["project"])


def gateway_container(project, service_hint="gateway", timeout=DEFAULT_TIMEOUT):
    """Find the gateway container of a compose project, running or not."""
    base = ["docker", "ps", "-a",
            "--filter", "label=com.docker.compose.project=%s" % project,
            "--format", "{{json .}}"]
    rc, out, err = run(base + ["--filter", "name=%s" % service_hint], timeout=timeout)
    rows = _json_lines(out) if rc == 0 else []
    if not rows:
        # Name filter missed (service renamed). Fall back to every container in
        # the project and pick the one whose compose service looks like a gateway.
        rc, out, err = run(base, timeout=timeout)
        if rc != 0:
            raise DockerError("docker ps failed for %s: %s" % (project, (err or "").strip()))
        rows = _json_lines(out)
        rows = [r for r in rows
                if service_hint in (r.get("Names") or "") or service_hint in (r.get("Image") or "")] or rows
    if not rows:
        return None
    rows.sort(key=lambda r: (0 if "up" in (r.get("State") or r.get("Status") or "").lower() else 1,
                             r.get("Names") or ""))
    row = rows[0]
    return {
        "id": (row.get("ID") or row.get("Id") or "")[:12],
        "name": (row.get("Names") or "").split(",")[0],
        "image": row.get("Image") or "",
        "status": row.get("Status") or "",
        "state": (row.get("State") or "").lower(),
    }


def inspect_container(container_id, timeout=DEFAULT_TIMEOUT):
    """Full ``docker inspect`` document for one container."""
    rc, out, err = run(["docker", "inspect", container_id], timeout=timeout)
    if rc != 0:
        raise DockerError("docker inspect failed for %s: %s" % (container_id, (err or "").strip()))
    rows = _json_lines(out)
    if not rows:
        raise DockerError("docker inspect returned nothing for %s" % container_id)
    return rows[0]


# --------------------------------------------------------------------------- #
# mounts, ports, layout
# --------------------------------------------------------------------------- #

def mount_map(inspect_doc):
    """Map container destinations to host paths by role.

    Returns ``{role: host_path}`` plus ``extra``: every mount that has no known
    role, so an unexpected bind is visible instead of silently dropped.
    """
    roles, extra = {}, []
    for m in (inspect_doc.get("Mounts") or []):
        dest = m.get("Destination") or ""
        src = m.get("Source") or m.get("Name") or ""
        entry = {
            "source": src,
            "destination": dest,
            "type": m.get("Type"),
            "mode": "rw" if m.get("RW", True) else "ro",
        }
        role = MOUNT_ROLES.get(dest)
        if role is None:
            tail = dest.rstrip("/").rsplit("/", 1)[-1]
            role = SHARED_SUFFIXES.get(tail)
        if role and role not in roles:
            roles[role] = src
        elif role:
            extra.append(entry)
        else:
            extra.append(entry)
    roles["extra"] = extra
    if roles.get("state_dir"):
        roles["config_file"] = os.path.join(roles["state_dir"], "openclaw.json")
    return roles


def host_port(inspect_doc):
    """Published host port for the gateway, with an explicit loopback verdict.

    A published port bypasses the ordinary firewall INPUT chain, so "which
    interface is this bound to" is a security answer, not a cosmetic one.
    """
    ports = ((inspect_doc.get("NetworkSettings") or {}).get("Ports") or {})
    for container_port, bindings in sorted(ports.items()):
        if not bindings:
            continue
        b = bindings[0]
        host_ip = b.get("HostIp") or ""
        try:
            hp = int(b.get("HostPort") or 0) or None
        except (TypeError, ValueError):
            hp = None
        return {
            "container_port": container_port,
            "host_ip": host_ip,
            "host_port": hp,
            "loopback": host_ip in ("127.0.0.1", "::1", "localhost"),
        }
    return {"container_port": None, "host_ip": None, "host_port": None, "loopback": None}


def layout_profile(record):
    """Fingerprint the layout: ``template`` / ``legacy`` / ``alien``.

    The project prefix matches a legacy instance too, so the prefix alone proves
    nothing. A template instance is the one that carries every marker the
    maintenance procedures assume; anything recognisably OpenClaw but shaped
    differently is legacy; anything unrecognisable is alien.
    """
    paths = record.get("paths") or {}
    container = record.get("container") or {}
    markers = {
        "state_mount": bool(paths.get("state_dir")),
        "auth_secrets_mount": bool(paths.get("auth_secrets")),
        "compose_file": bool((record.get("compose") or {}).get("config_files")),
        "gateway_container": bool(container.get("id")),
    }
    record.setdefault("fingerprint", {})["markers"] = markers
    looks_openclaw = (
        markers["state_mount"]
        or "openclaw" in (container.get("image") or "").lower()
        or "openclaw" in (container.get("name") or "").lower()
        or os.path.isfile(paths.get("config_file") or "")
    )
    if not looks_openclaw:
        return "alien"
    if all(markers.values()):
        return "template"
    return "legacy"


# --------------------------------------------------------------------------- #
# capability probe
# --------------------------------------------------------------------------- #

_VERB_RE = re.compile(r"^\s{0,8}([a-z][a-z0-9|-]{1,40})\)\s*$", re.M)
_PROBE_SH = (
    'printf "RWI=%s\\n" "$(command -v run-with-infisical 2>/dev/null || echo none)"; '
    'printf "OC=%s\\n" "$(command -v openclaw 2>/dev/null || echo none)"; '
    'printf "VER=%s\\n" "$(openclaw --version 2>/dev/null | head -n 1 || true)"'
)


def _wrapper_verbs(path):
    """Best-effort verb list of a site wrapper script.

    A missing verb is a finding ("wrapper drift"), never a licence to
    reimplement the wrapper's site knowledge inside the plugin.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read(65536)
    except OSError:
        return [], "unreadable"
    verbs = set()
    for m in _VERB_RE.finditer(text):
        for verb in m.group(1).split("|"):
            if verb not in ("*", ""):
                verbs.add(verb)
    return sorted(verbs), ("parsed" if verbs else "unknown")


def probe_capabilities(record, probe=True, timeout=DEFAULT_TIMEOUT):
    """What this instance can actually do, as opposed to what the template says.

    Runs at most one in-container command (``openclaw --version`` plus two
    ``command -v`` lookups) and only when the gateway is running.
    """
    project = record.get("project")
    caps = {
        "wrapper": None,
        "wrapper_verbs": [],
        "wrapper_verbs_source": "absent",
        "cli": None,
        "cli_version": None,
        "run_with_infisical": None,
        "exec_mode": "none",
    }
    wrapper = shutil.which(project) if project else None
    if wrapper:
        caps["wrapper"] = wrapper
        caps["wrapper_verbs"], caps["wrapper_verbs_source"] = _wrapper_verbs(wrapper)
    running = (record.get("container") or {}).get("state") == "running"
    service = (record.get("container") or {}).get("service") or "gateway"
    if not running:
        caps["exec_mode"] = "cold" if (record.get("paths") or {}).get("state_dir") else "none"
        return caps
    caps["exec_mode"] = "hot"
    if not probe:
        return caps
    rc, out, _err = run(
        ["docker", "compose", "-p", project, "exec", "-T", service, "sh", "-lc", _PROBE_SH],
        timeout=timeout)
    if rc != 0:
        caps["cli"] = False
        return caps
    for line in (out or "").splitlines():
        if line.startswith("RWI="):
            caps["run_with_infisical"] = line[4:].strip() not in ("", "none")
        elif line.startswith("OC="):
            caps["cli"] = line[3:].strip() not in ("", "none")
        elif line.startswith("VER="):
            caps["cli_version"] = line[4:].strip() or None
    return caps


# --------------------------------------------------------------------------- #
# state
# --------------------------------------------------------------------------- #

def _log_age_hours(container_id, timeout=15):
    """Hours since the gateway last wrote a log line, or ``None``.

    This is the zombie detector's raw signal: a container can be running and
    health-green while its log has not moved for weeks.
    """
    rc, out, err = run(["docker", "logs", "--tail", "1", "--timestamps", container_id],
                       timeout=timeout)
    if rc != 0:
        return None
    line = ((out or "") + (err or "")).strip().splitlines()
    if not line:
        return None
    stamp = line[-1].split(" ", 1)[0]
    stamp = re.sub(r"\.\d+", "", stamp).replace("Z", "+0000").replace("+00:00", "+0000")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = time.mktime(time.strptime(stamp, fmt))
            return max(0.0, (time.time() - parsed) / 3600.0)
        except (ValueError, OverflowError):
            continue
    return None


def classify_state(record, stale_log_hours=24.0):
    """Assign ``ok`` / ``degraded`` / ``down`` / ``alien`` from cheap evidence.

    Discovery classifies from container state, config presence and log movement.
    A deep health battery may downgrade ``ok`` to ``degraded`` later — it never
    upgrades: a subsystem proven dead outranks a green container.
    """
    reasons = []
    if record.get("profile") == "alien" or record.get("managed") is False:
        record["state_reasons"] = ["not a managed template instance"]
        return "alien"
    container = record.get("container") or {}
    if not container.get("id"):
        record["state_reasons"] = ["no gateway container for this project"]
        return "down"
    if container.get("state") != "running":
        record["state_reasons"] = ["container state is %r" % (container.get("state") or "unknown")]
        return "down"
    if container.get("restart_count", 0) >= RESTART_LOOP_THRESHOLD and \
            container.get("health") == "unhealthy":
        record["state_reasons"] = ["restart loop: %d restarts, health unhealthy"
                                   % container["restart_count"]]
        return "down"
    signals = record.get("signals") or {}
    if container.get("health") == "unhealthy":
        reasons.append("container health is unhealthy")
    if signals.get("config_present") is False:
        reasons.append("no openclaw.json at the mounted state dir")
    elif signals.get("config_bytes") is not None and signals["config_bytes"] < 8:
        reasons.append("openclaw.json is empty")
    age = signals.get("log_age_hours")
    if age is not None and age > stale_log_hours:
        reasons.append("log silent for %.1fh (threshold %.1fh)" % (age, stale_log_hours))
    caps = record.get("capabilities") or {}
    if caps.get("cli") is False:
        reasons.append("openclaw CLI does not answer inside the container")
    record["state_reasons"] = reasons
    return "degraded" if reasons else "ok"


# --------------------------------------------------------------------------- #
# exec argv builders (policy lives in ocexec, not here)
# --------------------------------------------------------------------------- #

def compose_exec_argv(record, argv, use_infisical=True, user=None, service=None):
    """Build the hot-path command line.

    ``-T`` is not optional: without it the non-interactive call allocates no TTY
    contract and ``--json`` output is mangled.
    """
    project = record["project"]
    svc = service or (record.get("container") or {}).get("service") or "gateway"
    cmd = ["docker", "compose", "-p", project, "exec", "-T"]
    if user:
        cmd += ["-u", user]
    cmd.append(svc)
    if use_infisical:
        cmd.append("run-with-infisical")
    cmd.append("openclaw")
    return cmd + list(argv)


def cold_run_argv(record, argv, image=None):
    """Build the cold-path command line for a gateway that is not running.

    Binds only the state directory. Never run this against the state dir of a
    running instance: gateway startup enforces unique state-directory ownership.
    """
    state_dir = (record.get("paths") or {}).get("state_dir")
    if not state_dir:
        raise DockerError("no state_dir mount known for %s; cold mode impossible"
                          % record.get("name"))
    img = image or (record.get("container") or {}).get("image")
    if not img:
        raise DockerError("no image known for %s; cold mode impossible" % record.get("name"))
    return ["docker", "run", "--rm", "-v", "%s:/home/node/.openclaw" % state_dir,
            img, "openclaw"] + list(argv)


# --------------------------------------------------------------------------- #
# the sweep
# --------------------------------------------------------------------------- #

def discover_instance(project_row, prefix="openclaw-", cfg=None, probe=True,
                      stale_log_hours=24.0, timeout=DEFAULT_TIMEOUT):
    """Build one instance record. Never raises: failure becomes ``ok=False``."""
    project = project_row["project"]
    name = instance_name(project, prefix)
    if cfg is not None:
        name = cfg.canonical_name(name)
    config_files = project_row.get("config_files") or []
    record = {
        "name": name,
        "ok": True,
        "error": None,
        "project": project,
        "state": "down",
        "state_reasons": [],
        "profile": "alien",
        "managed": True,
        "role": "standard",
        "criticality": "normal",
        "compose": {
            "config_files": config_files,
            "root": os.path.dirname(config_files[0]) if config_files else None,
            "status": project_row.get("status", ""),
        },
        "container": {},
        "port": {"container_port": None, "host_ip": None, "host_port": None, "loopback": None},
        "paths": {},
        "capabilities": {},
        "signals": {},
        "fingerprint": {},
        "notes": [],
    }
    if cfg is not None and cfg.present:
        spec = cfg.instance(name)
        record["managed"] = cfg.is_managed(name)
        record["role"] = cfg.role(name) if spec else "unknown"
        record["criticality"] = (spec or {}).get("criticality", "normal")
        if not spec:
            record["notes"].append("discovered on the host but absent from the fleet config")
    try:
        service_hint = (cfg.data.get("gateway_service") if cfg is not None and cfg.present
                        else None) or "gateway"
        cont = gateway_container(project, service_hint, timeout=timeout)
        if cont:
            doc = inspect_container(cont["id"], timeout=timeout)
            state = doc.get("State") or {}
            labels = ((doc.get("Config") or {}).get("Labels") or {})
            record["container"] = {
                "id": cont["id"],
                "name": (doc.get("Name") or cont["name"]).lstrip("/"),
                "service": labels.get("com.docker.compose.service") or service_hint,
                "image": (doc.get("Config") or {}).get("Image") or cont["image"],
                "image_digest": (doc.get("Image") or None),
                "state": (state.get("Status") or "").lower(),
                "status": cont.get("status", ""),
                "health": ((state.get("Health") or {}).get("Status") or "none").lower(),
                "restart_count": doc.get("RestartCount", 0),
                "started_at": state.get("StartedAt"),
                "finished_at": state.get("FinishedAt"),
                "exit_code": state.get("ExitCode"),
            }
            record["paths"] = mount_map(doc)
            record["port"] = host_port(doc)
            if record["port"].get("loopback") is False:
                record["notes"].append(
                    "gateway port published on %s — a published port bypasses the firewall "
                    "INPUT chain" % record["port"]["host_ip"])
        record["profile"] = layout_profile(record)
        cfgfile = (record["paths"] or {}).get("config_file")
        if cfgfile:
            try:
                st = os.stat(cfgfile)
                record["signals"]["config_present"] = True
                record["signals"]["config_bytes"] = st.st_size
                record["signals"]["config_mtime"] = int(st.st_mtime)
            except OSError:
                record["signals"]["config_present"] = False
                record["signals"]["config_bytes"] = None
        if probe and record["container"].get("state") == "running":
            record["signals"]["log_age_hours"] = _log_age_hours(record["container"]["id"])
        record["capabilities"] = probe_capabilities(record, probe=probe, timeout=timeout)
        record["state"] = classify_state(record, stale_log_hours=stale_log_hours)
    except DockerError as exc:
        record["ok"] = False
        record["error"] = str(exc)
        record["state"] = "down"
    except Exception as exc:  # a broken instance must not blind the sweep
        record["ok"] = False
        record["error"] = "%s: %s" % (type(exc).__name__, exc)
        record["state"] = "down"
    return record


def discover(prefix=None, cfg=None, probe=True, timeout=DEFAULT_TIMEOUT):
    """Discover every instance of the fleet. Returns a list of records."""
    if prefix is None:
        prefix = cfg.prefix if (cfg is not None and cfg.present) else "openclaw-"
    ok, reason = docker_available()
    if not ok:
        raise DockerError(reason)
    stale = 24.0
    if cfg is not None and cfg.present:
        stale = float(cfg.policy("stale_log_hours", 24.0))
    records = [discover_instance(row, prefix, cfg, probe, stale, timeout)
               for row in compose_projects(prefix, timeout=timeout)]
    if cfg is not None and cfg.present:
        seen = {r["name"] for r in records}
        for name in cfg.instances():
            if name not in seen:
                records.append({
                    "name": name, "ok": False,
                    "error": "configured instance has no compose project on this host",
                    "project": prefix + name, "state": "down", "state_reasons": ["not deployed"],
                    "profile": "alien", "managed": cfg.is_managed(name),
                    "role": cfg.role(name), "criticality": "normal",
                    "compose": {}, "container": {}, "port": {}, "paths": {},
                    "capabilities": {}, "signals": {}, "fingerprint": {}, "notes": [],
                })
    return sorted(records, key=lambda r: r["name"])
