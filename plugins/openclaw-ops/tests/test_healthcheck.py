"""healthcheck — the severity vocabulary at the one place foreign words enter it.

Every finding this plugin emits carries one of four severities, and every other
place that meets an unknown one raises. The lint check is the single door an
upstream word comes through, and it used to end in `else "info"` — a chain that
turned a spelling nobody had mapped into the quietest class in the report. These
tests pin the translation and pin the refusal.
"""

import unittest

import _support                                  # noqa: F401  (path bootstrap)
import healthcheck


class UpstreamSeverityTest(unittest.TestCase):

    def test_the_mapped_spellings_land_in_the_one_vocabulary(self):
        for word, expected in (("critical", "critical"), ("FATAL", "critical"),
                               ("error", "high"), ("warning", "warn"),
                               ("warn", "warn"), ("info", "info")):
            with self.subTest(word=word):
                self.assertEqual(healthcheck.upstream_severity(word), expected)

    def test_every_translation_target_is_a_severity_this_plugin_declares(self):
        for value in healthcheck.UPSTREAM_SEVERITIES.values():
            self.assertIn(value, healthcheck.SEVERITIES)

    def test_an_unmapped_word_raises_instead_of_becoming_info(self):
        for word in ("blocker", "sev1", "notice", ""):
            with self.subTest(word=word):
                with self.assertRaisesRegex(ValueError, "unknown upstream severity"):
                    healthcheck.upstream_severity(word)

    def test_the_message_names_the_finding_it_came_from(self):
        with self.assertRaisesRegex(ValueError, "fs.permissions"):
            healthcheck.upstream_severity("blocker", "doctor --lint finding 'fs.permissions'")

    def test_a_missing_severity_is_not_quietly_ranked(self):
        with self.assertRaises(ValueError):
            healthcheck.upstream_severity(None)


if __name__ == "__main__":
    unittest.main()


class AuthRouteProblemsTest(unittest.TestCase):
    """`models status --check` exits 1 for two different worlds; only the document separates them."""

    INDETERMINATE = {"auth": {
        "modelRouteIssues": [{"kind": "indeterminate", "provider": "anthropic",
                              "model": "claude-opus-5", "message": "could not be confirmed"}],
        "runtimeAuthRoutes": [{"provider": "anthropic", "runtime": "claude-cli",
                               "status": "indeterminate"},
                              {"provider": "openai", "runtime": "codex", "status": "usable"}]}}
    EXPIRED = {"auth": {
        "modelRouteIssues": [{"kind": "expired", "provider": "openai", "model": "gpt-5.6-terra"}],
        "runtimeAuthRoutes": [{"provider": "openai", "runtime": "codex", "status": "expired"}]}}

    def test_a_cli_backed_route_reports_only_indeterminate(self):
        kinds, labels = healthcheck._auth_route_problems(self.INDETERMINATE)
        self.assertEqual(kinds, {"indeterminate"})
        self.assertIn("anthropic/claude-opus-5", labels)

    def test_a_usable_route_is_not_a_problem(self):
        _kinds, labels = healthcheck._auth_route_problems(self.INDETERMINATE)
        self.assertFalse([l for l in labels if "codex" in l])

    def test_a_real_expiry_is_not_swallowed_by_the_indeterminate_branch(self):
        kinds, _labels = healthcheck._auth_route_problems(self.EXPIRED)
        self.assertIn("expired", kinds)
        self.assertFalse(kinds <= {"indeterminate", "unknown"})

    def test_a_document_without_an_auth_block_says_nothing(self):
        for doc in ({}, {"auth": None}, [], None):
            with self.subTest(doc=doc):
                self.assertEqual(healthcheck._auth_route_problems(doc), (set(), []))


class OrphanedTimerTest(unittest.TestCase):
    """An isolated timer has no agent binding by construction — that is not an orphan."""

    def test_an_isolated_timer_without_a_binding_is_not_orphaned(self):
        self.assertFalse(healthcheck._timer_is_orphaned(
            {"id": "a", "sessionTarget": "isolated"}))

    def test_a_bound_timer_is_not_orphaned(self):
        self.assertFalse(healthcheck._timer_is_orphaned(
            {"id": "b", "sessionTarget": "main", "agentId": "main"}))

    def test_a_main_timer_without_a_binding_is_still_orphaned(self):
        self.assertTrue(healthcheck._timer_is_orphaned({"id": "c", "sessionTarget": "main"}))
        self.assertTrue(healthcheck._timer_is_orphaned({"id": "d"}))
