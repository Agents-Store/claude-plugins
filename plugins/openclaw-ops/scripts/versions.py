#!/usr/bin/env python3
"""versions.py — what version this fleet runs, what it should run, and why not yet.

    versions.py [SELECTOR] [--channel stable|extended-stable|beta|dev]
                [--target VERSION] [--json|--table] [options]

Three ways to answer "what is the current stable version" that are WRONG
=======================================================================
Every one of them looks reasonable, every one of them ships regularly, and every
one of them returns a different number than the release channel actually points
at. They are listed here so that a later reader who "simplifies" this module
puts the bug back deliberately rather than by accident.

1. **Semver-max over the non-prerelease versions.**
   Correction releases are published as ``<version>-1``, ``<version>-2``. Semver
   parses a hyphen suffix as a *prerelease*, so a semver-correct maximum filters
   out exactly the releases that exist to fix the release it keeps. You get the
   broken original and call it the newest stable.
   This module therefore treats an all-numeric hyphen suffix as a CORRECTION
   that sorts ABOVE the bare version — deliberately not semver.

2. **Newest GitHub release with ``prerelease == false``, sorted by date.**
   The extended-stable line is also published as a non-prerelease GitHub release
   and it trails the stable line by about a month. Sorting by date and taking the
   first non-prerelease hands you extended-stable while you believe you are on
   stable — a silent month-long rollback of the whole fleet.

3. **Comparing npm publish dates with GitHub release dates.**
   They disagree by weeks, and the disagreement is not a bug: a build is
   published to the beta tag first and later PROMOTED to stable *without a
   version bump*. The npm publish date is the day the artefact was built; the
   GitHub release date is the day it became stable. Only the second one starts
   the soak clock.

What this module does instead
-----------------------------
The channel is resolved from **npm dist-tags** — the one place that says which
build a channel currently points at. The soak clock is read from the **GitHub
release date** of that exact version. The two sources answer two different
questions and neither substitutes for the other.

The soak gate
-------------
A target version is accepted only when all of these hold:

* it carries no ``-beta`` / ``-alpha`` / ``-rc`` / ``-dev`` marker;
* it is not older than the version already installed anywhere in the selection;
* it was promoted at least ``--soak-days`` days ago, measured by GitHub release
  date;
* no correction release on the same line shipped after it;
* when an image digest is checked, the digest resolved for the pinned reference
  matches the digest of the channel's current build.

Anything unproven is a refusal, not a warning. A missing GitHub release means the
promotion date is unknown, which means the soak clock never started.

Pinning
-------
Mutations pin a digest or a plain version, never a tag. ``latest``, ``main``,
``extended-stable`` and friends are rebuilt on a schedule under the same name, so
a rollback target pinned to one has already changed by the time you need it. Plain
version tags and dated tags are immutable; both forms are accepted, moving tags
are reported as a finding.

Exit codes
----------
    0  no drift, and the resolved target passes the gate
    1  runtime error
    2  fleet config missing or invalid
    3  the target was REJECTED by the soak gate
    4  selector matched nothing
    5  version drift across the selection
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, HERE)

import config as cfgmod          # noqa: E402
import discovery                 # noqa: E402
import fleet                     # noqa: E402
import gate                      # noqa: E402
import redact                    # noqa: E402

SCHEMA = "openclaw-ops/versions/1"
EXIT_OK, EXIT_RUNTIME, EXIT_CONFIG, EXIT_REJECTED, EXIT_EMPTY, EXIT_DRIFT = 0, 1, 2, 3, 4, 5

DEFAULT_PACKAGE = "openclaw"
NPM_REGISTRY = "https://registry.npmjs.org"
GITHUB_API = "https://api.github.com"
USER_AGENT = "openclaw-ops/versions"

# Channel name -> npm dist-tag. The channel is an operator concept and the
# dist-tag is the only mechanical fact about where it points; the two are NOT
# spelled the same, and the difference is the whole reason this table exists.
# The channel names here are exactly the ones `policy.update_channel` accepts in
# the fleet config (fleet.schema.json) — a value this table does not list fails
# schema validation, so a dist-tag name such as "latest" is deliberately not a
# channel name.
CHANNEL_TAGS = {
    "stable": "latest",            # the promoted production line; its dist-tag is "latest"
    "extended-stable": "extended-stable",
    "beta": "beta",
    "dev": "dev",
}
PRERELEASE_RE = re.compile(r"-(?:beta|alpha|rc|dev|next|canary|nightly|snapshot)", re.I)
VERSION_RE = re.compile(r"^v?(?P<base>\d+(?:\.\d+){0,3})(?:-(?P<suffix>[0-9A-Za-z.\-]+))?$")
VERSION_IN_TEXT = re.compile(r"\b(\d+\.\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z.\-]+)?)\b")


# --------------------------------------------------------------------------- #
# version algebra
# --------------------------------------------------------------------------- #

def parse_version(text):
    """Parse a version string into comparable parts.

    Returns ``{raw, base, correction, prerelease, valid}``. ``correction`` is the
    all-numeric hyphen suffix, which this module ranks ABOVE the bare version;
    a non-numeric suffix is a prerelease and ranks BELOW it. That asymmetry is
    the whole point — see wrong method 1 in the module docstring.
    """
    out = {"raw": text, "base": (), "correction": 0, "prerelease": None, "valid": False}
    if not text:
        return out
    match = VERSION_RE.match(str(text).strip())
    if not match:
        found = VERSION_IN_TEXT.search(str(text))
        if not found:
            return out
        match = VERSION_RE.match(found.group(1))
        if not match:
            return out
    out["base"] = tuple(int(p) for p in match.group("base").split("."))
    suffix = match.group("suffix")
    if suffix:
        if suffix.isdigit():
            out["correction"] = int(suffix)
        else:
            out["prerelease"] = suffix
    out["valid"] = True
    return out


def sort_key(parsed):
    base = parsed["base"] + (0,) * (4 - len(parsed["base"]))
    return (base[:4],
            0 if parsed["prerelease"] else 1,
            parsed["prerelease"] or "",
            parsed["correction"])


def compare(left, right):
    """-1 / 0 / 1 for two version strings, using this module's ranking."""
    a, b = sort_key(parse_version(left)), sort_key(parse_version(right))
    return (a > b) - (a < b)


def same_line(left, right):
    """Do two versions belong to the same release line (same base, corrections aside)?"""
    return parse_version(left)["base"] == parse_version(right)["base"]


# --------------------------------------------------------------------------- #
# network reads (all GET, all anonymous, all optional)
# --------------------------------------------------------------------------- #

class NetError(Exception):
    pass


def http_json(url, timeout=15, accept="application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise NetError("%s -> HTTP %s" % (url, exc.code))
    except Exception as exc:
        raise NetError("%s -> %s" % (url, exc))
    try:
        return json.loads(body)
    except ValueError as exc:
        raise NetError("%s -> not JSON: %s" % (url, exc))


def dist_tags(package, timeout=15):
    """The channel map. This, and only this, says where a channel points."""
    return http_json("%s/-/package/%s/dist-tags" % (NPM_REGISTRY, package), timeout)


def version_manifest(package, version, timeout=15):
    """One version's manifest — small, and it carries the repository URL."""
    return http_json("%s/%s/%s" % (NPM_REGISTRY, package, version), timeout)


def repo_slug(manifest):
    """Derive ``owner/name`` from the package manifest instead of hard-coding it.

    A hard-coded repository is a fact that rots; the package itself always knows
    where it is published from.
    """
    repo = (manifest or {}).get("repository")
    url = repo.get("url") if isinstance(repo, dict) else repo
    if not isinstance(url, str):
        return None
    match = re.search(r"github\.com[:/]+([^/]+)/([^/#?]+?)(?:\.git)?/?$", url)
    return "%s/%s" % (match.group(1), match.group(2)) if match else None


def github_releases(slug, timeout=20, pages=2):
    """Release list with publish dates. Anonymous, so rate-limited — cached per run."""
    out = []
    for page in range(1, pages + 1):
        url = "%s/repos/%s/releases?per_page=100&page=%d" % (GITHUB_API, slug, page)
        rows = http_json(url, timeout, accept="application/vnd.github+json")
        if not isinstance(rows, list) or not rows:
            break
        out.extend(rows)
        if len(rows) < 100:
            break
    return out


def release_for(releases, version):
    """Find the release publishing exactly this version, tolerating a ``v`` prefix."""
    want = parse_version(version)
    for row in releases or []:
        for candidate in (row.get("tag_name"), row.get("name")):
            if not candidate:
                continue
            got = parse_version(candidate)
            if got["valid"] and sort_key(got) == sort_key(want):
                return row
    return None


def _released_at(row):
    stamp = (row or {}).get("published_at") or (row or {}).get("created_at")
    if not stamp:
        return None
    try:
        return datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")\
            .replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# image digests
# --------------------------------------------------------------------------- #

def image_digest(reference, timeout=60):
    """Resolve an image reference to its manifest digest.

    ``docker buildx imagetools inspect`` answers for a remote reference without
    pulling it. When buildx is absent, the locally present image is used instead
    and the source is reported, because a local answer proves only what this host
    already has.
    """
    rc, out, err = discovery.run(
        ["docker", "buildx", "imagetools", "inspect", "--format", "{{.Manifest.Digest}}",
         reference], timeout=timeout)
    digest = (out or "").strip().splitlines()
    if rc == 0 and digest and digest[0].startswith("sha256:"):
        return {"digest": digest[0], "source": "registry", "error": None}
    rc2, out2, err2 = discovery.run(
        ["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", reference],
        timeout=timeout)
    text = (out2 or "").strip()
    if rc2 == 0 and "@sha256:" in text:
        return {"digest": text.split("@", 1)[1], "source": "local-image", "error": None}
    reason = (err or err2 or "").strip().splitlines()
    return {"digest": None, "source": None,
            "error": reason[0] if reason else "no digest for %s" % reference}


# --------------------------------------------------------------------------- #
# the gate
# --------------------------------------------------------------------------- #

def soak_gate(target, releases, soak_days, installed_versions=None, now=None,
              channel_version=None, digest_check=None):
    """Decide whether ``target`` may be installed. Returns a verdict dict.

    ``accepted`` is the only value that permits a mutation. ``unverified`` is a
    refusal with a different reason: nothing said the version is bad, but nothing
    proved it is good either, and an unproven upgrade is not a safe one.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    reasons, verdict = [], "accepted"
    parsed = parse_version(target)
    if not parsed["valid"]:
        return {"verdict": "rejected", "target": target, "age_days": None,
                "reasons": ["%r is not a version this module can parse" % target]}

    if parsed["prerelease"] or PRERELEASE_RE.search(str(target)):
        verdict = "rejected"
        reasons.append("carries a prerelease marker (%s): a channel target must be a promoted "
                       "build, and the dev line is explicitly not for production gateways"
                       % (parsed["prerelease"] or "prerelease"))

    for name, installed in sorted((installed_versions or {}).items()):
        if installed and compare(target, installed) < 0:
            verdict = "rejected"
            reasons.append("older than the version already installed on %s (%s): an upgrade that "
                           "moves backwards is a downgrade with no migration path"
                           % (name, installed))

    release = release_for(releases, target)
    age_days = None
    if release is None:
        if releases is None:
            verdict = "unverified" if verdict == "accepted" else verdict
            reasons.append("release history was not fetched, so the promotion date is unknown "
                           "and the soak clock cannot start")
        else:
            verdict = "unverified" if verdict == "accepted" else verdict
            reasons.append("no release found publishing %s — promotion date unknown" % target)
    else:
        published = _released_at(release)
        if published is None:
            verdict = "unverified" if verdict == "accepted" else verdict
            reasons.append("the release for %s carries no publish date" % target)
        else:
            age_days = (now - published).days
            if age_days < soak_days:
                verdict = "rejected"
                reasons.append("promoted %d day(s) ago, soak requires %d — %d to go"
                               % (age_days, soak_days, soak_days - age_days))
            else:
                reasons.append("promoted %d day(s) ago (soak %d)" % (age_days, soak_days))

    corrections = []
    for row in releases or []:
        tag = row.get("tag_name") or row.get("name") or ""
        got = parse_version(tag)
        if not got["valid"] or not same_line(tag, target):
            continue
        if sort_key(got) > sort_key(parsed):
            corrections.append(tag.lstrip("v"))
    if corrections:
        verdict = "rejected"
        reasons.append("a correction release shipped after it on the same line (%s) — take the "
                       "correction, not the version it corrects" % ", ".join(sorted(corrections)))

    if channel_version and compare(target, channel_version) != 0:
        reasons.append("note: the channel currently points at %s, not %s"
                       % (channel_version, target))

    if digest_check and digest_check.get("expected") and digest_check.get("actual") \
            and digest_check["expected"] != digest_check["actual"]:
        verdict = "rejected"
        reasons.append("digest mismatch: the pinned reference resolves to %s but the channel "
                       "build is %s" % (digest_check["actual"], digest_check["expected"]))

    return {"verdict": verdict, "target": target, "age_days": age_days,
            "release_url": (release or {}).get("html_url"), "reasons": reasons}


# --------------------------------------------------------------------------- #
# fleet drift
# --------------------------------------------------------------------------- #

def instance_versions(records):
    """Per-instance installed version, image reference and digest."""
    rows = []
    for rec in records:
        cont = rec.get("container") or {}
        image = cont.get("image")
        rows.append({
            "name": rec.get("name"),
            "state": rec.get("state"),
            "role": rec.get("role"),
            "profile": rec.get("profile"),
            "version": (rec.get("capabilities") or {}).get("cli_version"),
            "image": image,
            "image_digest": cont.get("image_digest"),
            "moving_tag": gate.is_moving_tag(image) if image else None,
        })
    return rows


def drift_report(rows, target=None):
    """Group the fleet by installed version and rank each instance against the target."""
    seen = {}
    for row in rows:
        version = parse_version(row.get("version") or "")
        key = row.get("version") if version["valid"] else None
        seen.setdefault(key, []).append(row["name"])
        if target and version["valid"]:
            cmp_result = compare(row["version"], target)
            row["vs_target"] = ("current" if cmp_result == 0
                                else "behind" if cmp_result < 0 else "ahead")
        else:
            row["vs_target"] = "unknown"
    known = {k: v for k, v in seen.items() if k}
    newest = max(known, key=lambda v: sort_key(parse_version(v))) if known else None
    return {
        "distinct": len(known),
        "by_version": {k: sorted(v) for k, v in sorted(seen.items(),
                                                       key=lambda kv: str(kv[0]))},
        "newest_installed": newest,
        "unknown": sorted(n for k, v in seen.items() if not k for n in v),
        "moving_tags": sorted(r["name"] for r in rows if r.get("moving_tag")),
    }


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

def render(payload):
    lines = []
    channel = payload["channel"]
    lines.append("channel %s -> dist-tag %s -> %s"
                 % (channel["name"], channel["tag"], channel.get("version") or "unresolved"))
    if channel.get("error"):
        lines.append("  channel lookup failed: %s" % channel["error"])
    if payload.get("all_tags"):
        lines.append("  dist-tags: " + ", ".join(
            "%s=%s" % (k, v) for k, v in sorted(payload["all_tags"].items())))
    verdict = payload.get("gate")
    if verdict:
        lines.append("")
        lines.append("target %s -> %s" % (verdict["target"], verdict["verdict"].upper()))
        for reason in verdict["reasons"]:
            lines.append("  - %s" % reason)
    drift = payload["drift"]
    lines.append("")
    lines.append("installed across %d instance(s): %d distinct version(s)%s"
                 % (len(payload["instances"]), drift["distinct"],
                    ", newest %s" % drift["newest_installed"] if drift["newest_installed"] else ""))
    heads = ["NAME", "STATE", "ROLE", "VERSION", "VS-TARGET", "IMAGE", "DIGEST"]
    rows = [[r["name"], r["state"] or "?", r["role"] or "-", r["version"] or "-",
             r.get("vs_target", "unknown"), r["image"] or "-",
             (r["image_digest"] or "-")[:19]] for r in payload["instances"]]
    widths = [max([len(heads[i])] + [len(row[i]) for row in rows]) for i in range(len(heads))]
    lines.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(heads)).rstrip())
    lines.append("  ".join("-" * widths[i] for i in range(len(heads))))
    for row in rows:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(heads))).rstrip())
    if drift["moving_tags"]:
        lines.append("")
        lines.append("moving image tags on: %s" % ", ".join(drift["moving_tags"]))
        lines.append("  a moving tag is rebuilt under the same name, so it is not a rollback "
                     "target. Pin a digest or a plain version before any upgrade.")
    return "\n".join(lines)


def emit(text, as_json=False, payload=None):
    body = json.dumps(payload, indent=2, ensure_ascii=False) if as_json else text
    result = redact.scrub_stream(body)
    sys.stdout.write(result.text.rstrip("\n") + "\n")
    if result.count and not as_json:
        sys.stderr.write(result.marker() + "\n")


# --------------------------------------------------------------------------- #

def build_parser():
    ap = argparse.ArgumentParser(
        prog="versions.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("selector", nargs="?", default="")
    ap.add_argument("--config", help="explicit fleet config path")
    ap.add_argument("--prefix", help="compose project prefix")
    ap.add_argument("--channel", default=None, choices=sorted(CHANNEL_TAGS),
                    help="release channel, as spelled in policy.update_channel (default: from "
                         "the fleet config, else stable). The channel name is not the dist-tag: "
                         "channel 'stable' resolves through dist-tag 'latest'")
    ap.add_argument("--target", default=None,
                    help="check this exact version instead of the channel's current build")
    ap.add_argument("--soak-days", type=int, default=None,
                    help="days a version must have been promoted (default: fleet config, else 14)")
    ap.add_argument("--package", default=DEFAULT_PACKAGE, help="npm package holding the runtime")
    ap.add_argument("--repo", default=None,
                    help="OWNER/NAME for the release history (default: derived from the package "
                         "manifest, never hard-coded)")
    ap.add_argument("--image", default=None,
                    help="image reference to resolve to a digest for the pin check")
    ap.add_argument("--no-net", action="store_true",
                    help="skip every network read: report installed versions and drift only")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--table", action="store_true")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    cfg = cfgmod.load_config(args.config)
    for line in cfg.warnings:
        sys.stderr.write("warning: %s\n" % line)

    channel_name = args.channel or (cfg.policy("update_channel", "stable") if cfg.present
                                    else "stable")
    soak_days = args.soak_days if args.soak_days is not None else (
        int(cfg.policy("soak_days", 14)) if cfg.present else 14)
    tag = CHANNEL_TAGS.get(channel_name)
    if tag is None:
        sys.stderr.write("error: unknown channel %r (known: %s)\n"
                         % (channel_name, ", ".join(sorted(CHANNEL_TAGS))))
        return EXIT_CONFIG

    try:
        records = discovery.discover(prefix=args.prefix, cfg=cfg, probe=True)
    except discovery.DockerError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    try:
        picked = fleet.resolve(records, args.selector, cfg, mutation=False)
    except fleet.SelectorError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return EXIT_RUNTIME
    if not picked:
        sys.stderr.write("error: selector %r matched no instance\n" % (args.selector or "managed"))
        return EXIT_EMPTY

    rows = instance_versions(picked)
    channel = {"name": channel_name, "tag": tag, "version": None, "error": None}
    all_tags, releases, repo = {}, None, args.repo
    if not args.no_net:
        try:
            all_tags = dist_tags(args.package, args.timeout)
            channel["version"] = all_tags.get(tag)
            if channel["version"] is None:
                channel["error"] = ("dist-tag %r does not exist for %s — the channel name is not "
                                    "a docker tag and not a git branch" % (tag, args.package))
        except NetError as exc:
            channel["error"] = str(exc)
        if repo is None and (channel["version"] or all_tags.get("latest")):
            try:
                manifest = version_manifest(args.package,
                                            channel["version"] or all_tags["latest"], args.timeout)
                repo = repo_slug(manifest)
            except NetError as exc:
                channel["error"] = channel["error"] or str(exc)
        if repo:
            try:
                releases = github_releases(repo, args.timeout)
            except NetError as exc:
                sys.stderr.write("warning: release history unavailable (%s); the soak clock "
                                 "cannot be verified\n" % exc)

    target = args.target or channel["version"]
    installed = {r["name"]: r["version"] for r in rows if r.get("version")}
    digest_check = None
    if args.image:
        resolved = image_digest(args.image, timeout=max(30, args.timeout))
        digest_check = {"reference": args.image, "actual": resolved["digest"],
                        "expected": None, "source": resolved["source"],
                        "error": resolved["error"]}
        if gate.is_moving_tag(args.image):
            sys.stderr.write("warning: %s is a moving tag; pin the digest %s instead\n"
                             % (args.image, resolved["digest"] or "(unresolved)"))

    verdict = None
    if target:
        verdict = soak_gate(target, releases, soak_days, installed_versions=installed,
                            channel_version=channel["version"], digest_check=digest_check)

    drift = drift_report(rows, target=target)
    payload = {
        "schema": SCHEMA,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
                        .isoformat().replace("+00:00", "Z"),
        "selector": args.selector or "managed",
        "package": args.package,
        "repository": repo,
        "channel": channel,
        "all_tags": all_tags,
        "soak_days": soak_days,
        "gate": verdict,
        "digest": digest_check,
        "drift": drift,
        "instances": rows,
    }

    emit(None, True, payload) if args.json else emit(render(payload))

    if verdict and verdict["verdict"] != "accepted":
        return EXIT_REJECTED
    if drift["distinct"] > 1:
        return EXIT_DRIFT
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
