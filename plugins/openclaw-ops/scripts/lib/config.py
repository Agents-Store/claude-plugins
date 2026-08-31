#!/usr/bin/env python3
"""Fleet-config resolution, validation and host binding.

The plugin publishes the *shape* of a deployment; the *contents* of one
particular deployment live in an operator-owned file outside the repository.
This module is the only reader of that file.

Resolution ladder, first hit wins:

    $OPENCLAW_OPS_CONFIG
    ./.openclaw-ops.json
    ~/.config/openclaw-ops/fleet.json
    /etc/openclaw-ops/fleet.json

Two guards run on every load:

* **Mode.** The file names identity files, project ids and instance topology.
  Anything more permissive than 0600 is reported; group- or world-writable is
  fatal, because a writable config redirects every later command.
* **Host binding.** ``host_fingerprint`` is ``sha256(/etc/machine-id)[0:16]``.
  If the recorded fingerprint is not this machine's, the config describes a
  different host and every path in it is a guess — the plugin drops to
  **read-only** rather than mutating against a stale map. This is the preflight
  that catches "wrong host" before any action.
"""

import hashlib
import json
import os
import re
import stat

__all__ = [
    "ConfigError", "FleetConfig",
    "CONFIG_LADDER", "SCHEMA_PATH", "EXAMPLE_PATH",
    "resolve_config_path", "load_config", "validate_config", "load_schema",
    "check_file_mode", "host_fingerprint", "check_host",
    "init_config", "dump_config", "default_config_path",
]

CONFIG_ENV = "OPENCLAW_OPS_CONFIG"
CONFIG_LADDER = [
    ("env", None),                                    # $OPENCLAW_OPS_CONFIG
    ("cwd", "./.openclaw-ops.json"),
    ("user", "~/.config/openclaw-ops/fleet.json"),
    ("system", "/etc/openclaw-ops/fleet.json"),
]
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet.schema.json")
EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet.example.json")
MACHINE_ID_PATHS = ["/etc/machine-id", "/var/lib/dbus/machine-id"]


class ConfigError(Exception):
    """Config missing, unparsable, invalid, or refusing the requested operation."""


# --------------------------------------------------------------------------- #
# location
# --------------------------------------------------------------------------- #

def default_config_path():
    """Where ``/init`` writes when the operator does not choose a location."""
    if os.geteuid() == 0:
        return "/etc/openclaw-ops/fleet.json"
    return os.path.expanduser("~/.config/openclaw-ops/fleet.json")


def resolve_config_path(explicit=None):
    """Walk the ladder. Returns ``(path, source)``; ``(None, None)`` when nothing exists."""
    if explicit:
        return (os.path.abspath(os.path.expanduser(explicit)), "explicit")
    for source, template in CONFIG_LADDER:
        if source == "env":
            val = os.environ.get(CONFIG_ENV)
            if val:
                return (os.path.abspath(os.path.expanduser(val)), "env")
            continue
        path = os.path.abspath(os.path.expanduser(template))
        if os.path.isfile(path):
            return (path, source)
    return (None, None)


# --------------------------------------------------------------------------- #
# host binding
# --------------------------------------------------------------------------- #

def host_fingerprint():
    """``sha256(machine-id)[0:16]``, or ``None`` on a host without one."""
    for path in MACHINE_ID_PATHS:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                mid = fh.read().strip()
            if mid:
                return hashlib.sha256(mid.encode("utf-8")).hexdigest()[:16]
        except OSError:
            continue
    return None


def check_host(data):
    """Compare recorded fingerprint against this host.

    Returns ``(ok, reason)``. ``ok=False`` means read-only: a config written for
    another machine must never drive a mutation here.
    """
    recorded = (data or {}).get("host_fingerprint")
    if not recorded:
        return (True, None)
    current = host_fingerprint()
    if current is None:
        return (True, "host has no machine-id; host binding not verified")
    if current != recorded:
        return (False,
                "config was written on a different host (recorded %s, this host %s)"
                % (recorded, current))
    return (True, None)


def check_file_mode(path):
    """Report permission problems. Returns ``(fatal, message)``."""
    try:
        st = os.stat(path)
    except OSError as exc:
        return (True, "cannot stat config: %s" % exc)
    mode = stat.S_IMODE(st.st_mode)
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        return (True, "config is group- or world-writable (mode %04o); "
                      "fix with: chmod 0600 %s" % (mode, path))
    if mode & (stat.S_IRGRP | stat.S_IROTH):
        return (False, "config is readable beyond its owner (mode %04o); "
                       "expected 0600: chmod 0600 %s" % (mode, path))
    return (False, None)


# --------------------------------------------------------------------------- #
# schema validation (stdlib-only subset validator)
# --------------------------------------------------------------------------- #

_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "integer": int, "null": type(None),
}


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _type_ok(value, want):
    wanted = want if isinstance(want, list) else [want]
    for w in wanted:
        py = _TYPES.get(w)
        if py is None:
            continue
        if w in ("integer", "number") and isinstance(value, bool):
            continue
        if isinstance(value, py):
            return True
    return False


def _walk(value, schema, path, errors):
    if "type" in schema and not _type_ok(value, schema["type"]):
        errors.append("%s: expected %s, got %s" % (path, schema["type"], type(value).__name__))
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append("%s: %r is not one of %s" % (path, value, schema["enum"]))
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append("%s: does not match %s" % (path, schema["pattern"]))
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append("%s: shorter than %d" % (path, schema["minLength"]))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append("%s: longer than %d" % (path, schema["maxLength"]))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append("%s: below minimum %s" % (path, schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append("%s: above maximum %s" % (path, schema["maximum"]))
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            _walk(item, schema["items"], "%s[%d]" % (path, i), errors)
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append("%s: missing required key %r" % (path, req))
        props = schema.get("properties", {})
        patterns = schema.get("patternProperties", {})
        allow_extra = schema.get("additionalProperties", True)
        for key, val in value.items():
            if key in props:
                _walk(val, props[key], "%s.%s" % (path, key), errors)
                continue
            matched = False
            for rx, sub in patterns.items():
                if re.search(rx, key):
                    _walk(val, sub, "%s.%s" % (path, key), errors)
                    matched = True
                    break
            if matched:
                continue
            if allow_extra is False:
                errors.append("%s: unknown key %r" % (path, key))


def validate_config(data, schema=None):
    """Validate against ``fleet.schema.json``. Returns a list of error strings."""
    errors = []
    _walk(data, schema or load_schema(), "$", errors)
    # Cross-field rules the schema cannot express.
    instances = (data or {}).get("instances") or {}
    if isinstance(instances, dict):
        roles = {}
        for name, spec in instances.items():
            role = (spec or {}).get("role", "standard")
            roles.setdefault(role, []).append(name)
        for role in ("reference", "canary"):
            if len(roles.get(role, [])) > 1:
                errors.append("$.instances: role %r claimed by %s — exactly one allowed"
                              % (role, ", ".join(sorted(roles[role]))))
        ref = (data or {}).get("reference")
        if ref and ref not in instances:
            errors.append("$.reference: %r is not present in $.instances" % ref)
        canary = ((data or {}).get("policy") or {}).get("canary")
        if canary and canary not in instances:
            errors.append("$.policy.canary: %r is not present in $.instances" % canary)
        if canary and ref and canary == ref:
            errors.append("$.policy.canary: the canary must not be the reference instance")
        for name, spec in instances.items():
            if (spec or {}).get("role") == "legacy" and (spec or {}).get("manage"):
                errors.append("$.instances.%s: role 'legacy' cannot be managed — "
                              "a legacy layout is a migration project, not a maintenance target"
                              % name)
    return errors


# --------------------------------------------------------------------------- #
# the loaded config
# --------------------------------------------------------------------------- #

class FleetConfig(object):
    """A loaded fleet config, or the documented absence of one."""

    def __init__(self, data, path=None, source=None, readonly=False,
                 readonly_reason=None, warnings=None, errors=None):
        self.data = data or {}
        self.path = path
        self.source = source
        self.readonly = readonly
        self.readonly_reason = readonly_reason
        self.warnings = list(warnings or [])
        self.errors = list(errors or [])

    # -- presence ---------------------------------------------------------- #
    @property
    def present(self):
        return self.path is not None and bool(self.data)

    @property
    def valid(self):
        return self.present and not self.errors

    # -- accessors --------------------------------------------------------- #
    @property
    def prefix(self):
        return self.data.get("project_prefix", "openclaw-")

    @property
    def reference(self):
        ref = self.data.get("reference")
        if ref:
            return ref
        for name, spec in self.instances().items():
            if (spec or {}).get("role") == "reference":
                return name
        return None

    @property
    def canary(self):
        canary = self.policy("canary")
        if canary:
            return canary
        for name, spec in self.instances().items():
            if (spec or {}).get("role") == "canary":
                return name
        return None

    def instances(self):
        return self.data.get("instances") or {}

    def instance(self, name):
        """Config block for an instance, resolving aliases. ``{}`` when unknown."""
        inst = self.instances()
        if name in inst:
            return inst[name] or {}
        for key, spec in inst.items():
            if name in ((spec or {}).get("aliases") or []):
                return spec or {}
        return {}

    def canonical_name(self, name):
        """Resolve an alias to the configured instance name."""
        inst = self.instances()
        if name in inst:
            return name
        for key, spec in inst.items():
            if name in ((spec or {}).get("aliases") or []):
                return key
        return name

    def is_managed(self, name):
        spec = self.instance(name)
        if not spec:
            return False
        if spec.get("role") in ("legacy", "neighbour"):
            return False
        return spec.get("manage", True) is True

    def managed_names(self):
        return sorted(n for n in self.instances() if self.is_managed(n))

    def role(self, name):
        return (self.instance(name) or {}).get("role", "standard")

    def policy(self, key, default=None):
        pol = self.data.get("policy") or {}
        if key in pol:
            return pol[key]
        return _POLICY_DEFAULTS.get(key, default)

    # -- gates ------------------------------------------------------------- #
    def require(self):
        """Raise unless a valid config is loaded."""
        if not self.present:
            raise ConfigError(
                "no fleet config found. Looked at: $%s, ./.openclaw-ops.json, "
                "~/.config/openclaw-ops/fleet.json, /etc/openclaw-ops/fleet.json. "
                "Run the init command to create one." % CONFIG_ENV)
        if self.errors:
            raise ConfigError("fleet config is invalid:\n  " + "\n  ".join(self.errors))
        return self

    def require_writable(self, operation="mutation"):
        """Raise when the config forbids mutating (wrong host, bad mode, invalid)."""
        self.require()
        if self.readonly:
            raise ConfigError("%s refused: %s" % (operation, self.readonly_reason))
        return self

    def as_dict(self):
        return {
            "path": self.path,
            "source": self.source,
            "present": self.present,
            "valid": self.valid,
            "readonly": self.readonly,
            "readonly_reason": self.readonly_reason,
            "warnings": self.warnings,
            "errors": self.errors,
            "project_prefix": self.prefix,
            "reference": self.reference,
            "canary": self.canary,
            "managed": self.managed_names(),
        }


_POLICY_DEFAULTS = {
    "update_channel": "stable",
    "soak_days": 14,
    "stale_log_hours": 24.0,
    "batch_max": 3,
    "snapshot_keep": 20,
    "loopback_only": True,
    "snapshot_dir": None,
    "lock_dir": None,
    "canary": None,
}


def load_config(explicit=None, require=False):
    """Resolve, read, validate and host-bind the fleet config.

    Never raises for a missing file unless ``require`` is set: discovery and
    inventory are useful before a config exists, and ``/init`` needs to run
    without one.
    """
    path, source = resolve_config_path(explicit)
    if path is None:
        cfg = FleetConfig({}, None, None)
        if require:
            cfg.require()
        return cfg
    warnings, errors, readonly, reason = [], [], False, None
    if not os.path.isfile(path):
        errors.append("config not found at %s" % path)
        cfg = FleetConfig({}, path, source, True, "config file does not exist", warnings, errors)
        if require:
            cfg.require()
        return cfg
    fatal, msg = check_file_mode(path)
    if msg:
        (errors if fatal else warnings).append(msg)
        if fatal:
            readonly, reason = True, msg
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        errors.append("cannot read config %s: %s" % (path, exc))
        cfg = FleetConfig({}, path, source, True, "config unreadable", warnings, errors)
        if require:
            cfg.require()
        return cfg
    errors.extend(validate_config(data))
    if errors and not readonly:
        readonly, reason = True, "config failed validation"
    host_ok, host_msg = check_host(data)
    if not host_ok:
        readonly, reason = True, host_msg
        errors.append(host_msg)
    elif host_msg:
        warnings.append(host_msg)
    cfg = FleetConfig(data, path, source, readonly, reason, warnings, errors)
    if require:
        cfg.require()
    return cfg


# --------------------------------------------------------------------------- #
# writing
# --------------------------------------------------------------------------- #

def init_config(instances, prefix="openclaw-", compose_root=None, data_root=None,
                reference=None, canary=None, gateway_service="gateway", host_label=None,
                update_channel=None, soak_days=None, stale_log_hours=None):
    """Build a config skeleton from a discovery pass.

    ``instances`` is the list of records produced by ``discovery.discover``.
    Everything autodetection cannot decide (reference, canary, criticality,
    secret project ids) is written with a conservative default for the operator
    to review — never guessed silently.

    ``update_channel`` / ``soak_days`` / ``stale_log_hours`` are the operator's
    policy answers. ``None`` means "not asked" and keeps the default; anything
    else is written into ``policy`` and validated with the rest of the file, so
    an answer the wizard collected cannot be silently discarded.
    """
    import datetime
    block = {}
    for inst in instances:
        name = inst.get("name")
        if not name:
            continue
        profile = inst.get("profile")
        if profile == "legacy":
            role, manage = "legacy", False
        elif profile == "alien":
            role, manage = "neighbour", False
        elif name == reference:
            role, manage = "reference", True
        elif name == canary:
            role, manage = "canary", True
        else:
            role, manage = "standard", True
        entry = {"manage": manage, "role": role, "criticality": "normal"}
        if profile == "legacy":
            entry["notes"] = ("Non-template layout. Migration project, not a maintenance "
                              "target: every mutation is refused.")
        elif profile == "alien":
            entry["notes"] = "Matches the prefix but failed the layout fingerprint. Inventory only."
        block[name] = entry
    cfg = {
        "version": 1,
        "project_prefix": prefix,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "gateway_service": gateway_service,
        "policy": {
            "update_channel": "stable",
            "soak_days": 14,
            "stale_log_hours": 24,
            "batch_max": 3,
            "loopback_only": True,
        },
        "instances": block,
    }
    fpv = host_fingerprint()
    if fpv:
        cfg["host_fingerprint"] = fpv
    if host_label:
        cfg["host_label"] = host_label
    if compose_root:
        cfg["compose_root"] = compose_root
    if data_root:
        cfg["data_root"] = data_root
    if reference:
        cfg["reference"] = reference
    if canary:
        cfg["policy"]["canary"] = canary
    if update_channel is not None:
        cfg["policy"]["update_channel"] = update_channel
    if soak_days is not None:
        cfg["policy"]["soak_days"] = soak_days
    if stale_log_hours is not None:
        cfg["policy"]["stale_log_hours"] = stale_log_hours
    return cfg


def dump_config(data):
    """Canonical serialisation: stable key order, trailing newline."""
    return json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def write_config(data, path, force=False):
    """Write the config at mode 0600. Refuses to clobber without ``force``."""
    path = os.path.abspath(os.path.expanduser(path))
    if os.path.exists(path) and not force:
        raise ConfigError("%s already exists; pass force to overwrite" % path)
    errors = validate_config(data)
    if errors:
        raise ConfigError("refusing to write an invalid config:\n  " + "\n  ".join(errors))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(dump_config(data))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    os.replace(tmp, path)
    os.chmod(path, 0o600)
    return path
