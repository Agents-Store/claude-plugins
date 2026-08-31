#!/usr/bin/env python3
"""Mutation discipline: risk classes, the dry-run plan, backups, pins, batching.

The working definition, which is deliberately not about command names:

    A mutation is an operation after which the observable state differs from
    what it would have been without it. Whether the subcommand is called
    "status" is irrelevant.

Everything here is enforcement, not advice. A plan missing a block does not
render. A rollback that is prose rather than a command does not validate. An
R4 operation without a typed confirmation does not run.
"""

import datetime
import hashlib
import json
import os
import re
import shutil
import time
import sys

__all__ = [
    "GateError", "RISK_CLASSES", "BLOCKS", "EXTRA_BLOCKS", "MOVING_TAGS",
    "RED_LINES", "RETRY_RULES", "BANNED_ARGS",
    "Plan", "make_plan", "gate", "snapshot", "bak_ring_warning",
    "pin", "require_pin", "is_moving_tag", "batch_policy", "retry_policy",
    "check_banned_args", "confirm_phrase",
    "AUTH_LOCK", "LOCK_TTL_SECONDS", "FleetLock", "fleet_lock", "lock_dir",
    "PLAN_ID_COMMANDS", "PLAN_TTL_SECONDS", "plan_dir", "plan_records",
    "parse_plan_id", "make_plan_id", "check_plan_id",
    "plan_from_dict", "check_plan_authorises",
]


class GateError(Exception):
    """A gate refused the operation. The message is what the human must read."""


# --------------------------------------------------------------------------- #
# risk classes
# --------------------------------------------------------------------------- #

RISK_CLASSES = {
    "R0": {
        "label": "read",
        "gate": "none",
        "description": "No observable effect. Files, docker ps/inspect, /healthz, "
                       "doctor --lint --json, models status --check, plugins list --json.",
    },
    "R1": {
        "label": "read with effect",
        "gate": "--yes",
        "description": "Reads that cost money, hold a lock, or move state: "
                       "models status --probe, any request down the agent path, memory index. "
                       "Gated exactly like R2 — the word 'status' in the name changes nothing.",
    },
    "R2": {
        "label": "reversible",
        "gate": "--yes",
        "description": "restart/up/down, editing openclaw.json, enabling or disabling a cron "
                       "entry, editing plugins.load.paths.",
    },
    "R3": {
        "label": "partially reversible",
        "gate": "--yes + verified backup",
        "description": "Version change, memory index --force, session pruning, database "
                       "compaction. The backup must be shown in the plan, not promised.",
    },
    "R4": {
        "label": "irreversible",
        "gate": "--yes + typed confirmation",
        "description": "State-schema migration, writing a secret to the store, "
                       "security audit --fix, rotating the gateway token.",
    },
}
RISK_ORDER = ["R0", "R1", "R2", "R3", "R4"]


def _rank(risk):
    try:
        return RISK_ORDER.index(risk)
    except ValueError:
        raise GateError("unknown risk class %r (expected one of %s)"
                        % (risk, ", ".join(RISK_ORDER)))


# --------------------------------------------------------------------------- #
# the eight blocks
# --------------------------------------------------------------------------- #
#
# A dry-run missing any block is a bug in the plugin, not a terse plan. The
# acceptance test for the whole format: a human holding only the printed plan,
# with the plugin uninstalled, can perform the rollback by hand.
#
BLOCKS = [
    ("TARGET", "Which instances, resolved by name. Never a selector that could widen later."),
    ("PRECHECK", "What was verified before proposing this, failures included. A precheck that "
                 "only prints passes is decoration."),
    ("CHANGE", "Line-by-line diff WITH a deletion count. A non-zero deletion count in a config "
               "is a separate red flag and must be called out."),
    ("BACKUP", "The snapshot that already exists, with its path and fingerprint. Not a promise."),
    ("IMPACT", "What stops working while this runs, and for how long."),
    ("VALIDATE", "The command that proves it worked, with the expected result."),
    ("ROLLBACK", "An executable command that undoes this. Prose is not a rollback."),
    ("APPLY", "The exact command that performs the change."),
]
EXTRA_BLOCKS = [
    ("IRREVERSIBLE", "What cannot be undone, stated plainly."),
    ("CONFIRM", "The phrase the operator must type verbatim."),
]
BLOCK_NAMES = [b[0] for b in BLOCKS]
EXTRA_BLOCK_NAMES = [b[0] for b in EXTRA_BLOCKS]

# Rollback text that only describes: "restore from backup", "revert the change".
_PROSE_ROLLBACK = re.compile(
    r"^(restore|revert|undo|roll ?back|put back|re-?apply)\b[^`$]*$", re.I)
# A real rollback looks like a command line.
_COMMAND_HINT = re.compile(r"(^|\s)(docker|cp|mv|tar|git|openclaw|systemctl|install|sh|bash|"
                           r"python3|chmod|chown|rm|ln)\b")

BANNED_ARGS = {
    "--accept-capabilities":
        "Capability consent is printed for a human, never passed by the plugin. Upstream made "
        "--yes and doctor --fix deliberately unable to approve capabilities; automating it "
        "destroys the mechanism.",
}


# --------------------------------------------------------------------------- #
# red lines and retry rules
# --------------------------------------------------------------------------- #

RED_LINES = {
    "upgrade-without-verified-backup":
        "An upgrade without a passing backup --verify is REJECTED, not warned about.",
    "fleet-wide-mutation":
        "Any mutation touching more than the canary in one step.",
    "secret-overwrite-different-fingerprint":
        "Overwriting an existing secret whose fingerprint differs from the new value.",
    "gateway-token-rotation":
        "Rotating the gateway bearer token — it is all-or-nothing operator access.",
    "delete-plaintext-env":
        "Deleting a plaintext env file before fingerprint parity with the secret store is proven. "
        "Neutralise by moving to quarantine outside the container volume, never by rm.",
    "doctor-fix-or-security-fix":
        "doctor --fix / security audit --fix — narrow, opaque, and they touch what they choose.",
    "skill-install-unread-lock":
        "Installing skills or plugins before lock.json has been read and backed up.",
    "legacy-instance-mutation":
        "Any mutation on a legacy-layout instance. That is a migration project.",
    "in-container-write-outside-mount":
        "Writing inside the container outside a mounted volume — the change dies with the image.",
}

RETRY_RULES = {
    "oauth-login": {
        "attempts": 0,
        "why": "A repeat burns the single-use refresh token and logs out the other consumer. "
               "Diagnose by reading the expiry from the profile, never by triggering a refresh.",
    },
    "oauth-refresh": {
        "attempts": 0,
        "why": "Same token sink. One failure means stop and inspect, not retry.",
    },
    "openclaw-update": {
        "attempts": 0,
        "why": "A failed update deliberately leaves the gateway stopped. Repeating on a "
               "half-migrated state directory is the road to unrecoverable.",
    },
    "skills-install": {
        "attempts": 0,
        "why": "A corrupted lock.json makes the next install remove the other skills. "
               "Stop and read the lock.",
    },
    "plugins-install": {
        "attempts": 0,
        "why": "Same lock hazard as skills-install.",
    },
    "restart-on-crash-loop": {
        "attempts": 0,
        "why": "A restart during a crash loop yields no information, extends the backoff, and "
               "overwrites the log holding the first cause. Read the log first.",
    },
    "secret-write": {
        "attempts": 0,
        "why": "Risk of a partial write, and every repeat is one more appearance of the value "
               "in a process table. Stop and verify by fingerprint.",
    },
}


def retry_policy(operation):
    """How many retries this operation gets. Default is one retry; the listed
    operations get zero, because repeating them is worse than failing."""
    return RETRY_RULES.get(operation, {"attempts": 1, "why": "no special hazard recorded"})


def check_banned_args(argv):
    """Raise when an argument the plugin must never pass appears in a command line."""
    for arg in argv:
        base = arg.split("=", 1)[0]
        if base in BANNED_ARGS:
            raise GateError("refusing to pass %s. %s" % (base, BANNED_ARGS[base]))
    return True


# --------------------------------------------------------------------------- #
# pins
# --------------------------------------------------------------------------- #

MOVING_TAGS = frozenset(["latest", "main", "edge", "nightly", "stable",
                         "extended-stable", "beta", "dev", "rolling"])


def is_moving_tag(reference):
    """Is this image/package reference a tag that gets rebuilt under the same name?

    Moving tags are rebuilt on a schedule; only plain version tags, dated tags
    and digests are immutable. A mutation pinned to a moving tag cannot be
    rolled back, because the thing it rolls back to has already changed.
    """
    if not reference:
        return True
    if "@sha256:" in reference:
        return False
    tag = reference.rsplit(":", 1)[-1] if ":" in reference.rsplit("/", 1)[-1] else "latest"
    if tag in MOVING_TAGS:
        return True
    for moving in MOVING_TAGS:
        if tag.startswith(moving) and not re.search(r"\d{4}-?\d{2}-?\d{2}", tag):
            return True
    return not re.search(r"\d", tag)


def pin(kind, value, source=None):
    """Record the immutable identifier a mutation is pinned to.

    ``kind`` is ``image-digest`` / ``npm-version`` / ``git-sha``. Rejects a
    moving tag outright: without a fixed identifier there is no rollback.
    """
    if not value:
        raise GateError("cannot pin %s: no identifier given" % kind)
    if kind == "image-digest":
        if "@sha256:" not in value and not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise GateError("image pin must be a digest, got %r. Moving tags are rebuilt "
                            "weekly under the same name." % value)
    elif kind == "npm-version":
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-.+][0-9A-Za-z.\-]+)?", value):
            raise GateError("npm pin must be a plain version, got %r" % value)
    elif kind == "git-sha":
        if not re.fullmatch(r"[0-9a-f]{7,40}", value):
            raise GateError("git pin must be a commit sha, got %r" % value)
    return {"kind": kind, "value": value, "source": source,
            "recorded_at": _now()}


def require_pin(pin_record, operation="mutation"):
    """Refuse a mutation of an executable artefact that has no recorded pin."""
    if not pin_record or not pin_record.get("value"):
        raise GateError("%s refused: no immutable identifier recorded. "
                        "Pin the image digest / package version / commit sha first — "
                        "a rollback without one is impossible." % operation)
    return pin_record


# --------------------------------------------------------------------------- #
# backups
# --------------------------------------------------------------------------- #

def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)\
        .isoformat().replace("+00:00", "Z")


def bak_ring_warning(path, ring=4):
    """Name the ``.bak`` the CLI's own rotation is about to evict.

    The built-in ``openclaw.json.bak.1..N`` ring protects the human, not the
    plugin: four automated edits in a row push out the last-known-good file the
    operator kept for themselves.
    """
    victim = "%s.bak.%d" % (path, ring)
    if os.path.exists(victim):
        return ("the built-in backup ring will evict %s on the next edit — "
                "that is the oldest copy the operator kept" % victim)
    return None


def snapshot(path, snapshot_dir=None, tag=None, keep=20):
    """Copy a file to a snapshot OUTSIDE the CLI's own ``.bak`` ring.

    Returns ``{path, source, fingerprint, created_at}``. Taken once, before the
    first edit of a session, precisely so an automated sequence cannot evict the
    human's copy.
    """
    import redact
    if not os.path.isfile(path):
        raise GateError("cannot snapshot %s: not a file" % path)
    base = snapshot_dir or os.path.join(
        os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
        "openclaw-ops", "snapshots")
    os.makedirs(base, mode=0o700, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    name = "%s.%s%s.snap" % (os.path.basename(path), stamp, ("." + tag) if tag else "")
    dest = os.path.join(base, name)
    shutil.copy2(path, dest)
    os.chmod(dest, 0o600)
    _prune_snapshots(base, os.path.basename(path), keep)
    return {"path": dest, "source": path, "fingerprint": redact.fp_of_file(dest),
            "created_at": _now()}


def _prune_snapshots(base, prefix, keep):
    try:
        names = sorted(n for n in os.listdir(base) if n.startswith(prefix + "."))
    except OSError:
        return
    for name in names[:-keep] if keep and len(names) > keep else []:
        try:
            os.unlink(os.path.join(base, name))
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# the fleet front lock
# --------------------------------------------------------------------------- #
#
# The runtime's own serialisation lock is a file lock INSIDE one state
# directory. It serialises two processes that share that directory and nothing
# else, which is precisely the wrong shape for credentials: a refresh token is
# single-use and rotating, so two instances refreshing the same account at the
# same moment is the one collision the local lock cannot see. This is the lock
# that spans the fleet — one holder at a time on this host, with a TTL so a
# crashed holder cannot wedge every later run for ever, and with the holder
# printed when it is busy, because "resource busy" without a name is a dead end.

LOCK_TTL_SECONDS = 900
LOCK_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
AUTH_LOCK = "fleet-auth"


def _policy(cfg, key):
    """Read one policy key from a FleetConfig or a plain dict. Never raises."""
    if cfg is None:
        return None
    getter = getattr(cfg, "policy", None)
    if callable(getter):
        try:
            return getter(key)
        except Exception:
            return None
    if isinstance(cfg, dict):
        return (cfg.get("policy") or {}).get(key)
    return None


def lock_dir(cfg=None, explicit=None):
    """Directory holding the lock files.

    Config first (``policy.lock_dir``, else the ``locks`` sibling of
    ``policy.snapshot_dir``), then the XDG state home. Never inside the plugin:
    the plugin is read-only and shared, this is per-host runtime state.
    """
    if explicit:
        return explicit
    configured = _policy(cfg, "lock_dir")
    if configured:
        return configured
    snap = _policy(cfg, "snapshot_dir")
    if snap:
        parent = os.path.dirname(str(snap).rstrip(os.sep)) or os.sep
        return os.path.join(parent, "locks")
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return os.path.join(base, "openclaw-ops", "locks")


def _lock_owner():
    return os.environ.get("USER") or os.environ.get("LOGNAME") or ("uid:%d" % os.getuid())


class FleetLock(object):
    """Exclusive, host-wide, TTL-bounded lock file for fleet-level work."""

    def __init__(self, name, cfg=None, ttl=LOCK_TTL_SECONDS, operation=None,
                 owner=None, directory=None):
        if not LOCK_NAME_RE.match(name or ""):
            raise GateError("invalid lock name %r: lowercase letters, digits and dashes only"
                            % name)
        self.name = name
        self.ttl = LOCK_TTL_SECONDS if ttl is None else int(ttl)
        self.operation = operation
        self.owner = owner or _lock_owner()
        self.dir = lock_dir(cfg, directory)
        self.path = os.path.join(self.dir, "%s.lock" % name)
        self.token = None
        self.record = None
        self.inherited = False

    # -- reading ----------------------------------------------------------- #
    def read(self):
        """The current holder record, or ``None`` when the lock is free."""
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _expired(record):
        try:
            return float(record.get("expires_epoch") or 0) <= time.time()
        except (TypeError, ValueError):
            return True

    def describe(self):
        """Holder summary for humans and for JSON output."""
        held = self.read()
        if held is None:
            return {"lock": self.name, "path": self.path, "held": False}
        return {"lock": self.name, "path": self.path, "held": True,
                "expired": self._expired(held), "owner": held.get("owner"),
                "pid": held.get("pid"), "operation": held.get("operation"),
                "acquired_at": held.get("acquired_at"),
                "expires_at": held.get("expires_at"),
                "seconds_left": max(0, int(float(held.get("expires_epoch") or 0) - time.time()))}

    # -- taking and giving back -------------------------------------------- #
    def acquire(self, token=None):
        """Take the lock, or inherit it when ``token`` matches the live holder.

        Inheriting is what keeps a procedure that already holds the lock from
        deadlocking against itself when it calls through the exec door.
        """
        if token:
            held = self.read()
            if held and held.get("token") == token and not self._expired(held):
                self.token, self.record, self.inherited = token, held, True
                return self
            raise GateError(
                "the %s lock token does not match its current holder — either the lock expired "
                "and someone else took it, or this token belongs to a finished procedure. Check "
                "with: gate.py lock status %s" % (self.name, self.name))
        os.makedirs(self.dir, mode=0o700, exist_ok=True)
        payload = None
        for _attempt in (1, 2):
            payload = {
                "lock": self.name,
                "token": hashlib.sha256(os.urandom(32)).hexdigest()[:16],
                "owner": self.owner,
                "pid": os.getpid(),
                "operation": self.operation,
                "acquired_at": _now(),
                "expires_epoch": time.time() + self.ttl,
                "ttl_seconds": self.ttl,
            }
            payload["expires_at"] = datetime.datetime.fromtimestamp(
                payload["expires_epoch"], datetime.timezone.utc).replace(
                microsecond=0).isoformat().replace("+00:00", "Z")
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                held = self.read()
                if held is None or self._expired(held):
                    # A stale holder: evict it once, say so, and try again.
                    try:
                        os.unlink(self.path)
                    except OSError:
                        pass
                    continue
                raise GateError(self._busy_message(held))
            with os.fdopen(fd, "w") as fh:
                json.dump(payload, fh, indent=2)
            self.token, self.record, self.inherited = payload["token"], payload, False
            return self
        raise GateError("could not take the %s lock: an expired holder was evicted and another "
                        "process took it immediately. Re-run once." % self.name)

    def _busy_message(self, held):
        left = max(0, int(float(held.get("expires_epoch") or 0) - time.time()))
        return ("the %s lock is held by %s (pid %s)%s since %s. Refused rather than queued: two "
                "credential mutations at once is what this lock exists to prevent. It expires on "
                "its own in %d s, or its holder releases it. Inspect: gate.py lock status %s"
                % (self.name, held.get("owner") or "an unnamed holder", held.get("pid"),
                   " for %r" % held["operation"] if held.get("operation") else "",
                   held.get("acquired_at"), left, self.name))

    def release(self, force=False):
        """Give the lock back. Inherited locks are left to whoever took them."""
        if self.inherited and not force:
            return False
        held = self.read()
        if held is None:
            return False
        if not force and self.token and held.get("token") != self.token:
            raise GateError("refusing to release the %s lock: it is held by %s now, not by this "
                            "process." % (self.name, held.get("owner") or "someone else"))
        try:
            os.unlink(self.path)
        except OSError:
            return False
        return True

    # -- context manager ---------------------------------------------------- #
    def __enter__(self):
        if self.token is None:
            self.acquire()
        return self

    def __exit__(self, *_exc):
        self.release()
        return False


def fleet_lock(name=AUTH_LOCK, cfg=None, ttl=LOCK_TTL_SECONDS, operation=None,
               owner=None, directory=None, token=None):
    """Take (or inherit) the fleet-wide front lock and return it, acquired."""
    return FleetLock(name, cfg=cfg, ttl=ttl, operation=operation, owner=owner,
                     directory=directory).acquire(token=token)


# --------------------------------------------------------------------------- #
# batching
# --------------------------------------------------------------------------- #

def batch_policy(direction):
    """Batch behaviour follows the direction of the transition, not the operation.

    ``good-to-changed``  -> fail-fast. A mixed-state fleet is described by no
    document and covered by no rollback, and a failure on the third of a set of
    clones is almost always systemic.
    ``broken-to-repair`` -> continue-and-report. One failure is no reason to
    leave the other five broken.
    """
    if direction == "good-to-changed":
        return {"mode": "fail-fast",
                "why": "a partially changed fleet matches no documented state"}
    if direction == "broken-to-repair":
        return {"mode": "continue-and-report",
                "why": "one failed repair is no reason to abandon the rest"}
    raise GateError("unknown batch direction %r (expected good-to-changed or broken-to-repair)"
                    % direction)


def canary_barrier(targets, canary=None, reference=None):
    """Order a multi-instance mutation: canary first, then stop and report.

    Returns ``(first_wave, remaining, note)``. Continuing past the barrier is a
    separate confirmation, never an implied one.
    """
    targets = list(targets)
    if len(targets) <= 1:
        return targets, [], None
    pick = canary if canary in targets else None
    if pick is None:
        pool = [t for t in targets if t != reference] or targets
        pick = pool[0]
    rest = [t for t in targets if t != pick]
    return ([pick], rest,
            "canary barrier: %s runs alone; the remaining %d need a separate confirmation"
            % (pick, len(rest)))


# --------------------------------------------------------------------------- #
# the plan
# --------------------------------------------------------------------------- #

def confirm_phrase(operation, target):
    """The phrase an R4 gate demands, verbatim.

    It carries the operation AND the target so muscle memory on the wrong
    instance fails instead of succeeding.
    """
    return "%s %s IRREVERSIBLE" % (operation.upper().replace(" ", "-"), target)


class Plan(object):
    """A dry-run plan. Renders only when every mandatory block is filled."""

    def __init__(self, operation, risk, target):
        _rank(risk)
        self.operation = operation
        self.risk = risk
        self.target = target if isinstance(target, str) else ", ".join(target)
        self.blocks = {}
        self.pin = None
        self.backup = None
        self.created_at = _now()

    # -- filling ----------------------------------------------------------- #
    def set(self, block, value):
        name = block.upper()
        if name not in BLOCK_NAMES + EXTRA_BLOCK_NAMES:
            raise GateError("unknown plan block %r" % block)
        self.blocks[name] = value if isinstance(value, list) else [str(value)]
        return self

    def add(self, block, line):
        name = block.upper()
        self.blocks.setdefault(name, []).append(str(line))
        return self

    def attach_backup(self, backup_record):
        self.backup = backup_record
        self.set("BACKUP", ["%s  (%s, taken %s)" % (
            backup_record["path"], backup_record.get("fingerprint") or "no-fingerprint",
            backup_record.get("created_at"))])
        return self

    def attach_pin(self, pin_record):
        self.pin = pin_record
        self.add("PRECHECK", "pinned %s = %s" % (pin_record["kind"], pin_record["value"]))
        return self

    # -- gating ------------------------------------------------------------ #
    def required_blocks(self):
        names = list(BLOCK_NAMES)
        if _rank(self.risk) >= _rank("R3"):
            names += EXTRA_BLOCK_NAMES
        return names

    def requires_yes(self):
        return _rank(self.risk) >= _rank("R1")

    def requires_backup(self):
        return _rank(self.risk) >= _rank("R3")

    def requires_typed_confirm(self):
        return _rank(self.risk) >= _rank("R4")

    def confirm_phrase(self):
        return confirm_phrase(self.operation, self.target)

    def validate(self):
        """Structural check. Returns a list of problems; empty means renderable."""
        problems = []
        for name in self.required_blocks():
            lines = [l for l in self.blocks.get(name, []) if str(l).strip()]
            if not lines:
                problems.append("missing block %s" % name)
        rollback = " ".join(self.blocks.get("ROLLBACK", []))
        if rollback.strip():
            if not _COMMAND_HINT.search(rollback) or _PROSE_ROLLBACK.match(rollback.strip()):
                problems.append("ROLLBACK must be an executable command, not a description: %r"
                                % rollback.strip()[:80])
        if self.requires_backup() and not self.backup:
            problems.append("%s needs a backup that already exists; attach_backup() was never "
                            "called" % self.risk)
        if self.requires_typed_confirm():
            confirm = " ".join(self.blocks.get("CONFIRM", []))
            if self.confirm_phrase() not in confirm:
                problems.append("CONFIRM must quote the exact phrase: %s" % self.confirm_phrase())
        return problems

    # -- output ------------------------------------------------------------ #
    def render(self):
        problems = self.validate()
        if problems:
            raise GateError("incomplete dry-run plan (this is a plugin bug):\n  - "
                            + "\n  - ".join(problems))
        info = RISK_CLASSES[self.risk]
        out = ["DRY RUN — %s" % self.operation,
               "risk %s (%s) — gate: %s" % (self.risk, info["label"], info["gate"]), ""]
        for name in self.required_blocks():
            out.append("%s:" % name)
            for line in self.blocks[name]:
                for sub in str(line).splitlines() or [""]:
                    out.append("  " + sub)
            out.append("")
        if self.requires_typed_confirm():
            out.append("Nothing has been changed. To proceed, re-run with --yes and type:")
            out.append("  %s" % self.confirm_phrase())
        elif self.requires_yes():
            out.append("Nothing has been changed. Re-run with --yes to apply.")
        return "\n".join(out).rstrip() + "\n"

    def as_dict(self):
        return {
            "operation": self.operation, "risk": self.risk, "target": self.target,
            "created_at": self.created_at, "blocks": self.blocks,
            "pin": self.pin, "backup": self.backup,
            "requires_yes": self.requires_yes(),
            "requires_backup": self.requires_backup(),
            "requires_typed_confirm": self.requires_typed_confirm(),
            "confirm_phrase": self.confirm_phrase() if self.requires_typed_confirm() else None,
            "problems": self.validate(),
        }

    def __str__(self):
        return self.render()


def make_plan(operation, risk, target, **blocks):
    """Build a plan in one call: ``make_plan(op, "R2", "alpha", TARGET=..., ...)``."""
    plan_obj = Plan(operation, risk, target)
    for key, value in blocks.items():
        plan_obj.set(key, value)
    return plan_obj


# --------------------------------------------------------------------------- #
# plan provenance: what authorises a mutation at the exec door
# --------------------------------------------------------------------------- #
#
# The exec door is one call, not a procedure: it cannot build a plan, and it
# must not perform a mutation that no plan covers. Two things can authorise it.
# The rendered plan itself, handed over as JSON — the strong form, re-validated
# here. Or the id of the plan a plan-building command has already shown to the
# operator — the form a ROLLBACK line can carry, since a rollback runs from a
# printed plan rather than from a file.
#
# The id is deliberately structured: it names the command that built the plan
# and the instance it was built for, so an id copied to another instance stops
# being valid instead of quietly widening.

PLAN_ID_COMMANDS = ("repair", "update", "auth", "shared-sync", "clone")
PLAN_ID_RE = re.compile(r"^(?P<command>[a-z][a-z0-9-]{1,31})/"
                        r"(?P<target>[A-Za-z0-9][A-Za-z0-9._-]{0,63})/"
                        r"(?P<stamp>[0-9A-Za-z:.\-]{4,32})$")

# A plan describes state that was read at PRECHECK time. The longer the id sits
# unused, the less the plan describes the box it was built for, so the record
# expires on its own rather than waiting to be revoked.
PLAN_TTL_SECONDS = 1800


def plan_dir(cfg=None, explicit=None):
    """Directory holding the issued-plan records.

    Same resolution order as :func:`lock_dir` — config (``policy.plan_dir``, else
    the ``plans`` sibling of ``policy.snapshot_dir``), then the XDG state home.
    Never inside the plugin: the plugin is read-only and shared, this is
    per-host runtime state.
    """
    if explicit:
        return explicit
    configured = _policy(cfg, "plan_dir")
    if configured:
        return configured
    snap = _policy(cfg, "snapshot_dir")
    if snap:
        parent = os.path.dirname(str(snap).rstrip(os.sep)) or os.sep
        return os.path.join(parent, "plans")
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return os.path.join(base, "openclaw-ops", "plans")


def _plan_record_path(plan_id, directory):
    return os.path.join(directory, re.sub(r"[^A-Za-z0-9._-]", "_", plan_id) + ".json")


def _plan_hash(plan_obj):
    """Content fingerprint of the plan an id stands for, or ``None``."""
    if plan_obj is None:
        return None
    data = plan_obj.as_dict() if hasattr(plan_obj, "as_dict") else plan_obj
    payload = json.dumps({"operation": data.get("operation"), "risk": data.get("risk"),
                          "target": data.get("target"), "blocks": data.get("blocks")},
                         sort_keys=True, ensure_ascii=False)
    return "fp:" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:8]


def _plan_targets(value):
    return [part.strip() for part in re.split(r"[,\s]+", value or "") if part.strip()]


def parse_plan_id(plan_id, target=None):
    """Validate the SHAPE of a plan id. Says nothing about whether it was issued."""
    match = PLAN_ID_RE.match(plan_id or "")
    if not match:
        raise GateError(
            "%r is not a plan id. The form is <command>/<instance>/<utc-stamp>, e.g. "
            "repair/<instance>/2020-01-01T00:00:00Z, and only a command that has already "
            "shown the eight-block plan mints one." % (plan_id or ""))
    parts = match.groupdict()
    if parts["command"] not in PLAN_ID_COMMANDS:
        raise GateError("plan id names %r, which builds no plans. Plans come from: %s."
                        % (parts["command"], ", ".join(PLAN_ID_COMMANDS)))
    if target is not None and parts["target"] != target:
        raise GateError("this plan id was minted for %r, not for %r. A plan authorises the "
                        "instance it was built for and no other."
                        % (parts["target"], target))
    return parts


def make_plan_id(command, target, when=None, plan=None, risk=None, cfg=None,
                 directory=None, ttl=PLAN_TTL_SECONDS):
    """Mint a plan id AND record it, so the door can verify it was really issued.

    A shape check alone makes the barrier disciplinary: any string of the right
    form passes, and the id can be replayed for ever. So minting writes a record
    — command, instance, risk class, the fingerprint of the plan it stands for,
    and an expiry — and :func:`check_plan_id` reads it back.
    """
    if command not in PLAN_ID_COMMANDS:
        raise GateError("only the plan-building commands mint plan ids (%s), got %r"
                        % (", ".join(PLAN_ID_COMMANDS), command))
    if plan is not None:
        names = _plan_targets(getattr(plan, "target", None) or "")
        if names and target not in names:
            raise GateError("the plan targets %s; the id is being minted for %r."
                            % (", ".join(names), target))
        problems = plan.validate() if hasattr(plan, "validate") else []
        if problems:
            raise GateError("no id for a plan that does not render:\n  - "
                            + "\n  - ".join(problems))
        risk = risk or getattr(plan, "risk", None)
    risk = risk or "R2"
    if risk not in RISK_CLASSES:
        raise GateError("unknown risk class %r: the classes are %s"
                        % (risk, ", ".join(RISK_ORDER)))
    stamp = when or _now()
    ttl = PLAN_TTL_SECONDS if ttl is None else int(ttl)
    base = plan_dir(cfg, directory)
    os.makedirs(base, mode=0o700, exist_ok=True)
    _prune_plans(base)
    # Two plans inside one second are ordinary (a command that shows one plan per
    # instance), so the stamp gets a discriminator rather than the mint failing.
    for suffix in [""] + [".%d" % n for n in range(1, 100)]:
        plan_id = "%s/%s/%s%s" % (command, target, stamp, suffix)
        parse_plan_id(plan_id, target)
        path = _plan_record_path(plan_id, base)
        if not os.path.exists(path):
            break
    else:
        raise GateError("too many plan ids minted for %s/%s in one second" % (command, target))
    now = time.time()
    record = {"plan_id": plan_id, "command": command, "target": target, "risk": risk,
              "plan_hash": _plan_hash(plan), "created_at": _now(),
              "expires_epoch": now + ttl,
              "expires_at": _stamp(now + ttl), "used_at": None}
    _write_private_json(path, record)
    return plan_id


def check_plan_id(plan_id, target=None, risk=None, cfg=None, directory=None, consume=False):
    """Was this id really issued, is it still live, and does it cover this call?

    Shape, then registry. A record that is missing, expired, already used, minted
    for another instance or minted for a lower risk class is refused — the four
    ways a well-formed string can fail to be an authorisation.

    ``consume=True`` burns the record: one plan authorises one mutation, so an id
    cannot be carried from the change it was shown for to a second one.
    """
    parts = parse_plan_id(plan_id, target)
    base = plan_dir(cfg, directory)
    path = _plan_record_path(plan_id, base)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        raise GateError(
            "no plan %s was issued on this host. The id has the right shape, which is not the "
            "same as a plan existing: run the command that owns the operation (%s), let it show "
            "the eight blocks and mint the id, then pass that id."
            % (plan_id, ", ".join(PLAN_ID_COMMANDS)))
    if record.get("plan_id") != plan_id:
        raise GateError("the record at %s belongs to another plan id — refusing to read it as %s."
                        % (path, plan_id))
    if record.get("used_at"):
        raise GateError("plan %s was already used at %s. A plan authorises one mutation; the "
                        "next change needs its own plan, shown and answered."
                        % (plan_id, record["used_at"]))
    try:
        expired = float(record.get("expires_epoch") or 0) <= time.time()
    except (TypeError, ValueError):
        expired = True
    if expired:
        raise GateError("plan %s expired at %s. A plan describes state read at precheck time; "
                        "re-run the command that built it and answer the fresh plan."
                        % (plan_id, record.get("expires_at")))
    if target is not None and record.get("target") != target:
        raise GateError("plan %s was recorded for %r, not for %r."
                        % (plan_id, record.get("target"), target))
    if risk is not None:
        if risk not in RISK_CLASSES:
            raise GateError("unknown risk class %r: the classes are %s"
                            % (risk, ", ".join(RISK_ORDER)))
        if _rank(record.get("risk")) < _rank(risk):
            raise GateError("plan %s was minted for class %s; this call classifies as %s. A plan "
                            "authorises its own class and below."
                            % (plan_id, record.get("risk"), risk))
    if consume:
        record["used_at"] = _now()
        _write_private_json(path, record)
    parts = dict(parts)
    parts["record"] = record
    return parts


def plan_records(cfg=None, directory=None):
    """Every plan record on this host, newest first. For ``gate.py plan list``."""
    base = plan_dir(cfg, directory)
    out = []
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return out
    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(base, name), "r", encoding="utf-8") as fh:
                out.append(json.load(fh))
        except (OSError, ValueError):
            continue
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out


def _write_private_json(path, record):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _stamp(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)\
        .replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _prune_plans(base, grace=86400):
    """Drop records long past their expiry; a used one is kept for the grace window."""
    cutoff = time.time() - grace
    try:
        names = os.listdir(base)
    except OSError:
        return
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(base, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                record = json.load(fh)
            if float(record.get("expires_epoch") or 0) <= cutoff:
                os.unlink(path)
        except (OSError, ValueError):
            continue


def plan_from_dict(data):
    """Rebuild a :class:`Plan` from ``as_dict()`` output, without trusting it."""
    if not isinstance(data, dict):
        raise GateError("a plan must be a JSON object as produced by Plan.as_dict()")
    plan_obj = Plan(data.get("operation") or "unnamed operation",
                    data.get("risk") or "R2",
                    data.get("target") or "")
    blocks = data.get("blocks") or {}
    if not isinstance(blocks, dict):
        raise GateError("plan.blocks must be an object of block name -> lines")
    for name, lines in blocks.items():
        plan_obj.set(name, lines if isinstance(lines, list) else [lines])
    plan_obj.backup = data.get("backup")
    plan_obj.pin = data.get("pin")
    if data.get("created_at"):
        plan_obj.created_at = data["created_at"]
    return plan_obj


def check_plan_authorises(data, target, risk):
    """Does this rendered plan authorise ``risk`` on ``target``? Raise if not.

    Re-validates the plan rather than believing its own ``problems`` field: a
    plan that arrives as a file has been outside this process, and the whole
    point of the block list is that it is checked where it is used.
    """
    plan_obj = plan_from_dict(data)
    problems = plan_obj.validate()
    if problems:
        raise GateError("the plan does not validate:\n  - " + "\n  - ".join(problems))
    if _rank(plan_obj.risk) < _rank(risk):
        raise GateError("the plan is class %s; this call classifies as %s. A plan authorises its "
                        "own class and below." % (plan_obj.risk, risk))
    names = [part.strip() for part in re.split(r"[,\s]+", plan_obj.target or "") if part.strip()]
    if target not in names:
        raise GateError("the plan targets %s; this call runs against %r."
                        % (", ".join(names) or "nothing", target))
    return plan_obj


def gate(plan_obj, yes=False, typed=None, first_offer=True):
    """Enforce the plan's gate. Returns ``True`` to apply, raises otherwise.

    ``first_offer`` encodes the agent rule: ``--yes`` is never added in the same
    turn the command is first proposed. A dry run is shown, the human answers,
    and only then does the flag appear. "The user said go ahead earlier" is not
    an answer to this plan.
    """
    problems = plan_obj.validate()
    if problems:
        raise GateError("plan is not renderable:\n  - " + "\n  - ".join(problems))
    if not plan_obj.requires_yes():
        return True
    if not yes:
        raise GateError("dry run only. Re-run with --yes to apply.")
    if yes and first_offer:
        raise GateError("--yes must not be added in the same turn the command is first "
                        "proposed. Show the dry run, get an explicit answer, then apply.")
    if plan_obj.requires_typed_confirm():
        want = plan_obj.confirm_phrase()
        if (typed or "").strip() != want:
            raise GateError("this operation is irreversible and needs the exact phrase:\n  %s"
                            % want)
    if plan_obj.requires_backup() and not plan_obj.backup:
        raise GateError("%s refused: no verified backup attached." % plan_obj.risk)
    return True


def _cli(argv=None):
    """Small CLI so a shell procedure can hold the same lock the door takes."""
    import argparse
    ap = argparse.ArgumentParser(
        prog="gate.py", description="Mutation discipline: risk classes, plans, the fleet lock.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("info", help="print the risk classes, blocks and red lines as JSON")
    lock_ap = sub.add_parser("lock", help="take, inspect or release the fleet front lock")
    lock_ap.add_argument("action", choices=["take", "status", "release"])
    lock_ap.add_argument("name", nargs="?", default=AUTH_LOCK)
    lock_ap.add_argument("--ttl", type=int, default=LOCK_TTL_SECONDS,
                         help="seconds before a crashed holder stops blocking others")
    lock_ap.add_argument("--operation", help="what the lock is being held for, shown to whoever "
                                            "finds it busy")
    lock_ap.add_argument("--token", help="token printed by 'lock take', required to release")
    lock_ap.add_argument("--dir", dest="directory", help="override the lock directory")
    lock_ap.add_argument("--json", action="store_true")
    plan_ap = sub.add_parser("plan", help="mint, verify or list the issued plan ids")
    plan_ap.add_argument("action", choices=["mint", "check", "list"])
    plan_ap.add_argument("command_or_id", nargs="?",
                         help="mint: the plan-building command; check: the plan id")
    plan_ap.add_argument("target", nargs="?", help="mint: the instance the plan was built for")
    plan_ap.add_argument("--risk", default=None,
                         help="risk class the plan covers (default R2 on mint)")
    plan_ap.add_argument("--ttl", type=int, default=PLAN_TTL_SECONDS,
                         help="seconds the id stays valid (default %d)" % PLAN_TTL_SECONDS)
    plan_ap.add_argument("--plan", dest="plan_file",
                         help="mint: the rendered plan (Plan.as_dict() JSON) the id stands for")
    plan_ap.add_argument("--for", dest="for_target",
                         help="check: the instance the call runs against")
    plan_ap.add_argument("--consume", action="store_true",
                         help="check: burn the record, as the exec door does when it applies")
    plan_ap.add_argument("--dir", dest="plan_directory", help="override the plan directory")
    plan_ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd in (None, "info"):
        print(json.dumps({"risk_classes": RISK_CLASSES, "blocks": BLOCK_NAMES,
                          "extra_blocks": EXTRA_BLOCK_NAMES,
                          "red_lines": sorted(RED_LINES),
                          "zero_retry": sorted(RETRY_RULES),
                          "plan_id_commands": list(PLAN_ID_COMMANDS),
                          "locks": {"default": AUTH_LOCK, "ttl_seconds": LOCK_TTL_SECONDS}},
                         indent=2))
        return 0

    cfg = None
    try:
        import config as _config
        cfg = _config.load_config()
    except Exception:
        cfg = None

    if args.cmd == "plan":
        return _plan_cli(args, cfg)

    lock = FleetLock(args.name, cfg=cfg, ttl=args.ttl, operation=args.operation,
                     directory=args.directory)
    if args.action == "status":
        state = lock.describe()
        print(json.dumps(state, indent=2) if args.json else _format_lock_status(state))
        return 0
    if args.action == "take":
        try:
            lock.acquire()
        except GateError as exc:
            sys.stderr.write("refused: %s\n" % exc)
            return 4
        if args.json:
            print(json.dumps({"lock": lock.name, "token": lock.token,
                              "expires_at": lock.record["expires_at"]}, indent=2))
        else:
            print(lock.token)
        return 0
    if not args.token:
        sys.stderr.write("error: lock release needs the --token printed by 'lock take'\n")
        return 2
    lock.token = args.token
    try:
        released = lock.release()
    except GateError as exc:
        sys.stderr.write("refused: %s\n" % exc)
        return 4
    print("released" if released else "not held by this token")
    return 0


def _plan_cli(args, cfg):
    """``gate.py plan mint|check|list`` — the registry from a shell procedure."""
    directory = args.plan_directory
    if args.action == "list":
        records = plan_records(cfg, directory)
        if args.json:
            print(json.dumps(records, indent=2))
        else:
            for record in records:
                print("%-52s %-3s %s%s" % (record.get("plan_id"), record.get("risk"),
                                           record.get("expires_at"),
                                           "  USED %s" % record["used_at"]
                                           if record.get("used_at") else ""))
        return 0
    if args.action == "mint":
        if not args.command_or_id or not args.target:
            sys.stderr.write("error: plan mint needs <command> <instance>\n")
            return 2
        plan_obj = None
        if args.plan_file:
            try:
                with open(args.plan_file, "r", encoding="utf-8") as fh:
                    plan_obj = plan_from_dict(json.load(fh))
            except (OSError, ValueError) as exc:
                sys.stderr.write("error: --plan could not be read as a plan: %s\n" % exc)
                return 2
        try:
            plan_id = make_plan_id(args.command_or_id, args.target, plan=plan_obj,
                                   risk=args.risk, cfg=cfg, directory=directory, ttl=args.ttl)
        except GateError as exc:
            sys.stderr.write("refused: %s\n" % exc)
            return 4
        print(json.dumps({"plan_id": plan_id}, indent=2) if args.json else plan_id)
        return 0
    try:
        parts = check_plan_id(args.command_or_id, target=args.for_target, risk=args.risk,
                              cfg=cfg, directory=directory, consume=args.consume)
    except GateError as exc:
        sys.stderr.write("refused: %s\n" % exc)
        return 4
    record = parts["record"]
    print(json.dumps(record, indent=2) if args.json
          else "valid: %s (%s, expires %s)%s" % (record["plan_id"], record["risk"],
                                                 record["expires_at"],
                                                 " — consumed" if args.consume else ""))
    return 0


def _format_lock_status(state):
    if not state.get("held"):
        return "%s: free (%s)" % (state["lock"], state["path"])
    return ("%s: held by %s (pid %s)%s since %s, %d s left%s"
            % (state["lock"], state.get("owner"), state.get("pid"),
               " for %r" % state["operation"] if state.get("operation") else "",
               state.get("acquired_at"), state.get("seconds_left") or 0,
               " — EXPIRED, the next taker evicts it" if state.get("expired") else ""))


if __name__ == "__main__":
    sys.exit(_cli())
