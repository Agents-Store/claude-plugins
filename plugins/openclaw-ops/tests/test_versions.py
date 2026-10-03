"""versions — which line a version is on, where a channel points, and when a bridge is due.

Three upstream facts moved under this module and none of them is visible in a single
dist-tag lookup:

* the release line is now machine-readable — the high monthly patch numbers belong to the
  extended-stable line, the low ones to regular stable;
* ``beta`` is not the ``beta`` dist-tag: it is whichever of ``beta`` and ``latest`` is
  newer, so an old beta never replaces a newer stable, and ``dev`` is a git checkout of
  the moving head, not a package channel at all;
* an installation older than the cut-off cannot go straight to the current line. Doctor
  refuses and routes it through one bridge release, so the gate has to say so before an
  upgrade is attempted instead of after the refusal.

No network: every release list below is a literal, and ``now`` is passed in.
"""

import datetime
import json
import unittest
from unittest import mock

import _support                                  # noqa: F401  (path bootstrap)
import versions


NOW = datetime.datetime(2026, 10, 3, 12, 0, tzinfo=datetime.timezone.utc)


def release(tag, published):
    return {"tag_name": "v" + tag, "published_at": published,
            "html_url": "https://example.com/releases/" + tag}


# A release list in which every target below has long since soaked.
RELEASES = [
    release("2026.9.8", "2026-09-01T00:00:00Z"),
    release("2026.9.7", "2026-08-25T00:00:00Z"),
    release("2026.9.5", "2026-08-20T00:00:00Z"),
    release("2026.8.35", "2026-08-10T00:00:00Z"),
    release("2026.8.20", "2026-08-01T00:00:00Z"),
]


class ReleaseLineTest(unittest.TestCase):
    """The patch number says which line a build was cut for."""

    def line(self, text):
        return versions.release_line(text)["line"]

    def test_a_low_patch_is_regular_stable(self):
        for text in ("2026.9.8", "2026.9.1", "2026.8.32"):
            with self.subTest(version=text):
                self.assertEqual(self.line(text), "stable")

    def test_a_high_patch_is_the_extended_stable_line(self):
        for text in ("2026.8.33", "2026.8.35", "2026.7.34"):
            with self.subTest(version=text):
                self.assertEqual(self.line(text), "extended-stable")

    def test_the_boundary_is_one_named_constant(self):
        boundary = versions.EXTENDED_STABLE_MIN_PATCH
        self.assertEqual(self.line("2026.8.%d" % (boundary - 1)), "stable")
        self.assertEqual(self.line("2026.8.%d" % boundary), "extended-stable")

    def test_a_numeric_correction_keeps_the_line_of_its_base(self):
        self.assertEqual(self.line("2026.9.8-1"), "stable")
        self.assertEqual(self.line("2026.8.35-2"), "extended-stable")

    def test_a_named_prerelease_is_on_neither_line(self):
        self.assertEqual(self.line("2026.9.9-beta.1"), "prerelease")
        self.assertEqual(self.line("2026.9.9-rc.2"), "prerelease")

    def test_a_string_that_is_not_a_version_has_no_line(self):
        self.assertEqual(self.line("latest"), "unknown")
        self.assertEqual(self.line(None), "unknown")


class ChannelTargetTest(unittest.TestCase):
    """A channel name resolves to a version under rules of its own."""

    TAGS = {"latest": "2026.9.8", "beta": "2026.9.7", "extended-stable": "2026.8.35"}

    def test_stable_is_the_latest_dist_tag(self):
        self.assertEqual(versions.channel_target("stable", self.TAGS)["version"], "2026.9.8")

    def test_extended_stable_is_its_own_dist_tag(self):
        self.assertEqual(versions.channel_target("extended-stable", self.TAGS)["version"],
                         "2026.8.35")

    def test_beta_never_goes_backwards_to_an_older_beta_tag(self):
        got = versions.channel_target("beta", self.TAGS)
        self.assertEqual(got["version"], "2026.9.8")
        self.assertEqual(got["tag"], "latest")
        self.assertIn("newer", got["note"])

    def test_beta_takes_the_beta_tag_when_it_is_the_newer_one(self):
        tags = dict(self.TAGS, beta="2026.9.9-beta.1")
        got = versions.channel_target("beta", tags)
        self.assertEqual(got["version"], "2026.9.9-beta.1")
        self.assertEqual(got["tag"], "beta")

    def test_beta_falls_back_to_latest_when_the_beta_tag_is_missing(self):
        got = versions.channel_target("beta", {"latest": "2026.9.8"})
        self.assertEqual(got["version"], "2026.9.8")

    def test_dev_is_a_git_checkout_and_has_no_package_target(self):
        got = versions.channel_target("dev", self.TAGS)
        self.assertIsNone(got["version"])
        self.assertIn("git", got["note"])
        self.assertIn("production", got["note"])

    def test_an_optional_dev_dist_tag_is_reported_but_never_promoted_to_a_target(self):
        got = versions.channel_target("dev", dict(self.TAGS, dev="2026.10.0-dev.1"))
        self.assertIsNone(got["version"])

    def test_a_missing_dist_tag_is_a_finding_not_a_fallback(self):
        got = versions.channel_target("extended-stable", {"latest": "2026.9.8"})
        self.assertIsNone(got["version"])
        self.assertIn("does not exist", got["note"])

    def test_every_channel_name_the_fleet_config_accepts_resolves(self):
        for name in ("stable", "extended-stable", "beta", "dev"):
            with self.subTest(channel=name):
                self.assertIn("note", versions.channel_target(name, self.TAGS))


class BridgeGateTest(unittest.TestCase):
    """An installation older than the cut-off must cross the bridge release first."""

    def gate(self, target, installed, channel=None, releases=RELEASES):
        return versions.soak_gate(target, releases, 14, installed_versions=installed,
                                  now=NOW, channel=channel)

    def test_an_old_installation_aiming_past_the_bridge_is_refused_with_its_own_verdict(self):
        verdict = self.gate("2026.9.8", {"alpha": "2026.6.10"})
        self.assertEqual(verdict["verdict"], "bridge-required")
        self.assertEqual(verdict["bridge"]["version"], versions.BRIDGE_VERSION)
        self.assertEqual(verdict["bridge"]["instances"], ["alpha"])
        self.assertTrue(any("bridge" in r for r in verdict["reasons"]))

    def test_the_reason_names_what_to_run_between_the_two_hops(self):
        verdict = self.gate("2026.9.8", {"alpha": "2026.6.10"})
        text = " ".join(verdict["reasons"])
        self.assertIn(versions.BRIDGE_VERSION, text)
        self.assertIn("doctor --fix", text)

    def test_the_bridge_itself_is_an_acceptable_target_for_an_old_installation(self):
        verdict = self.gate(versions.BRIDGE_VERSION, {"alpha": "2026.6.10"})
        self.assertEqual(verdict["verdict"], "accepted")
        self.assertNotIn("bridge", verdict)

    def test_a_recent_installation_goes_straight_to_the_target(self):
        verdict = self.gate("2026.9.8", {"alpha": "2026.9.1"})
        self.assertEqual(verdict["verdict"], "accepted")

    def test_one_old_instance_in_the_selection_is_enough(self):
        verdict = self.gate("2026.9.8", {"alpha": "2026.9.1", "beta": "2026.5.30"})
        self.assertEqual(verdict["verdict"], "bridge-required")
        self.assertEqual(verdict["bridge"]["instances"], ["beta"])

    def test_the_cutoff_is_a_month_not_a_patch_number(self):
        before, after = versions.BRIDGE_REQUIRED_BEFORE, versions.BRIDGE_REQUIRED_BEFORE
        old = "%d.%d.99" % (before[0], before[1] - 1)
        new = "%d.%d.1" % (after[0], after[1])
        self.assertEqual(self.gate("2026.9.8", {"a": old})["verdict"], "bridge-required")
        self.assertEqual(self.gate("2026.9.8", {"a": new})["verdict"], "accepted")

    def test_an_unreadable_installed_version_does_not_trigger_the_bridge(self):
        verdict = self.gate("2026.9.8", {"alpha": "unknown"})
        self.assertNotEqual(verdict["verdict"], "bridge-required")

    def test_a_rejection_for_another_reason_is_not_softened_into_a_bridge_verdict(self):
        verdict = self.gate("2026.9.8-beta.1", {"alpha": "2026.6.10"})
        self.assertEqual(verdict["verdict"], "rejected")
        self.assertTrue(any("bridge" in r for r in verdict["reasons"]))

    def test_the_bridge_outranks_an_unverified_promotion_date(self):
        verdict = self.gate("2026.9.8", {"alpha": "2026.6.10"}, releases=[])
        self.assertEqual(verdict["verdict"], "bridge-required")


class LineGateTest(unittest.TestCase):
    """A channel's own line is checked, so a pointer cannot hand a fleet the wrong one."""

    def gate(self, target, channel):
        return versions.soak_gate(target, RELEASES, 14, now=NOW, channel=channel)

    def test_an_extended_stable_build_is_not_a_target_for_regular_stable(self):
        verdict = self.gate("2026.8.35", "stable")
        self.assertEqual(verdict["verdict"], "rejected")
        self.assertTrue(any("extended-stable" in r for r in verdict["reasons"]))

    def test_nor_for_beta_through_its_stable_fallback(self):
        self.assertEqual(self.gate("2026.8.35", "beta")["verdict"], "rejected")

    def test_a_regular_build_is_not_a_target_for_extended_stable(self):
        verdict = self.gate("2026.9.8", "extended-stable")
        self.assertEqual(verdict["verdict"], "rejected")

    def test_the_matching_line_is_accepted(self):
        self.assertEqual(self.gate("2026.9.8", "stable")["verdict"], "accepted")
        self.assertEqual(self.gate("2026.8.35", "extended-stable")["verdict"], "accepted")

    def test_no_channel_means_no_line_check(self):
        self.assertEqual(self.gate("2026.8.35", None)["verdict"], "accepted")


class RenderTest(unittest.TestCase):
    """The table says which line each hop is on and why a bridge is due."""

    def payload(self, verdict):
        return {"channel": {"name": "stable", "tag": "latest", "version": "2026.9.8",
                            "error": None, "note": None, "line": "stable"},
                "all_tags": {}, "gate": verdict, "instances": [],
                "drift": {"distinct": 0, "newest_installed": None, "moving_tags": []}}

    def test_a_bridge_verdict_is_printed_in_capitals_with_its_reasons(self):
        verdict = versions.soak_gate("2026.9.8", RELEASES, 14,
                                     installed_versions={"alpha": "2026.6.10"}, now=NOW)
        text = versions.render(self.payload(verdict))
        self.assertIn("BRIDGE-REQUIRED", text)
        self.assertIn(versions.BRIDGE_VERSION, text)

    def test_the_channel_line_is_printed_with_the_version(self):
        text = versions.render(self.payload(None))
        self.assertIn("line stable", text)


class MainTest(unittest.TestCase):
    """End to end with discovery and the network stubbed: what the operator actually sees."""

    TAGS = {"latest": "2026.9.8", "beta": "2026.9.7", "extended-stable": "2026.8.35"}

    def run_main(self, argv, installed="2026.9.1"):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        record = {"name": "alpha", "state": "ok", "role": "standard", "profile": "template",
                  "managed": True, "container": {"image": "openclaw:pinned", "image_digest": None},
                  "capabilities": {"cli_version": installed}}
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(versions.discovery, "discover", return_value=[record]), \
                mock.patch.object(versions.fleet, "resolve", return_value=[record]), \
                mock.patch.object(versions, "dist_tags", return_value=dict(self.TAGS)), \
                mock.patch.object(versions, "version_manifest",
                                  return_value={"repository": "git+https://github.com/o/r.git"}), \
                mock.patch.object(versions, "github_releases", return_value=list(RELEASES)), \
                redirect_stdout(out), redirect_stderr(err):
            code = versions.main(argv + ["--json"])
        return code, json.loads(out.getvalue())

    def test_beta_is_resolved_to_the_newer_tag_and_says_why(self):
        _code, doc = self.run_main(["--channel", "beta", "--soak-days", "1"])
        self.assertEqual(doc["channel"]["version"], "2026.9.8")
        self.assertEqual(doc["channel"]["tag"], "latest")
        self.assertIn("newer", doc["channel"]["note"])

    def test_dev_has_no_package_and_no_target(self):
        _code, doc = self.run_main(["--channel", "dev"])
        self.assertIsNone(doc["channel"]["version"])
        self.assertIn("git", doc["channel"]["note"])
        self.assertIsNone(doc["channel"]["error"])
        self.assertIsNone(doc["gate"])

    def test_an_old_installation_gets_the_bridge_verdict_and_the_rejection_exit(self):
        code, doc = self.run_main(["--soak-days", "1"], installed="2026.6.10")
        self.assertEqual(doc["gate"]["verdict"], "bridge-required")
        self.assertEqual(doc["gate"]["bridge"]["version"], versions.BRIDGE_VERSION)
        self.assertEqual(code, versions.EXIT_REJECTED)

    def test_the_channel_line_is_reported(self):
        _code, doc = self.run_main(["--channel", "extended-stable", "--soak-days", "1"])
        self.assertEqual(doc["channel"]["line"], "extended-stable")
        self.assertEqual(doc["gate"]["line"], "extended-stable")


if __name__ == "__main__":
    unittest.main()
