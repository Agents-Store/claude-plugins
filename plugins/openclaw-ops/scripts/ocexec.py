#!/usr/bin/env python3
"""ocexec.py — the single door into the openclaw CLI of one instance.

    ocexec.py <instance> [options] -- <openclaw args...>

Why one door
------------
Direct ``docker compose exec -T`` is the primary path, not the site wrapper:
wrappers drift between instances of the same host, their pass-through arm is
literally the same call, and without a guaranteed ``-T`` a non-interactive
invocation mangles ``--json`` output. Because every CLI call goes through here,
this is also the only place that needs to enforce the bans and the only place
that has to redact — and it always does, on both streams.

Modes
-----
hot   ``docker compose -p <project> exec -T <service> run-with-infisical openclaw <argv>``
      The normal path. Secrets are injected inside the container and never
      cross the boundary. Without the injection wrapper in the image, the same
      call runs without it.
cold  ``docker run --rm -v <state-dir>:/home/node/.openclaw <image> openclaw <argv>``
      Only when the gateway is not running, and only for the subcommands that
      are safe on a broken instance: setup, qa, database. Anything else is
      refused with the reason, because a cold container is not a gateway.

Refusals (never negotiable)
---------------------------
* an ``alien`` instance — it failed the layout fingerprint, so nothing here
  knows what it is;
* ``--accept-capabilities`` — capability consent is printed for a human;
  upstream deliberately made ``--yes`` and ``doctor --fix`` unable to grant it;
* ``models status --probe`` while the gateway runs — it needs the gateway
  stopped, and running it live is a lie dressed as a status read;
* a cold container against the state directory of a RUNNING instance — gateway
  startup enforces unique state-directory ownership;
* R3/R4 argv — an irreversible or backup-requiring operation must go through
  the command that builds the eight-block plan, not through the escape hatch;
* anything above R0 with no plan behind it — ``--yes`` alone buys nothing here.
  A mutation is authorised either by the rendered plan (``--plan <file>``) or by
  the id of the plan a plan-building command already showed to the operator
  (``--plan-id <command>/<instance>/<stamp>``). The id is looked up in the
  registry the minting command wrote — issued here, unexpired, this instance,
  this risk class — and is burned on use, so one plan buys one mutation. Without
  one of the two, the door is a way around the mutation discipline rather than
  the place that enforces it.

Locks
-----
Any credential mutation (``models auth <verb>``) takes the fleet-wide front lock
first (``gate.fleet_lock``). The runtime's own lock is a file lock inside one
state directory and serialises nothing across instances, which is the wrong
shape for a rotating single-use refresh token. A procedure that already holds
the lock passes its token with ``--lock-token`` and the door inherits it instead
of deadlocking against it.

Exit codes
----------
    <child>  the CLI's own exit code (0/1/2 carry meaning: see ocjson)
    64       refused by policy
    65       instance unknown or unusable
    66       docker unavailable
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import config as cfgmod          # noqa: E402
import discovery                 # noqa: E402
import gate                      # noqa: E402
import ocjson                    # noqa: E402
import redact                    # noqa: E402

EXIT_REFUSED, EXIT_TARGET, EXIT_DOCKER = 64, 65, 66

# The only subcommands documented as safe on a broken instance.
SAFE_BROKEN = ("setup", "qa", "database")

# Reads with no observable effect.
READ_ONLY = {
    ("--version",), ("--help",), ("docs",), ("health",), ("status",),
    ("doctor", "--lint"), ("doctor", "--post-upgrade"),
    ("models", "list"), ("models", "status"), ("models", "auth", "list"),
    ("plugins", "list"), ("skills", "list"), ("cron", "list"),
    ("memory", "status"), ("gateway", "status"), ("config", "get"),
    ("security", "audit"), ("backup", "list"), ("database", "status"),
}

# Reads that cost money, hold a lock, or move state.
R1_MARKERS = (("models", "status", "--probe"), ("memory", "index"), ("run",), ("chat",))

# Backup-requiring and irreversible operations: they belong to a command that
# builds a plan, not to the escape hatch.
R3_MARKERS = (("memory", "index", "--force"), ("sessions", "prune"), ("database", "compact"),
              ("backup", "restore"))
R4_MARKERS = (("update",), ("upgrade",), ("secrets", "set"), ("gateway", "token"),
              ("security", "audit", "--fix"), ("doctor", "--fix"))


# --------------------------------------------------------------------------- #
# argv classification
# --------------------------------------------------------------------------- #

def _has(argv, marker):
    """Does argv contain every token of ``marker``, in order?"""
    idx = 0
    for token in marker:
        while idx < len(argv) and argv[idx] != token:
            idx += 1
        if idx == len(argv):
            return False
        idx += 1
    return True


def classify_argv(argv):
    """Assign a risk class to an ``openclaw`` command line.

    The classification is by effect, not by name: ``models status --probe`` is
    called status and is an R1 because it requires the gateway down and changes
    what the fleet is doing while it runs.
    """
    for marker in R4_MARKERS:
        if _has(argv, marker):
            return "R4", "matches %s" % " ".join(marker)
    for marker in R3_MARKERS:
        if _has(argv, marker):
            return "R3", "matches %s" % " ".join(marker)
    for marker in R1_MARKERS:
        if _has(argv, marker):
            return "R1", "matches %s" % " ".join(marker)
    positional = [a for a in argv if not a.startswith("-")]
    flags = [a for a in argv if a.startswith("-")]
    for marker in READ_ONLY:
        head = [t for t in marker if not t.startswith("-")]
        tail = [t for t in marker if t.startswith("-")]
        if positional[:len(head)] == head and all(f in flags for f in tail):
            if any(f in flags for f in ("--fix", "--force", "--write", "--set", "--apply")):
                return "R2", "read subcommand carrying a write flag"
            return "R0", "read-only subcommand"
    return "R2", "not on the read-only list — treated as a reversible mutation"


def derive_command_key(argv):
    """Pick the exit-code contract that applies to this command line."""
    for key in ocjson.EXIT_CONTRACTS:
        if _has(argv, tuple(key.split())):
            return key
    return None


# --------------------------------------------------------------------------- #
# refusals
# --------------------------------------------------------------------------- #

class Refusal(Exception):
    """Policy said no. The message is the whole point: it explains the rule."""


def _shown(argv, count=3):
    """The user's own argv, redacted, for a message a human will read."""
    return " ".join(redact.redact_argv(list(argv)[:count]))


def needs_fleet_lock(argv, risk):
    """Credential mutations serialise across the whole fleet, not per state dir."""
    return risk != "R0" and _has(argv, ("models", "auth"))


def require_plan_authority(record, risk, plan_id=None, plan=None, cfg=None, consume=True):
    """Refuse a mutation that no plan stands behind.

    ``--yes`` answers "did a human see this?"; it does not answer "is there a
    backup and an executable rollback?". Only a plan does, so above R0 the door
    wants one: the plan itself, or the id of the plan already shown.

    An id is checked against the registry the minting command wrote, not against
    a regex: it must have been issued here, still be inside its TTL, name this
    instance and cover this risk class. ``consume`` burns it, so one plan buys
    one mutation and cannot be carried to the next call.
    """
    name = record["name"]
    if plan is not None:
        try:
            gate.check_plan_authorises(plan, name, risk)
        except gate.GateError as exc:
            raise Refusal("the plan passed with --plan does not authorise this call: %s" % exc)
        return True
    if plan_id:
        try:
            gate.check_plan_id(plan_id, name, risk=risk, cfg=cfg, consume=consume)
        except gate.GateError as exc:
            raise Refusal(str(exc))
        return True
    raise Refusal(
        "class %s on %s needs a plan behind it, and this call carries none. The escape hatch "
        "runs one command; it cannot build the eight blocks, so it does not get to skip them. "
        "Run the command that owns this operation (/openclaw-ops:repair, :update, :auth, "
        ":shared-sync, :clone) — it shows the plan, then passes --plan-id <command>/%s/<stamp> "
        "when it applies it. A step outside those commands hands over the rendered plan itself "
        "with --plan <file>, and it must carry a BACKUP and an executable ROLLBACK."
        % (risk, name, name))


def check_policy(record, argv, risk, mode, yes, plan_id=None, plan=None, dry_run=False,
                 cfg=None):
    gate.check_banned_args(argv)
    if record.get("profile") == "alien" or record.get("state") == "alien":
        raise Refusal("%s failed the layout fingerprint (alien). It stays in the inventory; "
                      "nothing runs against it." % record["name"])
    if not record.get("managed", True):
        raise Refusal("%s is not managed by this fleet config (role=%s). Reads of the host side "
                      "are fine; running its CLI is not."
                      % (record["name"], record.get("role")))
    if _has(argv, ("models", "status", "--probe")) and record.get("state") != "down":
        raise Refusal(
            "models status --probe requires a stopped gateway; %s is %s. Use "
            "'models status --check' for monitoring (exit 1 = expired, 2 = expiring), or run "
            "the probe as an explicit scripted step that stops the gateway and restores it in a "
            "trap." % (record["name"], record.get("state")))
    if risk in ("R3", "R4"):
        raise Refusal(
            "%s is class %s and needs a plan with a backup%s. The escape hatch does not build "
            "plans — run the dedicated command so the dry run, the snapshot and the rollback "
            "exist before anything changes."
            % (_shown(argv), risk, " and a typed confirmation" if risk == "R4" else ""))
    if risk != "R0" and not yes and not dry_run:
        # A dry run shows the resolved call and runs nothing, which is the step the exec
        # command documents first; refusing to preview a mutation would leave the operator
        # answering a plan nobody could print.
        raise Refusal("%s is class %s (%s). Re-run with --yes once the plan has been shown and "
                      "answered." % (_shown(argv) or "command", risk,
                                     gate.RISK_CLASSES[risk]["label"]))
    if risk != "R0" and not dry_run:
        require_plan_authority(record, risk, plan_id, plan, cfg=cfg)
    if mode == "cold":
        if record.get("state") != "down":
            raise Refusal(
                "cold mode is refused while %s is %s: a second container on a live state "
                "directory violates the gateway's unique state-directory ownership."
                % (record["name"], record.get("state")))
        head = next((a for a in argv if not a.startswith("-")), None)
        if head not in SAFE_BROKEN:
            raise Refusal(
                "%s is down, so only the cold path is available, and only %s are safe there. "
                "%s is not one of them: bring the gateway up first, or read the host side "
                "(files, compose logs) instead."
                % (record["name"], "/".join(SAFE_BROKEN),
                   repr(redact.scrub(head)) if head else "(none)"))
    return True


def choose_mode(record, requested):
    """Resolve ``auto`` into ``hot`` or ``cold``, or explain why neither is possible."""
    state = record.get("state")
    caps = record.get("capabilities") or {}
    if requested in ("hot", "cold"):
        return requested
    if state in ("ok", "degraded") and caps.get("exec_mode") == "hot":
        return "hot"
    if (record.get("paths") or {}).get("state_dir"):
        return "cold"
    raise Refusal("no usable exec path for %s: the gateway is %s and no state-directory mount "
                  "is known." % (record["name"], state))


# --------------------------------------------------------------------------- #
# execution
# --------------------------------------------------------------------------- #

def build_argv(record, argv, mode, use_infisical=True, user=None, service=None, image=None):
    if mode == "hot":
        caps = record.get("capabilities") or {}
        with_inf = bool(use_infisical and caps.get("run_with_infisical") is not False)
        return discovery.compose_exec_argv(record, argv, use_infisical=with_inf,
                                           user=user, service=service)
    return discovery.cold_run_argv(record, argv, image=image)


def execute(record, argv, mode, timeout=120, use_infisical=True, user=None,
            service=None, image=None):
    """Run the command and return an :class:`ocjson.OcResult` with scrubbed streams."""
    cmd = build_argv(record, argv, mode, use_infisical, user, service, image)
    rc, out, err = discovery.run(cmd, timeout=timeout)
    out_res = redact.scrub_stream(out)
    err_res = redact.scrub_stream(err)
    return ocjson.interpret(derive_command_key(argv), rc, out_res.text, err_res.text,
                            argv=redact.redact_argv(cmd),
                            scrubbed=out_res.count + err_res.count), cmd


# --------------------------------------------------------------------------- #

def build_parser():
    ap = argparse.ArgumentParser(
        prog="ocexec.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("instance", help="instance name or alias")
    ap.add_argument("--mode", choices=["auto", "hot", "cold"], default="auto")
    ap.add_argument("--json", action="store_true", help="print an envelope instead of raw streams")
    ap.add_argument("--yes", action="store_true", help="required for anything above R0")
    ap.add_argument("--plan-id", dest="plan_id",
                    help="id of the plan that authorised this call, minted by the command that "
                         "built it: <command>/<instance>/<utc-stamp>. Required above R0 unless "
                         "--plan is given")
    ap.add_argument("--plan",
                    help="path to a rendered plan (gate.Plan.as_dict() as JSON). Re-validated "
                         "here: all eight blocks, a BACKUP, an executable ROLLBACK")
    ap.add_argument("--lock-token", dest="lock_token",
                    help="token of a fleet lock this procedure already holds, so a credential "
                         "mutation inherits it instead of deadlocking against it")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--service", help="override the compose service name")
    ap.add_argument("--user", help="run as this user inside the container")
    ap.add_argument("--image", help="image for cold mode (default: the instance's own)")
    ap.add_argument("--no-infisical", action="store_true",
                    help="skip the secret-injection wrapper (diagnosing delivery itself)")
    ap.add_argument("--config", help="explicit fleet config path")
    ap.add_argument("--prefix", help="compose project prefix")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the resolved command line and the risk class, run nothing")
    ap.add_argument("args", nargs="*",
                    help="everything after -- is passed to openclaw verbatim (split off before "
                         "parsing, so our own options keep working after the instance name)")
    return ap


def split_passthrough(raw):
    """Split our own options from the openclaw argv at the first bare ``--``.

    argparse's REMAINDER swallows every option that follows the first
    positional, so ``ocexec.py <instance> --json -- health`` would parse with
    ``--json`` inside the passthrough and off in our own options — the exact
    invocation every command and skill here documents. Splitting first makes
    the documented form mean what it says.
    """
    raw = list(raw)
    if "--" in raw:
        cut = raw.index("--")
        return raw[:cut], raw[cut + 1:]
    return raw, None


def main(argv=None):
    head, tail = split_passthrough(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(head)
    passthrough = list(args.args) if tail is None else tail
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    if not passthrough:
        sys.stderr.write("error: nothing to run. Usage: ocexec.py <instance> -- <openclaw args>\n")
        return EXIT_REFUSED

    cfg = cfgmod.load_config(args.config)
    for line in cfg.warnings:
        sys.stderr.write("warning: %s\n" % line)
    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=True)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_DOCKER

    wanted = cfg.canonical_name(args.instance) if cfg.present else args.instance
    record = next((r for r in records if r["name"] == wanted), None)
    if record is None:
        sys.stderr.write("error: no instance named %r on this host. Known: %s\n"
                         % (args.instance, ", ".join(r["name"] for r in records) or "(none)"))
        return EXIT_TARGET

    risk, why = classify_argv(passthrough)
    plan = None
    try:
        if args.plan:
            with open(args.plan, "r", encoding="utf-8") as fh:
                plan = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.stderr.write("refused: --plan could not be read as a JSON plan: %s\n" % exc)
        return EXIT_REFUSED

    try:
        mode = choose_mode(record, args.mode)
        check_policy(record, passthrough, risk, mode, args.yes,
                     plan_id=args.plan_id, plan=plan, dry_run=args.dry_run, cfg=cfg)
    except (Refusal, gate.GateError) as exc:
        if args.json:
            sys.stdout.write(json.dumps({"ok": False, "refused": str(exc), "instance": wanted,
                                         "risk": risk, "reason": why}, indent=2) + "\n")
        else:
            sys.stderr.write("refused: %s\n" % exc)
        return EXIT_REFUSED

    if args.dry_run:
        cmd = build_argv(record, passthrough, mode, not args.no_infisical,
                         args.user, args.service, args.image)
        shown = redact.redact_argv(cmd)
        payload = {"instance": wanted, "mode": mode, "risk": risk, "reason": why,
                   "command": shown}
        notes = []
        if risk != "R0":
            notes.append("running this needs --yes and the plan that authorises it "
                         "(--plan-id or --plan)")
        if needs_fleet_lock(passthrough, risk):
            notes.append("takes the %s front lock for the duration" % gate.AUTH_LOCK)
        if notes:
            payload["notes"] = notes
        sys.stdout.write((json.dumps(payload, indent=2) if args.json
                          else "mode=%s risk=%s (%s)\n%s%s"
                          % (mode, risk, why, " ".join(shown),
                             "".join("\n[%s]" % n for n in notes))) + "\n")
        return 0

    lock = None
    if needs_fleet_lock(passthrough, risk):
        try:
            lock = gate.fleet_lock(gate.AUTH_LOCK, cfg=cfg, token=args.lock_token,
                                   operation="%s: %s" % (wanted, _shown(passthrough)))
        except gate.GateError as exc:
            if args.json:
                sys.stdout.write(json.dumps({"ok": False, "refused": str(exc),
                                             "instance": wanted, "risk": risk,
                                             "lock": gate.AUTH_LOCK}, indent=2) + "\n")
            else:
                sys.stderr.write("refused: %s\n" % exc)
            return EXIT_REFUSED
    try:
        result, _cmd = execute(record, passthrough, mode, timeout=args.timeout,
                               use_infisical=not args.no_infisical, user=args.user,
                               service=args.service, image=args.image)
    finally:
        if lock is not None:
            lock.release()
    if args.json:
        payload = result.as_dict()
        payload.update({"ok": result.ok, "instance": wanted, "mode": mode, "risk": risk})
        if args.plan_id:
            payload["plan_id"] = args.plan_id
        if lock is not None:
            payload["lock"] = gate.AUTH_LOCK
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        if result.scrubbed:
            sys.stderr.write("[scrubbed: %d match%s]\n"
                             % (result.scrubbed, "" if result.scrubbed == 1 else "es"))
        if result.command_key:
            sys.stderr.write("[%s: exit %d = %s (%s)]\n"
                             % (result.command_key, result.rc, result.label, result.explanation))
    return result.rc


if __name__ == "__main__":
    sys.exit(main())
