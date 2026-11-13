import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, load_plugin  # noqa: E402

from plugin_test import manifest, upstream  # noqa: E402
from plugin_test.manifest import UpstreamSource  # noqa: E402

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date(2026, 11, 20)

FIXTURES = {
    "https://registry.npmjs.org/next": {"dist-tags": {"latest": "16.4.0"},
                                        "time": {"16.4.0": "2026-11-10T00:00:00Z"}},
    "https://pypi.org/pypi/sqlalchemy/json": {"info": {"version": "2.0.40"}},
    "gh:repos/acme/tool/releases/latest": {"tag_name": "v3.1.0", "published_at": "2026-11-01T00:00:00Z",
                                           "body": "Fixes GHSA-abcd-1234-wxyz in the parser",
                                           "html_url": "https://github.com/acme/tool/releases/tag/v3.1.0"},
    "gh:repos/acme/plain/releases/latest": {"tag_name": "1.4.0", "body": "Faster startup", "html_url": ""},
    "gh:repos/acme/mono/releases/latest": {"tag_name": "n8n@2.47.5", "body": "", "html_url": ""},
    "gh:repos/acme/tags/tags?per_page=100": [{"name": "v1.9.0"}, {"name": "v1.10.0"}, {"name": "v2.0.0-rc.1"}],
    "https://hub.docker.com/v2/repositories/library/redis/tags?page_size=100":
        {"results": [{"name": "latest"}, {"name": "7.4.1"}, {"name": "8.0.0-rc1"}, {"name": "7.10.0"}]},
}


def fetch(url):
    if url not in FIXTURES:
        raise upstream.UpstreamError("no fixture for %s" % url)
    return FIXTURES[url]


def failing_fetch(url):
    raise upstream.UpstreamError("HTTP 429")


class LatestTest(unittest.TestCase):
    def test_npm_latest(self):
        r = upstream.latest(UpstreamSource("npm", id="next"), fetch)
        self.assertEqual((r.version, r.published, r.security), ("16.4.0", "2026-11-10T00:00:00Z", False))

    def test_pypi_latest(self):
        self.assertEqual(upstream.latest(UpstreamSource("pypi", id="sqlalchemy"), fetch).version, "2.0.40")

    def test_github_release_security(self):
        r = upstream.latest(UpstreamSource("github-release", id="acme/tool"), fetch)
        self.assertEqual((r.version, r.security), ("3.1.0", True))
        self.assertFalse(upstream.latest(UpstreamSource("github-release", id="acme/plain"), fetch).security)

    def test_github_release_prefixed_tag(self):
        self.assertEqual(upstream.latest(UpstreamSource("github-release", id="acme/mono"), fetch).version, "2.47.5")
        self.assertEqual([upstream.normalize_tag(t) for t in ("n8n@2.47.5", "v1.2.3", "release-4.5.6", "@scope/pkg@1.0.0")],
                         ["2.47.5", "1.2.3", "4.5.6", "1.0.0"])

    def test_github_tag_semver_max(self):
        self.assertEqual(upstream.latest(UpstreamSource("github-tag", id="acme/tags"), fetch).version, "1.10.0")

    def test_docker_tags_skip_latest(self):
        self.assertEqual(upstream.latest(UpstreamSource("docker", id="redis"), fetch).version, "7.10.0")

    def test_docs_has_no_release(self):
        self.assertIsNone(upstream.latest(UpstreamSource("docs", url="https://example.com/docs"), fetch))


class BumpTest(unittest.TestCase):
    def test_bump_kind(self):
        cases = [("16.3.8", "16.4.0", "minor"), ("v1.2.3", "1.2.4", "patch"), ("1.2.3", "2.0.0", "major"),
                 ("1.2.3", "1.2.3", "none"), ("1.2.3", "1.3.0-beta.1", "prerelease"), ("2026.10", "2026.11", "minor"),
                 ("abc", "def", "unparsed"), ("1.3.0", "1.2.9", "none"), ("2.0.0-rc.1", "2.0.0-rc.2", "patch")]
        for pinned, latest, kind in cases:
            self.assertEqual(upstream.bump_kind(pinned, latest), kind, (pinned, latest))


class ReasonsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def plugin(self, toml, skills=("a",)):
        self.repo.plugin("u-dev", files={"skills/%s/SKILL.md" % s: "---\nname: %s\n---\n" % s for s in skills})
        if toml is not None:
            self.repo.tests("u-dev", {"plugin-test.toml": toml})
        p = load_plugin(self.repo.root, "u-dev")
        return p, manifest.load(p)[0]

    def kinds(self, reasons):
        return sorted(r["kind"] for r in reasons)

    def test_minor_release_is_a_reason(self):
        p, m = self.plugin('[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\nkind = "npm"\nid = "next"\n'
                           'pinned = "16.3.8"\n')
        reasons = upstream.reasons(p, m, fetch, TODAY, set())
        self.assertEqual(reasons, [{"kind": "minor", "source": "npm:next", "from": "16.3.8", "to": "16.4.0"}])

    def test_security_release(self):
        p, m = self.plugin('[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\nkind = "github-release"\n'
                           'id = "acme/tool"\npinned = "3.0.2"\n')
        self.assertEqual(self.kinds(upstream.reasons(p, m, fetch, TODAY, set())), ["security"])

    def test_reasons_quarterly(self):
        for days, expected in ((91, ["quarterly"]), (89, [])):
            reviewed = (TODAY - datetime.timedelta(days=days)).isoformat()
            p, m = self.plugin("[upstream]\nreviewed = %s\n" % reviewed)
            self.assertEqual(self.kinds(upstream.reasons(p, m, fetch, TODAY, set())), expected, days)

    def test_never_reviewed(self):
        p, m = self.plugin(None)
        self.assertEqual(self.kinds(upstream.reasons(p, m, fetch, TODAY, set())), ["never-reviewed"])

    def test_reasons_drift(self):
        p, m = self.plugin("[upstream]\nreviewed = 2026-11-01\n")
        reasons = upstream.reasons(p, m, fetch, TODAY, {"mcp:context7", "cli:gh"})
        self.assertEqual(self.kinds(reasons), ["cli-drift", "mcp-drift"])

    def test_source_error_not_queued(self):
        p, m = self.plugin('[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\nkind = "npm"\nid = "next"\n'
                           'pinned = "16.3.8"\n')
        reasons = upstream.reasons(p, m, failing_fetch, TODAY, set())
        self.assertEqual(self.kinds(reasons), ["source-error"])
        self.assertIsNone(upstream.priority(reasons))

    def test_unparsed_is_minor(self):
        self.assertEqual(upstream.priority([{"kind": "minor", "source": "x", "from": "a", "to": "b", "unparsed": True}]),
                         upstream.priority([{"kind": "minor", "source": "x", "from": "1", "to": "1.1"}]))
        p, m = self.plugin('[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\nkind = "pypi"\nid = "sqlalchemy"\n'
                           'pinned = "two"\n')
        reason = upstream.reasons(p, m, fetch, TODAY, set())[0]
        self.assertEqual((reason["kind"], reason.get("unparsed")), ("minor", True))

    def test_empty_pinned_is_no_version_reason(self):
        p, m = self.plugin('[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\nkind = "npm"\nid = "next"\n')
        self.assertEqual(upstream.reasons(p, m, fetch, TODAY, set()), [])

    def test_priority_order(self):
        def prio(kind):
            return upstream.priority([{"kind": kind, "source": "s", "from": "", "to": ""}])
        order = [prio(k) for k in ("security", "major", "minor", "mcp-drift", "quarterly", "patch")]
        self.assertEqual(order, sorted(order))
        self.assertEqual(len(set(order)), 6)
        self.assertEqual(prio("cli-drift"), prio("mcp-drift"))
        self.assertEqual(prio("never-reviewed"), prio("quarterly"))
        self.assertEqual(upstream.priority([{"kind": "patch"}, {"kind": "major"}]), prio("major"))

    def test_vendored_only_plugin_skipped(self):
        p, m = self.plugin('[upstream]\nskip_paths = ["skills/*"]\n', skills=("x", "y"))
        self.assertEqual(upstream.reasons(p, m, fetch, TODAY, set()), [])


class NightlyDriftTest(unittest.TestCase):
    def test_drift_from_report(self):
        report = {"findings": [
            {"plugin": "codemap-dev", "check": "mcp-list", "level": "warn",
             "message": "сервер drawio: новые инструменты: get_drawio_reference"},
            {"plugin": "infisical-dev", "check": "cli-flags", "level": "fail", "message": "infisical: флаг пропал: --x"},
            {"plugin": "ok-dev", "check": "mcp-list", "level": "pass", "message": "сервер a: ок"},
            {"plugin": "x-dev", "check": "skill-links", "level": "fail", "message": "битая ссылка"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(report, fh)
        self.addCleanup(os.unlink, fh.name)
        self.assertEqual(upstream.nightly_drift(fh.name), {"codemap-dev": {"mcp:drawio"}, "infisical-dev": {"cli:infisical"}})

    def test_missing_report_is_empty(self):
        self.assertEqual(upstream.nightly_drift("/nonexistent/report.json"), {})


class CliTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_queue_survives_network_errors(self):
        self.repo.plugin("a-dev", files={"skills/a/SKILL.md": "---\nname: a\n---\n"})
        self.repo.tests("a-dev", {"plugin-test.toml": '[upstream]\nreviewed = 2026-11-01\n[[upstream.source]]\n'
                                                     'kind = "npm"\nid = "definitely-not-a-package-xyz"\npinned = "1.0.0"\n'})
        self.repo.plugin("b-dev", files={"skills/b/SKILL.md": "---\nname: b\n---\n"})
        out = os.path.join(self.repo.root, "queue.json")
        env = dict(os.environ, PLUGIN_UPSTREAM_OFFLINE="1")      # любая сетевая выборка → UpstreamError
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "plugin_upstream.py"), "queue", "--repo",
                               self.repo.root, "--today", "2026-11-20", "--out", out],
                              capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out) as fh:
            queue = json.load(fh)
        self.assertEqual([q["plugin"] for q in queue], ["b-dev"])          # a-dev: только source-error
        self.assertEqual(queue[0]["reasons"][0]["kind"], "never-reviewed")
        self.assertEqual(queue[0]["dir"], "plugins/b-dev")


if __name__ == "__main__":
    unittest.main()
