#!/usr/bin/env python3
"""healthcheck.py — the expensive probe battery, run on demand.

    healthcheck.py [SELECTOR] [--json|--table] [--snapshot] [options]

Discovery is cheap and runs constantly; this is the opposite. Every instance
costs several in-container calls, so nothing here runs implicitly. Everything it
runs is class R0 — a read with no observable effect — and that is asserted per
command, not assumed: a battery that quietly mutates while calling itself a
health check is the exact failure this plugin exists to prevent.

Two independent verdicts, and the point is that they can disagree
------------------------------------------------------------------
HEALTH   what the instance says about itself: container state, /healthz,
         /startupz, /readyz, delivery queues, credential status, memory
         subsystem.
LIVENESS what an outside observer sees it DO: how long ago the log moved, when
         the timers last fired, when the index was last written.

A gateway can answer every probe with 200 while its log has not moved for weeks.
No self-report catches that, because every self-report is produced by the same
process that stopped doing work. So the two columns are computed from disjoint
evidence and printed side by side; ``HEALTH ok`` next to ``LIVENESS stale`` is
itself the finding (``fleet.liveness.zombie``), not a rendering artefact.

Probe notes that are easy to get wrong
--------------------------------------
* ``/healthz`` only proves the HTTP server is up. ``/startupz`` adds "startup
  finished" and deliberately ignores channel health. Only ``/readyz`` means the
  channels passed a deep check — and **only with a Bearer token**: unauthenticated
  it answers a bare ``{"ready": false}`` with no list of what failed, which reads
  like a healthy negative and is not.
* ``health --json`` with top-level ``ok: true`` does **not** mean the delivery
  queues are clear. ``deliveryQueues.ingressPressure`` is parsed explicitly.
* ``models status --check`` is the monitoring path: exit 1 = expired, 2 =
  expiring. ``--probe`` is never used here — it requires a stopped gateway, so
  running it against a live fleet is a mutation wearing the word "status".
* Probes run **inside** the container. The gateway bearer token is resolved from
  the container's own environment and never crosses the boundary, is never
  passed on a host command line, and is never printed.

A subcommand this runtime does not have is reported as ``unsupported``, never as
a failure: the fleet spans several versions and a missing verb is drift, not a
defect. Downgrade-only rule: this battery may push an instance from ``ok`` to
``degraded``; it never promotes one, because a subsystem proven dead outranks a
green container.

Exit codes
----------
    0  battery ran, no critical or high finding
    1  runtime error (docker unreachable, sweep failed)
    2  fleet config missing or invalid
    3  selector refused
    4  selector matched nothing
    5  at least one critical- or high-severity finding
    6  warn-severity findings only
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, HERE)

import config as cfgmod          # noqa: E402
import discovery                 # noqa: E402
import fleet                     # noqa: E402
import ocexec                    # noqa: E402
import ocjson                    # noqa: E402
import redact                    # noqa: E402

SCHEMA = "openclaw-ops/health/1"
EXIT_OK, EXIT_RUNTIME, EXIT_CONFIG, EXIT_REFUSED, EXIT_EMPTY = 0, 1, 2, 3, 4
EXIT_BLOCKING_FINDINGS, EXIT_WARN_FINDINGS = 5, 6

# Documented upstream: the gateway listens on this port inside the container.
DEFAULT_CONTAINER_PORT = 18789

# Environment names a deployment may use for the gateway bearer token. The value
# is read inside the container and only the NAME ever leaves it.
TOKEN_ENV_CANDIDATES = [
    "OPENCLAW_GATEWAY_TOKEN", "OPENCLAW_GATEWAY_AUTH_TOKEN", "OPENCLAW_AUTH_TOKEN",
    "OPENCLAW_TOKEN", "OPENCLAW_GATEWAY_BEARER", "OPENCLAW_API_TOKEN", "GATEWAY_TOKEN",
]

# The one severity vocabulary of this plugin, ascending. It is the vocabulary the
# findings catalog declares, and report.py, /audit and the auditor agent all read
# the same four names. A fifth spelling anywhere is a bug, not a synonym.
SEVERITIES = ("info", "warn", "high", "critical")
SEVERITY_RANK = {name: index for index, name in enumerate(SEVERITIES)}
# The two classes that make a run "not clean" — exit 5, and what downgrades a verdict.
BLOCKING = ("critical", "high")


# Upstream speaks its own severity words. They are translated by a TABLE, not by
# a chain ending in a default: a spelling nobody has mapped is a new upstream
# word, and filing it as `info` is how a critical lint finding leaves the report
# without anyone noticing. An unmapped word fails here, exactly like an unknown
# severity anywhere else in this file.
UPSTREAM_SEVERITIES = {
    "critical": "critical", "fatal": "critical",
    "error": "high",
    "warn": "warn", "warning": "warn",
    "info": "info",
}


def upstream_severity(value, where="upstream finding"):
    """Map an upstream severity word into the one vocabulary, or fail loudly."""
    try:
        return UPSTREAM_SEVERITIES[str(value).strip().lower()]
    except (KeyError, TypeError):
        raise ValueError(
            "unknown upstream severity %r in %s: the spellings this plugin translates are %s, "
            "and the vocabulary they map into is %s. Add the mapping deliberately — a word "
            "silently filed as 'info' is a finding nobody reads."
            % (value, where, ", ".join(sorted(UPSTREAM_SEVERITIES)), ", ".join(SEVERITIES)))


def severity_rank(value, where="finding"):
    """Guarded lookup. An unknown severity fails loudly instead of being dropped."""
    try:
        return SEVERITY_RANK[value]
    except (KeyError, TypeError):
        raise ValueError(
            "unknown severity %r in %s: the vocabulary is %s"
            % (value, where, ", ".join(SEVERITIES)))


UNSUPPORTED_RE = re.compile(
    r"(unknown|unrecognized|unrecognised|invalid)\s+(command|argument|option|flag)"
    r"|command not found|is not a( known)? command|no such (command|subcommand)", re.I)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)\
        .isoformat().replace("+00:00", "Z")


def _dig(doc, *names, **kw):
    """Find the first value stored under any of ``names`` anywhere in ``doc``.

    Runtimes differ in nesting and in camel/snake case across the versions a
    drifted fleet actually runs, so a fixed path would report "missing" on half
    the instances. Depth is capped; the search is breadth-first so the shallowest
    match wins.
    """
    depth = kw.get("depth", 6)
    wanted = {n.lower().replace("_", "") for n in names}
    queue = [(doc, 0)]
    while queue:
        node, level = queue.pop(0)
        if level > depth:
            continue
        if isinstance(node, dict):
            for key, val in node.items():
                if str(key).lower().replace("_", "") in wanted:
                    return val
            for val in node.values():
                if isinstance(val, (dict, list)):
                    queue.append((val, level + 1))
        elif isinstance(node, list):
            for val in node[:64]:
                if isinstance(val, (dict, list)):
                    queue.append((val, level + 1))
    return None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _epoch(value):
    """Parse an ISO-8601 or epoch timestamp into epoch seconds, or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) / 1000.0 if value > 1e11 else float(value)
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{10,13}", text):
        num = float(text)
        return num / 1000.0 if num > 1e11 else num
    text = re.sub(r"\.\d+", "", text).replace("Z", "+0000").replace("+00:00", "+0000")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            return parsed.timestamp()
        except ValueError:
            continue
    return None


def _age_hours(value):
    """Hours since ``value``, clamped at zero. A future stamp reads as 'just now'."""
    signed = _age_hours_signed(value)
    return None if signed is None else max(0.0, signed)


def _age_hours_signed(value):
    """Hours since ``value``, negative when it lies in the future.

    Liveness needs the sign: a timestamp ahead of the clock is unusable evidence,
    and clamping it to zero turns a broken clock into proof of activity.
    """
    stamp = _epoch(value)
    if stamp is None:
        return None
    return (time.time() - stamp) / 3600.0


# --------------------------------------------------------------------------- #
# findings
# --------------------------------------------------------------------------- #
#
# Finding ids are the contract with report.py, /repair and the auditor. They are
# stable strings: renaming one breaks every delta comparison ever taken, so a new
# symptom gets a NEW id rather than a redefinition of an old one.
#
def finding(rec, fid, severity, message, source, fix=None, evidence=None):
    """Attach one finding to an instance result. ``finding_id`` is delta-stable."""
    severity_rank(severity, "finding %r" % fid)
    rec["findings"].append({
        "id": fid,
        "finding_id": "%s/%s" % (rec["name"], fid),
        "instance": rec["name"],
        "severity": severity,
        "message": message,
        "source": source,
        "fix": fix,
        "evidence": evidence,
    })


def worst(findings_list):
    rank = -1
    for item in findings_list:
        rank = max(rank, severity_rank(item["severity"],
                                       "finding %r" % item.get("id")))
    return SEVERITIES[rank] if rank >= 0 else None


# --------------------------------------------------------------------------- #
# in-container HTTP probes
# --------------------------------------------------------------------------- #

# Runs inside the container. Resolves the bearer token from the container's own
# environment into a shell variable, uses it, and never echoes it: only the NAME
# of the variable is printed. Client preference is curl, then node's fetch, then
# wget (wget cannot report a status code portably, so it reports 200/000 only).
#
# The token never reaches a command line. An argument list is world-readable
# through /proc on every process in the container, so a header passed as -H or
# --header would publish the gateway's operator credential to anything that can
# run ps — the same leak this plugin refuses everywhere else. Each client is
# therefore fed the header out of band: curl reads a config file from stdin,
# node reads an environment variable, wget reads a mode-600 WGETRC written by a
# here-document and removed immediately afterwards.
_PROBE_SH = r'''
set -u
PORT="${OC_PORT:-18789}"
TOK=""; TOKNAME=""
for v in ${OC_TOKEN_ENVS:-}; do
  val=$(printenv "$v" 2>/dev/null) || val=""
  if [ -n "$val" ]; then TOK="$val"; TOKNAME="$v"; break; fi
done
printf 'TOKEN\t%s\n' "${TOKNAME:-none}"
if command -v curl >/dev/null 2>&1; then CLIENT=curl
elif command -v node >/dev/null 2>&1; then CLIENT=node
elif command -v wget >/dev/null 2>&1; then CLIENT=wget
else CLIENT=none; fi
printf 'CLIENT\t%s\n' "$CLIENT"
NODE_SNIPPET='const h=process.env.OCT?{Authorization:"Bearer "+process.env.OCT}:{};fetch(process.env.OCU,{headers:h}).then(async r=>{const t=await r.text();console.log(t.slice(0,600));console.log("OCSTATUS:"+r.status)}).catch(()=>console.log("OCSTATUS:000"))'
probe() {
  path="$1"; auth="$2"; out=""
  url="http://127.0.0.1:$PORT$path"
  case "$CLIENT" in
    curl)
      if [ "$auth" = "1" ] && [ -n "$TOK" ]; then
        out=$(curl -s -m 8 -w "\nOCSTATUS:%{http_code}" --config - "$url" 2>/dev/null <<OCCFG
header = "Authorization: Bearer $TOK"
OCCFG
) || out=""
      else
        out=$(curl -s -m 8 -w "\nOCSTATUS:%{http_code}" "$url" 2>/dev/null) || out=""
      fi
      ;;
    node)
      if [ "$auth" = "1" ] && [ -n "$TOK" ]; then
        out=$(OCU="$url" OCT="$TOK" node -e "$NODE_SNIPPET" 2>/dev/null) || out=""
      else
        out=$(OCU="$url" OCT="" node -e "$NODE_SNIPPET" 2>/dev/null) || out=""
      fi
      ;;
    wget)
      if [ "$auth" = "1" ] && [ -n "$TOK" ]; then
        rcfile=$(mktemp 2>/dev/null) || rcfile="/tmp/.ocwgetrc.$$"
        ( umask 077; cat > "$rcfile" <<OCRC
header = Authorization: Bearer $TOK
OCRC
        )
        body=$(WGETRC="$rcfile" wget -q -T 8 -O - "$url" 2>/dev/null) && out="$body
OCSTATUS:200" || out="OCSTATUS:000"
        rm -f "$rcfile"
      else
        body=$(wget -q -T 8 -O - "$url" 2>/dev/null) && out="$body
OCSTATUS:200" || out="OCSTATUS:000"
      fi
      ;;
    *) out="OCSTATUS:000" ;;
  esac
  code=$(printf '%s\n' "$out" | sed -n 's/^OCSTATUS:\(.*\)$/\1/p' | tail -n 1)
  body=$(printf '%s\n' "$out" | grep -v '^OCSTATUS:' | tr '\n' ' ' | cut -c1-500)
  printf 'PROBE\t%s\t%s\t%s\t%s\n' "$path" "$auth" "${code:-000}" "$body"
}
probe /healthz 0
probe /startupz 0
probe /readyz 0
if [ -n "$TOK" ]; then probe /readyz 1; fi
'''


def http_probes(record, port, token_envs, timeout=45):
    """Run the endpoint battery inside the container.

    Returns ``{"client", "token_env", "probes": {...}, "error"}``. A container
    with no HTTP client is a reported condition, not an exception.
    """
    project = record.get("project")
    service = (record.get("container") or {}).get("service") or "gateway"
    argv = ["docker", "compose", "-p", project, "exec", "-T",
            "-e", "OC_PORT=%d" % port,
            "-e", "OC_TOKEN_ENVS=%s" % " ".join(token_envs),
            service, "sh", "-lc", _PROBE_SH]
    rc, out, err = discovery.run(argv, timeout=timeout)
    result = {"client": None, "token_env": None, "probes": {}, "error": None}
    if rc != 0 and not out:
        first = (redact.scrub(err) or "").strip().splitlines()
        result["error"] = first[0] if first else "exit %d" % rc
        return result
    for line in (out or "").splitlines():
        parts = line.rstrip("\n").split("\t")
        if parts[0] == "TOKEN" and len(parts) >= 2:
            result["token_env"] = None if parts[1] == "none" else parts[1]
        elif parts[0] == "CLIENT" and len(parts) >= 2:
            result["client"] = None if parts[1] == "none" else parts[1]
        elif parts[0] == "PROBE" and len(parts) >= 4:
            path, auth, code = parts[1], parts[2] == "1", _as_int(parts[3])
            body = redact.scrub(parts[4]) if len(parts) > 4 else ""
            key = path.lstrip("/") + ("_auth" if auth else "")
            result["probes"][key] = {"path": path, "authenticated": auth,
                                     "status": code, "body": body.strip()[:400]}
    return result


# --------------------------------------------------------------------------- #
# CLI reads
# --------------------------------------------------------------------------- #

def oc_read(record, argv, timeout):
    """Run one read-only openclaw command through the single door.

    Asserts the command classifies as R0 before running it. Returns
    ``(OcResult|None, status)`` where status is ``ok`` / ``unsupported`` /
    ``refused`` / ``failed``.
    """
    risk, why = ocexec.classify_argv(argv)
    if risk != "R0":
        return None, "refused:%s (%s)" % (risk, why)
    try:
        mode = ocexec.choose_mode(record, "auto")
        ocexec.check_policy(record, argv, risk, mode, yes=False)
    except Exception as exc:                     # Refusal or GateError
        return None, "refused:%s" % exc
    if mode != "hot":
        return None, "refused:gateway is %s — CLI reads need a running gateway" % record.get("state")
    result, _cmd = ocexec.execute(record, argv, mode, timeout=timeout)
    if result.json is None and result.rc != 0 and UNSUPPORTED_RE.search(
            (result.stderr or "") + " " + (result.stdout or "")):
        return result, "unsupported"
    if result.json is None and result.rc not in (0, 1, 2):
        return result, "failed"
    return result, "ok"


# --------------------------------------------------------------------------- #
# the battery
# --------------------------------------------------------------------------- #

class Options(object):
    """Thresholds and switches, so the checks read as policy rather than magic."""

    def __init__(self, args):
        self.timeout = args.timeout
        self.container_port = args.container_port
        self.token_envs = args.token_env or TOKEN_ENV_CANDIDATES
        self.idle_hours = args.idle_hours
        self.stale_hours = args.stale_hours
        self.cron_drift_hours = args.cron_drift_hours
        self.memory_db_warn_mb = args.memory_db_warn_mb
        self.skip_http = args.skip_http
        self.skip_cli = args.skip_cli
        self.lint = args.lint


def check_container(rec, record):
    """Container-level evidence: state, restart count, docker health."""
    cont = record.get("container") or {}
    rec["metrics"]["restart_count"] = cont.get("restart_count")
    rec["metrics"]["docker_health"] = cont.get("health")
    rec["metrics"]["image"] = cont.get("image")
    rec["metrics"]["image_digest"] = cont.get("image_digest")
    if not cont.get("id"):
        finding(rec, "fleet.container.absent", "critical",
                "no gateway container exists for this compose project",
                source="docker:ps")
        return
    if cont.get("state") != "running":
        finding(rec, "fleet.container.down", "critical",
                "container state is %r (exit code %s)" % (cont.get("state"), cont.get("exit_code")),
                source="docker:inspect",
                fix="read the compose logs before any restart — a restart during a crash loop "
                    "overwrites the log holding the first cause")
        return
    restarts = cont.get("restart_count") or 0
    if restarts >= 3:
        finding(rec, "fleet.liveness.crash-loop", "critical",
                "%d restarts recorded; docker health is %s" % (restarts, cont.get("health")),
                source="docker:inspect",
                fix="zero retries: read the log first, restarting only extends the backoff")
    elif cont.get("health") == "unhealthy":
        finding(rec, "fleet.container.unhealthy", "warn",
                "docker reports the container unhealthy while it is running",
                source="docker:inspect")


def check_http(rec, record, opts):
    """Endpoint battery, and the distinction between the three endpoints."""
    if opts.skip_http or (record.get("container") or {}).get("state") != "running":
        return
    port = opts.container_port or _as_int(
        str((record.get("port") or {}).get("container_port") or "").split("/")[0]) \
        or DEFAULT_CONTAINER_PORT
    res = http_probes(record, port, opts.token_envs, timeout=max(30, opts.timeout))
    rec["probes"] = res["probes"]
    rec["metrics"]["probe_client"] = res["client"]
    rec["metrics"]["gateway_token_env"] = res["token_env"]
    if res["error"]:
        finding(rec, "fleet.probe.unreachable", "warn",
                "could not run the probe battery inside the container: %s" % res["error"],
                source="docker:exec")
        return
    if not res["client"]:
        finding(rec, "fleet.probe.no-http-client", "info",
                "no curl, node or wget inside the container — endpoint probes were skipped, "
                "so HEALTH rests on the CLI reads alone",
                source="docker:exec")
        return
    for key, fid, sev in (("healthz", "fleet.probe.healthz-fail", "critical"),
                          ("startupz", "fleet.probe.startupz-fail", "high")):
        probe = res["probes"].get(key)
        if probe and probe.get("status") != 200:
            finding(rec, fid, sev, "%s answered %s" % (probe["path"], probe.get("status")),
                    source="probe:%s" % probe["path"], evidence=probe.get("body"))
    ready = res["probes"].get("readyz_auth") or res["probes"].get("readyz")
    if ready is not None:
        rec["metrics"]["readyz_status"] = ready.get("status")
        rec["metrics"]["readyz_authenticated"] = ready.get("authenticated")
        if ready.get("status") != 200:
            detail = ready.get("body") or ""
            if not ready.get("authenticated"):
                finding(rec, "fleet.liveness.health-vs-ready", "warn",
                        "/readyz answered %s without a bearer token, so the response carries no "
                        "list of failing channels — this is an unreadable negative, not a verdict"
                        % ready.get("status"),
                        source="probe:/readyz",
                        fix="set --token-env to the variable holding the gateway token, or add it "
                            "to the container environment, then re-run")
            else:
                finding(rec, "fleet.probe.readyz-fail", "high",
                        "/readyz answered %s with a token: channels failed the deep check"
                        % ready.get("status"),
                        source="probe:/readyz", evidence=detail[:300])
    if not res["token_env"]:
        finding(rec, "fleet.probe.token-absent", "info",
                "no gateway bearer token found in the container environment under any known name; "
                "the authenticated /readyz probe was skipped",
                source="docker:exec")


def check_health_cli(rec, record, opts):
    """``health --json`` — and the queues that a green top-level ``ok`` hides."""
    if opts.skip_cli:
        return
    result, status = oc_read(record, ["health", "--json"], opts.timeout)
    rec["commands"]["health"] = status
    if status != "ok" or result is None or result.json is None:
        return
    doc = result.json
    top_ok = _dig(doc, "ok", "healthy")
    rec["metrics"]["health_ok"] = top_ok
    pressure = _dig(doc, "ingressPressure", "ingress_pressure")
    queues = _dig(doc, "deliveryQueues", "delivery_queues")
    depth = None
    if isinstance(queues, dict):
        depth = _dig(queues, "depth", "pending", "backlog", "queued")
    rec["metrics"]["ingress_pressure"] = pressure
    rec["metrics"]["queue_depth"] = depth
    dirty = False
    if isinstance(pressure, (int, float)) and not isinstance(pressure, bool):
        dirty = pressure > 0
    elif isinstance(pressure, str):
        dirty = pressure.lower() not in ("", "ok", "none", "low", "normal", "idle")
    elif isinstance(pressure, bool):
        dirty = pressure
    if isinstance(depth, (int, float)) and not isinstance(depth, bool) and depth > 0:
        dirty = True
    if dirty:
        finding(rec, "fleet.liveness.queue-backlog", "high",
                "delivery queues are not clear (ingressPressure=%r, depth=%r) while the top-level "
                "health verdict is %r — ok:true does not mean the queues drained"
                % (pressure, depth, top_ok),
                source="cli:health --json")
    elif top_ok is False:
        finding(rec, "fleet.health.not-ok", "high",
                "health --json reports ok:false", source="cli:health --json",
                evidence=json.dumps(redact.structure_only(doc))[:300])


def check_models(rec, record, opts):
    """``models status --check`` — exit code carries the answer, not the stdout."""
    if opts.skip_cli:
        return
    result, status = oc_read(record, ["models", "status", "--check", "--json"], opts.timeout)
    rec["commands"]["models_status"] = status
    if result is None:
        return
    label, explanation = ocjson.exit_meaning("models status --check", result.rc)
    rec["metrics"]["credentials"] = label
    if status == "unsupported":
        return
    if label == "expired":
        finding(rec, "fleet.auth.expired", "critical",
                "models status --check exited 1: %s" % explanation,
                source="cli:models status --check",
                fix="a repeat of an OAuth refresh burns the single-use token and logs out the "
                    "other consumer — read the profile expiry instead of retrying")
    elif label == "expiring":
        finding(rec, "fleet.auth.expiring", "high",
                "models status --check exited 2: %s" % explanation,
                source="cli:models status --check")
    elif label not in ("healthy", "ok"):
        finding(rec, "fleet.auth.check-inconclusive", "warn",
                "models status --check exited %d (%s)" % (result.rc, explanation),
                source="cli:models status --check")


def check_version(rec, record, opts):
    """Runtime version: what this instance actually runs, quoted from itself."""
    version = (record.get("capabilities") or {}).get("cli_version")
    if not version and not opts.skip_cli:
        result, status = oc_read(record, ["--version"], opts.timeout)
        rec["commands"]["version"] = status
        if result is not None and status == "ok":
            version = (result.stdout or "").strip().splitlines()[:1]
            version = version[0].strip() if version else None
    rec["metrics"]["version"] = version
    if not version:
        finding(rec, "fleet.version.unknown", "warn",
                "the runtime did not report a version; upgrade and drift checks cannot reason "
                "about this instance", source="cli:--version")


def check_plugins(rec, record, opts):
    if opts.skip_cli:
        return
    result, status = oc_read(record, ["plugins", "list", "--json"], opts.timeout)
    rec["commands"]["plugins_list"] = status
    if status != "ok" or result is None or result.json is None:
        return
    doc = result.json
    items = doc if isinstance(doc, list) else (_dig(doc, "plugins", "items", "entries") or [])
    count = len(items) if isinstance(items, list) else None
    rec["metrics"]["plugins"] = count
    if count == 0:
        finding(rec, "fleet.shared.plugins-none", "info",
                "no plugins are loaded", source="cli:plugins list --json")


def check_cron(rec, record, opts):
    """Timers: how many, how many enabled, and whether any timer has stalled."""
    if opts.skip_cli:
        return
    result, status = oc_read(record, ["cron", "list", "--json"], opts.timeout)
    rec["commands"]["cron_list"] = status
    if status != "ok" or result is None or result.json is None:
        return
    doc = result.json
    rows = doc if isinstance(doc, list) else (_dig(doc, "jobs", "crons", "items", "entries") or [])
    if not isinstance(rows, list):
        return
    rows = [r for r in rows if isinstance(r, dict)]
    enabled = [r for r in rows if _dig(r, "enabled", "isEnabled", depth=1) is not False]
    rec["metrics"]["cron_total"] = len(rows)
    rec["metrics"]["cron_enabled"] = len(enabled)
    groups, missing_agent, stalled = {}, [], []
    for row in rows:
        name = _dig(row, "name", "id", depth=1)
        schedule = _dig(row, "schedule", "cron", "expression", depth=1)
        groups.setdefault((str(name), str(schedule)), []).append(row)
        if not _dig(row, "agentId", "agent", depth=1):
            missing_agent.append(str(name))
        drift = _age_hours(_dig(row, "nextRun", "nextRunAt", "next", depth=2))
        if drift is not None and drift > opts.cron_drift_hours:
            stalled.append("%s (%.1fh past due)" % (name, drift))
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    rec["metrics"]["cron_duplicates"] = len(dupes)
    if dupes:
        finding(rec, "fleet.cron.duplicates-after-upgrade", "critical",
                "%d duplicated (name, schedule) group(s): %s — duplicates fire two or three times "
                "per tick and the copies lose their agent binding"
                % (len(dupes), ", ".join(sorted(n for n, _s in dupes)[:5])),
                source="cli:cron list --json",
                fix="in each group keep the entry that still carries a non-empty agent id")
    if missing_agent:
        finding(rec, "fleet.cron.orphaned-agent", "warn",
                "%d timer(s) carry no agent id: %s"
                % (len(missing_agent), ", ".join(sorted(missing_agent)[:5])),
                source="cli:cron list --json")
    if stalled:
        finding(rec, "fleet.cron.night-stall", "high",
                "%d timer(s) are past their next run: %s — a stalled timer keeps reporting active"
                % (len(stalled), "; ".join(stalled[:5])),
                source="cli:cron list --json")


def check_memory(rec, record, opts):
    """Memory subsystem: the embedding provider, index identity, and DB size.

    The embedding *probe* here is deliberately free. Issuing a real embedding
    request is a paid call down the agent path (class R1) and belongs to an
    explicit repair step, not to a monitoring battery that anyone may run on the
    whole fleet.
    """
    state_dir = (record.get("paths") or {}).get("state_dir")
    if state_dir and os.path.isdir(state_dir):
        total, biggest, biggest_name = 0, 0, None
        for root, _dirs, files in os.walk(state_dir):
            if root.count(os.sep) - state_dir.count(os.sep) > 3:
                continue
            for name in files:
                if not re.search(r"\.(db|sqlite3?|db-wal)$", name):
                    continue
                try:
                    size = os.path.getsize(os.path.join(root, name))
                except OSError:
                    continue
                total += size
                if size > biggest:
                    biggest, biggest_name = size, name
        rec["metrics"]["memory_db_bytes"] = total or None
        rec["metrics"]["memory_db_largest"] = biggest_name
        if total and total > opts.memory_db_warn_mb * 1024 * 1024:
            finding(rec, "fleet.memory.db-growth", "warn",
                    "memory database is %.0f MB (largest file %s); the memory tables have no "
                    "retention or LRU upstream, so this only grows"
                    % (total / 1048576.0, biggest_name),
                    source="host:state-dir")
    if opts.skip_cli:
        return
    result, status = oc_read(record, ["memory", "status", "--json"], opts.timeout)
    rec["commands"]["memory_status"] = status
    if status != "ok" or result is None or result.json is None:
        if status == "unsupported":
            rec["metrics"]["embeddings"] = "unsupported"
        return
    doc = result.json
    provider = _dig(doc, "provider", "embeddingProvider")
    model = _dig(doc, "model", "embeddingModel")
    error = _dig(doc, "error", "lastError", "failure")
    paused = _dig(doc, "paused", "indexIdentityMismatch", "identityMismatch")
    last_indexed = _dig(doc, "lastIndexedAt", "lastIndexed", "indexedAt", "updatedAt")
    rec["metrics"]["embedding_provider"] = provider if isinstance(provider, str) else None
    rec["metrics"]["embedding_model"] = model if isinstance(model, str) else None
    indexed_age = _age_hours_signed(last_indexed)
    if indexed_age is not None and indexed_age < -0.5:
        rec["metrics"]["last_indexed_hours"] = None
        finding(rec, "fleet.memory.index-clock-skew", "warn",
                "the last index timestamp is %.1fh in the future — a clock skew this size makes "
                "every age in this report unreliable" % abs(indexed_age),
                source="cli:memory status --json")
    else:
        rec["metrics"]["last_indexed_hours"] = (
            None if indexed_age is None else max(0.0, indexed_age))
    if error:
        text = redact.scrub(str(error))[:300]
        rec["metrics"]["embeddings"] = "error"
        finding(rec, "fleet.memory.embeddings-unauthorized", "critical",
                "the embedding provider is failing: %s" % text,
                source="cli:memory status --json",
                fix="an invalid-JWT style rejection means a token was presented where an API key "
                    "was expected — an OAuth session does not satisfy embedding requests")
    elif paused:
        rec["metrics"]["embeddings"] = "paused"
        finding(rec, "fleet.memory.index-identity-changed", "high",
                "vector search is paused on an index-identity mismatch: the provider, model or "
                "chunking changed, and reindexing is explicit — it never happens by itself",
                source="cli:memory status --json")
    else:
        rec["metrics"]["embeddings"] = "ok"
    age = rec["metrics"]["last_indexed_hours"]
    if age is not None and age > 24 * 30:
        finding(rec, "fleet.memory.stale-index", "warn",
                "the index has not been written for %.0f days" % (age / 24.0),
                source="cli:memory status --json")


def check_lint(rec, record, opts):
    """``doctor --lint --json`` — the only findings that arrive with a sanctioned fix."""
    if not opts.lint or opts.skip_cli:
        return
    result, status = oc_read(record, ["doctor", "--lint", "--json"], opts.timeout)
    rec["commands"]["doctor_lint"] = status
    if result is None or status in ("unsupported", "failed"):
        return
    label, explanation = ocjson.exit_meaning("doctor --lint", result.rc)
    rec["metrics"]["lint"] = label
    for item in result.findings():
        # Upstream ids pass through VERBATIM — that is the catalog rule, and it is what
        # lets /repair resolve one of the documented pass-through families. A local
        # prefix here would invent an id that no catalog row can ever cover.
        check_id = item.get("checkId") or "fleet.lint.unclassified"
        severity = upstream_severity(item.get("severity", "warn"),
                                     "doctor --lint finding %r" % check_id)
        finding(rec, check_id, severity,
                redact.scrub(str(item.get("message") or explanation))[:300],
                source="cli:doctor --lint --json",
                fix=redact.scrub(str(item.get("fixHint"))) if item.get("fixHint") else None,
                evidence=item.get("ocPath") or item.get("path"))


def check_liveness_log(rec, record, opts):
    """When did the gateway last write a log line?

    Read here rather than taken from the discovery sweep, and parsed as UTC. This
    single number is the primary evidence behind LIVENESS, and a docker timestamp
    parsed as local time shifts every age by the host's UTC offset — in the
    direction that makes a stalled instance look fresh on a host west of UTC,
    which is exactly the failure the zombie detector exists to catch.
    """
    cid = (record.get("container") or {}).get("id")
    age, source = None, None
    if cid:
        rc, out, err = discovery.run(
            ["docker", "logs", "--tail", "1", "--timestamps", cid], timeout=min(20, opts.timeout))
        if rc == 0:
            lines = ((out or "") + (err or "")).strip().splitlines()
            if lines:
                age = _age_hours(lines[-1].split(" ", 1)[0])
                source = "docker logs --timestamps"
    if age is None:
        age = (record.get("signals") or {}).get("log_age_hours")
        source = "discovery sweep" if age is not None else None
    rec["metrics"]["log_age_hours"] = age
    rec["metrics"]["log_age_source"] = source
    if age is None and (record.get("container") or {}).get("state") == "running":
        finding(rec, "fleet.liveness.log-unreadable", "warn",
                "the gateway log carries no readable timestamp, so LIVENESS rests on the index "
                "write time alone", source="host:docker logs")


def check_config_file(rec, record):
    signals = record.get("signals") or {}
    rec["metrics"]["config_bytes"] = signals.get("config_bytes")
    rec["metrics"]["config_age_hours"] = (
        _age_hours(signals.get("config_mtime")) if signals.get("config_mtime") else None)
    if signals.get("config_present") is False:
        finding(rec, "fleet.config.empty", "critical",
                "no openclaw.json at the mounted state directory",
                source="host:state-dir")
    elif signals.get("config_bytes") is not None and signals["config_bytes"] < 8:
        finding(rec, "fleet.config.empty", "critical",
                "openclaw.json is %d bytes — effectively empty" % signals["config_bytes"],
                source="host:state-dir")


# --------------------------------------------------------------------------- #
# verdicts
# --------------------------------------------------------------------------- #

def verdict_health(rec, record):
    """What the instance says about itself."""
    if record.get("state") == "down":
        return "down"
    if record.get("profile") == "alien":
        return "unknown"
    severity = worst([f for f in rec["findings"]
                      if not f["id"].startswith("fleet.liveness.")])
    if severity in BLOCKING:
        return "degraded"
    probes = rec.get("probes") or {}
    if probes:
        healthz = (probes.get("healthz") or {}).get("status")
        if healthz != 200:
            return "degraded"
        ready = probes.get("readyz_auth")
        if ready and ready.get("status") != 200:
            return "degraded"
    if severity == "warn":
        return "degraded"
    if not probes and not rec.get("commands"):
        return "unknown"
    return "ok"


def verdict_liveness(rec, record, opts):
    """What an outside observer sees the instance DO.

    Computed only from evidence the gateway does not produce about itself: log
    movement, timer firing, index writes. Keeping the evidence disjoint is what
    makes a disagreement with HEALTH meaningful.
    """
    log_age = rec["metrics"].get("log_age_hours")
    index_age = rec["metrics"].get("last_indexed_hours")
    # The log is the primary witness. The index write time only stands in when the
    # log is unreadable: taking whichever signal is freshest lets one moving
    # subsystem vouch for a gateway that stopped serving weeks ago.
    primary = log_age if log_age is not None else index_age
    rec["metrics"]["liveness_evidence"] = ("log" if log_age is not None
                                           else "index" if index_age is not None else None)
    if primary is None:
        return "unknown"
    if (log_age is not None and index_age is not None
            and log_age > opts.stale_hours and index_age < opts.idle_hours):
        finding(rec, "fleet.liveness.evidence-conflict", "warn",
                "the log has not moved for %.1fh while the index was written %.1fh ago — two "
                "observers disagree about whether this instance is working"
                % (log_age, index_age), source="host:docker logs")
    if primary > opts.stale_hours:
        return "stale"
    if primary > opts.idle_hours:
        return "idle"
    return "active"


def apply_divergence(rec, record, opts):
    """The whole reason the two columns exist.

    The zombie test is not "HEALTH says ok" — an unrelated warning would then hide
    it. It is the narrower and more damning statement: the container is running,
    it still ANSWERS, and nothing it does has moved in days.
    """
    health, live = rec["health"], rec["liveness"]
    running = (record.get("container") or {}).get("state") == "running"
    probes = rec.get("probes") or {}
    answers = ((probes.get("healthz") or {}).get("status") == 200
               or any(v == "ok" for v in (rec.get("commands") or {}).values()))
    rec["divergence"] = False
    if running and answers and live == "stale":
        rec["divergence"] = True
        finding(rec, "fleet.liveness.zombie", "critical",
                "it still answers while nothing has moved for %.1fh: the process that replies to "
                "the probes is the one that stopped working, so no self-report can catch this"
                % (rec["metrics"].get("log_age_hours") or opts.stale_hours),
                source="host:docker logs",
                fix="triage before any upgrade or restart — a restart destroys the evidence")
    elif health == "down" and live in ("active", "idle"):
        rec["divergence"] = True
        finding(rec, "fleet.liveness.orphan-activity", "warn",
                "the gateway is down yet its log moved recently — something else is still writing "
                "under this instance", source="host:docker logs")
    elif health == "ok" and live == "idle":
        finding(rec, "fleet.liveness.quiet", "info",
                "healthy but idle for %.1fh — expected on an instance with no timers"
                % (rec["metrics"].get("log_age_hours") or 0.0),
                source="host:docker logs")


# --------------------------------------------------------------------------- #
# per-instance run
# --------------------------------------------------------------------------- #

def run_instance(record, opts):
    rec = {
        "name": record.get("name"),
        "project": record.get("project"),
        "state": record.get("state"),
        "state_before": record.get("state"),
        "profile": record.get("profile"),
        "role": record.get("role"),
        "criticality": record.get("criticality"),
        "managed": record.get("managed"),
        "ok": record.get("ok", True),
        "error": record.get("error"),
        "health": "unknown",
        "liveness": "unknown",
        "divergence": False,
        "probes": {},
        "commands": {},
        "metrics": {},
        "findings": [],
    }
    if record.get("profile") == "alien" or not record.get("managed", True):
        rec["health"] = "unknown"
        rec["liveness"] = "unknown"
        if record.get("profile") == "alien":
            finding(rec, "fleet.inventory.alien", "info",
                    "inventory only: this object matched the project prefix but failed the "
                    "layout marker set, so no command was run against it", source="config")
        else:
            finding(rec, "fleet.inventory.unmanaged", "info",
                    "inventory only: this instance is marked unmanaged in the fleet config, "
                    "so no command was run against it", source="config")
        return rec
    if not record.get("ok", True):
        finding(rec, "fleet.inventory.discovery-failed", "high",
                "discovery could not describe this instance: %s" % record.get("error"),
                source="docker")
    check_container(rec, record)
    check_liveness_log(rec, record, opts)
    check_config_file(rec, record)
    check_version(rec, record, opts)
    if (record.get("container") or {}).get("state") == "running":
        check_http(rec, record, opts)
        check_health_cli(rec, record, opts)
        check_models(rec, record, opts)
        check_plugins(rec, record, opts)
        check_cron(rec, record, opts)
        check_lint(rec, record, opts)
    check_memory(rec, record, opts)
    rec["health"] = verdict_health(rec, record)
    rec["liveness"] = verdict_liveness(rec, record, opts)
    apply_divergence(rec, record, opts)
    # Downgrade only. A battery may prove a subsystem dead; it may never declare
    # an instance healthier than discovery already found it.
    if rec["state"] == "ok" and worst(rec["findings"]) in BLOCKING:
        rec["state"] = "degraded"
    rec["worst_severity"] = worst(rec["findings"])
    return rec


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

_COLUMNS = [
    ("NAME", lambda r: r["name"]),
    ("STATE", lambda r: r["state"] or "?"),
    ("HEALTH", lambda r: r["health"]),
    ("LIVENESS", lambda r: r["liveness"] + ("  <-- diverges" if r["divergence"] else "")),
    ("VERSION", lambda r: r["metrics"].get("version") or "-"),
    ("CREDS", lambda r: r["metrics"].get("credentials") or "-"),
    ("PLUGINS", lambda r: _num(r["metrics"].get("plugins"))),
    ("CRON", lambda r: _cron(r)),
    ("MEM-DB", lambda r: _mb(r["metrics"].get("memory_db_bytes"))),
    ("LOG-AGE", lambda r: _hours(r["metrics"].get("log_age_hours"))),
    ("FINDINGS", lambda r: _findings(r)),
]


def _num(value):
    return "-" if value is None else str(value)


def _mb(value):
    return "-" if not value else "%.0fMB" % (value / 1048576.0)


def _hours(value):
    return "-" if value is None else "%.1fh" % value


def _cron(rec):
    total = rec["metrics"].get("cron_total")
    if total is None:
        return "-"
    enabled = rec["metrics"].get("cron_enabled")
    dupes = rec["metrics"].get("cron_duplicates") or 0
    return "%s/%s%s" % (enabled, total, " dup:%d" % dupes if dupes else "")


def _findings(rec):
    counts = {}
    for item in rec["findings"]:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    if not counts:
        return "-"
    return " ".join("%s:%d" % (s, counts[s]) for s in SEVERITIES if s in counts)


def render_table(results):
    heads = [h for h, _fn in _COLUMNS]
    rows = [[str(fn(r)) for _h, fn in _COLUMNS] for r in results]
    widths = [max([len(heads[i])] + [len(row[i]) for row in rows]) for i in range(len(heads))]
    out = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(heads)).rstrip(),
           "  ".join("-" * widths[i] for i in range(len(heads)))]
    for row in rows:
        out.append("  ".join(row[i].ljust(widths[i]) for i in range(len(heads))).rstrip())
    lines = ["\n".join(out), ""]
    for rec in results:
        for item in rec["findings"]:
            if item["severity"] == "info":
                continue
            lines.append("%-8s %-46s %s" % (item["severity"].upper(), item["finding_id"],
                                            item["message"]))
    return "\n".join(lines).rstrip()


def emit(text, as_json=False, payload=None):
    body = json.dumps(payload, indent=2, ensure_ascii=False) if as_json else text
    result = redact.scrub_stream(body)
    sys.stdout.write(result.text.rstrip("\n") + "\n")
    if result.count and not as_json:
        sys.stderr.write(result.marker() + "\n")


def snapshot_dir(cfg, override=None):
    if override:
        return os.path.abspath(os.path.expanduser(override))
    configured = cfg.policy("snapshot_dir") if cfg.present else None
    base = configured or os.path.join(
        os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
        "openclaw-ops")
    return os.path.join(os.path.abspath(os.path.expanduser(base)), "health")


def write_snapshot(payload, directory, keep=30):
    """Persist one run so the next report can compute a delta.

    Mode 0600: a run carries instance names, ports and paths — deployment
    topology, which is exactly what this plugin refuses to publish.
    """
    os.makedirs(directory, mode=0o700, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(directory, "health-%s.json" % stamp)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    try:
        names = sorted(n for n in os.listdir(directory)
                       if n.startswith("health-") and n.endswith(".json"))
        for old in names[:-keep] if keep and len(names) > keep else []:
            os.unlink(os.path.join(directory, old))
    except OSError:
        pass
    return path


# --------------------------------------------------------------------------- #

def build_parser():
    ap = argparse.ArgumentParser(
        prog="healthcheck.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("selector", nargs="?", default="",
                    help="fleet selector (default: every managed instance)")
    ap.add_argument("--config", help="explicit fleet config path (bypasses the ladder)")
    ap.add_argument("--prefix", help="compose project prefix (default: from config)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--snapshot", action="store_true",
                    help="write this run to the state directory so the next report has a baseline")
    ap.add_argument("--state-dir", help="override the snapshot directory")
    ap.add_argument("--keep", type=int, default=30, help="snapshots to retain (default 30)")
    ap.add_argument("--jobs", type=int, default=4, help="instances probed in parallel")
    ap.add_argument("--timeout", type=int, default=45, help="per-command timeout in seconds")
    ap.add_argument("--container-port", type=int, default=None,
                    help="gateway port inside the container (default: detected, else %d)"
                         % DEFAULT_CONTAINER_PORT)
    ap.add_argument("--token-env", action="append",
                    help="environment name holding the gateway bearer token inside the container; "
                         "repeatable. Only the NAME is used here — the value never leaves the "
                         "container")
    ap.add_argument("--idle-hours", type=float, default=6.0,
                    help="log silence after which LIVENESS is idle (default 6)")
    ap.add_argument("--stale-hours", type=float, default=None,
                    help="log silence after which LIVENESS is stale (default: fleet config)")
    ap.add_argument("--cron-drift-hours", type=float, default=1.0,
                    help="how far past its next run a timer may be before it counts as stalled")
    ap.add_argument("--memory-db-warn-mb", type=float, default=200.0)
    ap.add_argument("--skip-http", action="store_true", help="skip the endpoint probes")
    ap.add_argument("--skip-cli", action="store_true", help="skip every in-container CLI read")
    ap.add_argument("--lint", action="store_true",
                    help="also run doctor --lint --json (adds findings that carry a checkId and a "
                         "fixHint from the runtime itself)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = cfgmod.load_config(args.config)
    for line in cfg.warnings:
        sys.stderr.write("warning: %s\n" % line)
    if cfg.readonly:
        sys.stderr.write("READ-ONLY: %s\n" % cfg.readonly_reason)
    if args.stale_hours is None:
        args.stale_hours = float(cfg.policy("stale_log_hours", 24.0)) if cfg.present else 24.0
    opts = Options(args)

    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=True)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    try:
        picked = fleet.resolve(records, args.selector, cfg, mutation=False)
    except fleet.SelectorError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_REFUSED
    if not picked:
        sys.stderr.write("error: selector %r matched no instance\n" % (args.selector or "managed"))
        return EXIT_EMPTY

    results = []
    if args.jobs > 1 and len(picked) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda r: run_instance(r, opts), picked))
    else:
        results = [run_instance(r, opts) for r in picked]
    results.sort(key=lambda r: r["name"])

    all_findings = [f for r in results for f in r["findings"]]
    payload = {
        "schema": SCHEMA,
        "generated_at": _now(),
        "selector": args.selector or "managed",
        "host": {"label": cfg.data.get("host_label") if cfg.present else None,
                 "fingerprint": cfgmod.host_fingerprint()},
        "thresholds": {"idle_hours": opts.idle_hours, "stale_hours": opts.stale_hours,
                       "cron_drift_hours": opts.cron_drift_hours,
                       "memory_db_warn_mb": opts.memory_db_warn_mb},
        "counts": {
            "instances": len(results),
            "diverging": sum(1 for r in results if r["divergence"]),
            "critical": sum(1 for f in all_findings if f["severity"] == "critical"),
            "high": sum(1 for f in all_findings if f["severity"] == "high"),
            "warn": sum(1 for f in all_findings if f["severity"] == "warn"),
            "info": sum(1 for f in all_findings if f["severity"] == "info"),
        },
        "instances": results,
    }

    if args.snapshot:
        try:
            path = write_snapshot(payload, snapshot_dir(cfg, args.state_dir), keep=args.keep)
            payload["snapshot"] = path
            sys.stderr.write("snapshot: %s\n" % path)
        except OSError as exc:
            sys.stderr.write("warning: could not write snapshot: %s\n" % exc)

    if args.json:
        emit(None, True, payload)
    else:
        emit(render_table(results))

    if any(payload["counts"][name] for name in BLOCKING):
        return EXIT_BLOCKING_FINDINGS
    if payload["counts"]["warn"]:
        return EXIT_WARN_FINDINGS
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
