"""Сверка «за чем следит плагин» с реестрами — без модели (spec workspace 2026-11-13-plugin-refresh §5.2).

Читает [upstream] из plugin-test.toml, спрашивает npm, PyPI, GitHub (через `gh api`), Docker Hub и добавляет
поводы из ночного L1 (дрейф MCP и CLI). Итог — очередь «кому пора обновиться и почему» для ночной службы
обновления. Сеть может отказать: такой источник получает повод source-error и в очередь не ставится.
"""
from __future__ import annotations

import datetime
import fnmatch
import http.client
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import discover, manifest

QUARTER_DAYS = 90
HTTP_TIMEOUT = 20
GH_TIMEOUT = 30
USER_AGENT = "agents-store-plugin-upstream"
OFFLINE_VAR = "PLUGIN_UPSTREAM_OFFLINE"          # 1 — никакой сети (тесты)
RE_SECURITY = re.compile(r"\bsecurity\b|\bCVE-\d{4}-\d+|\bGHSA-[0-9a-z]{4}-", re.I)
RE_VERSION = re.compile(r"^[vV]?(\d+(?:\.\d+)*)(?:[-+.]?([0-9A-Za-z][0-9A-Za-z.-]*))?$")
DRIFT_LEVELS = ("fail", "warn")
RE_MCP_SERVER = re.compile(r"^сервер ([^:\s]+)")
RE_CLI_TOOL = re.compile(r"^([^:\s]+):")
# Меньше — раньше в очереди. source-error, none и prerelease в очередь не ставят.
PRIORITY = {"security": 0, "major": 1, "minor": 2, "mcp-drift": 3, "cli-drift": 3,
            "quarterly": 4, "never-reviewed": 4, "patch": 5}


class UpstreamError(RuntimeError):
    """Реестр не ответил, ответил ошибкой или не тем JSON."""


@dataclass
class Release:
    version: str
    published: str = ""
    security: bool = False
    notes_url: str = ""


RE_TAG_PREFIX = re.compile(r"^(?:release[-_]?|v)", re.I)


def normalize_tag(name: str) -> str:
    """Имя тега → версия: «n8n@2.47.5» → «2.47.5», «v1.2.3» → «1.2.3», «release-4.5.6» → «4.5.6»."""
    name = name.strip().rsplit("@", 1)[-1]
    return RE_TAG_PREFIX.sub("", name)


def parse_version(value):
    """(числа, prerelease) или None. «v1.2.3» → ((1, 2, 3), ""); «1.3.0-beta.1» → ((1, 3, 0), "beta.1")."""
    if not isinstance(value, str):
        return None
    m = RE_VERSION.match(value.strip())
    if not m:
        return None
    nums = tuple(int(x) for x in m.group(1).split("."))
    return nums, (m.group(2) or "")


def _padded(nums, size):
    return nums + (0,) * (size - len(nums))


def bump_kind(pinned: str, latest: str) -> str:
    """major | minor | patch | none | prerelease | unparsed — что изменилось от pinned к latest."""
    a, b = parse_version(pinned), parse_version(latest)
    if a is None or b is None:
        return "none" if pinned.strip() == latest.strip() else "unparsed"
    (na, pa), (nb, pb) = a, b
    if pb and not pa:
        return "prerelease"
    size = max(len(na), len(nb), 3)
    na, nb = _padded(na, size), _padded(nb, size)
    if nb > na:
        first = next(i for i in range(size) if nb[i] != na[i])
        return ("major", "minor")[first] if first < 2 else "patch"
    if nb == na and pa and (not pb or pb > pa):
        return "patch"
    return "none"


def _best(names):
    """Старшая стабильная semver/calver-версия из списка имён тегов, или None."""
    best = None
    for name in names:
        name = normalize_tag(name)
        parsed = parse_version(name)
        if parsed is None or parsed[1]:
            continue
        key = _padded(parsed[0], 6)
        if best is None or key > best[0]:
            best = (key, name)
    return best[1] if best else None


def url_for(source) -> str:
    if source.kind == "npm":
        return "https://registry.npmjs.org/%s" % source.id
    if source.kind == "pypi":
        return "https://pypi.org/pypi/%s/json" % source.id
    if source.kind == "github-release":
        return "gh:repos/%s/releases/latest" % source.id
    if source.kind == "github-tag":
        return "gh:repos/%s/tags?per_page=100" % source.id
    if source.kind == "docker":
        image = source.id if "/" in source.id else "library/%s" % source.id
        return "https://hub.docker.com/v2/repositories/%s/tags?page_size=100" % image
    return ""


def latest(source, fetch):
    """Release последней версии источника; None для docs. Ошибка выборки или формата — UpstreamError."""
    if source.kind == "docs":
        return None
    data = fetch(url_for(source))
    try:
        if source.kind == "npm":
            version = data["dist-tags"]["latest"]
            return Release(version, published=(data.get("time") or {}).get(version, ""))
        if source.kind == "pypi":
            return Release(data["info"]["version"])
        if source.kind == "github-release":
            body = data.get("body") or ""
            return Release(normalize_tag(data["tag_name"]), published=data.get("published_at") or "",
                           security=bool(RE_SECURITY.search(body)), notes_url=data.get("html_url") or "")
        names = [t["name"] for t in (data if source.kind == "github-tag" else data["results"])]
    except (KeyError, TypeError, AttributeError) as exc:
        raise UpstreamError("неожиданный ответ реестра (%s)" % type(exc).__name__)
    version = _best(names)
    if version is None:
        raise UpstreamError("нет стабильных версий")
    return Release(version)


def _label(source):
    return "%s:%s" % (source.kind, source.id or source.url)


def _vendored_only(plugin, m):
    """Все skills плагина — под skip_paths: обновлять в нём нечего (vercel-dev)."""
    root = os.path.join(plugin.dir, "skills")
    skills = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))) if os.path.isdir(root) else []
    if not skills or not m.upstream_skip_paths:
        return False
    return all(any(fnmatch.fnmatch("skills/%s/SKILL.md" % s, g) or fnmatch.fnmatch("skills/%s" % s, g)
                   for g in m.upstream_skip_paths) for s in skills)


def reasons(plugin, m, fetch, today: datetime.date, drift: set) -> list:
    """Поводы обновить плагин: версии источников, дрейф из ночного L1, квартал или «не выверялся»."""
    if _vendored_only(plugin, m):
        return []
    out = []
    for source in m.upstream_sources:
        if source.kind == "docs":
            continue
        try:
            release = latest(source, fetch)
        except Exception:   # noqa: BLE001 — реестр не должен ронять сверку (Review Focus 1): любой сбой = source-error
            out.append({"kind": "source-error", "source": _label(source), "from": source.pinned, "to": ""})
            continue
        if not source.pinned:
            continue
        bump = bump_kind(source.pinned, release.version)
        if bump not in ("major", "minor", "patch", "unparsed"):
            continue
        reason = {"kind": "security" if release.security else ("minor" if bump == "unparsed" else bump),
                  "source": _label(source), "from": source.pinned, "to": release.version}
        if bump == "unparsed":
            reason["unparsed"] = True
        out.append(reason)
    for key in sorted(drift):
        kind = "mcp-drift" if key.startswith("mcp:") else "cli-drift"
        out.append({"kind": kind, "source": key, "from": "", "to": ""})
    if m.upstream_reviewed is None:
        out.append({"kind": "never-reviewed", "source": "", "from": "", "to": ""})
    elif (today - m.upstream_reviewed).days > QUARTER_DAYS:
        out.append({"kind": "quarterly", "source": "", "from": m.upstream_reviewed.isoformat(), "to": ""})
    return out


def priority(reasons_list):
    """Наименьший приоритет среди поводов, которые ставят в очередь; None — не ставить."""
    values = [PRIORITY[r["kind"]] for r in reasons_list if r.get("kind") in PRIORITY]
    return min(values) if values else None


def nightly_drift(report_path) -> dict:
    """{плагин: {"mcp:<server>", "cli:<tool>"}} из находок mcp-list / cli-flags ночного отчёта L1."""
    try:
        with open(report_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    out = {}
    for f in data.get("findings", []) if isinstance(data, dict) else []:
        if not isinstance(f, dict) or f.get("level") not in DRIFT_LEVELS:
            continue
        message = f.get("message") or ""
        if f.get("check") == "mcp-list":
            m = RE_MCP_SERVER.match(message)
            key = "mcp:%s" % (m.group(1) if m else "?")
        elif f.get("check") == "cli-flags":
            m = RE_CLI_TOOL.match(message)
            key = "cli:%s" % (m.group(1) if m else "?")
        else:
            continue
        out.setdefault(f.get("plugin"), set()).add(key)
    return out


def default_fetch(url):
    """JSON по URL: `gh:<путь>` — через `gh api`, остальное — HTTPS. Любая ошибка — UpstreamError."""
    if os.environ.get(OFFLINE_VAR) == "1":
        raise UpstreamError("offline")
    try:
        if url.startswith("gh:"):
            proc = subprocess.run(["gh", "api", url[3:]], capture_output=True, text=True, timeout=GH_TIMEOUT)
            if proc.returncode != 0:
                raise UpstreamError("gh api: код %d" % proc.returncode)
            return json.loads(proc.stdout)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except UpstreamError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError, urllib.error.URLError, http.client.HTTPException) as exc:
        raise UpstreamError(type(exc).__name__)


def queue(repo, fetch, today, drift_by_plugin, errors=None) -> list:
    """Очередь [{plugin, dir, priority, reasons}] по возрастанию приоритета. errors (список) получает
    {plugin, source} каждого неответившего источника — и тех плагинов, что в очередь не попали."""
    out = []
    for plugin in discover.discover(repo):
        m, _ = manifest.load(plugin)
        found = reasons(plugin, m, fetch, today, drift_by_plugin.get(plugin.name, set()))
        if errors is not None:
            errors += [{"plugin": plugin.name, "source": r["source"]} for r in found if r["kind"] == "source-error"]
        prio = priority(found)
        if prio is None:
            continue
        out.append({"plugin": plugin.name, "dir": "plugins/%s" % plugin.dirname, "priority": prio, "reasons": found})
    return sorted(out, key=lambda e: (e["priority"], e["plugin"]))
