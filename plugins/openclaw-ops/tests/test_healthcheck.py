"""healthcheck — the severity vocabulary at the one place foreign words enter it.

Every finding this plugin emits carries one of four severities, and every other
place that meets an unknown one raises. The lint check is the single door an
upstream word comes through, and it used to end in `else "info"` — a chain that
turned a spelling nobody had mapped into the quietest class in the report. These
tests pin the translation and pin the refusal.
"""

import json
import unittest
from unittest import mock

import _support                                  # noqa: F401  (path bootstrap)
import healthcheck
import ocexec
import ocjson


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
                              "model": "example-model-a", "message": "could not be confirmed"}],
        "runtimeAuthRoutes": [{"provider": "anthropic", "runtime": "claude-cli",
                               "status": "indeterminate"},
                              {"provider": "openai", "runtime": "codex", "status": "usable"}]}}
    EXPIRED = {"auth": {
        "modelRouteIssues": [{"kind": "expired", "provider": "openai", "model": "example-model-b"}],
        "runtimeAuthRoutes": [{"provider": "openai", "runtime": "codex", "status": "expired"}]}}

    def test_a_cli_backed_route_reports_only_indeterminate(self):
        kinds, labels = healthcheck._auth_route_problems(self.INDETERMINATE)
        self.assertEqual(kinds, {"indeterminate"})
        self.assertIn("anthropic/example-model-a", labels)

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


class _LintOpts(object):
    """Just the switches check_lint reads."""

    def __init__(self, lint=True, lint_all=False, skip_cli=False, timeout=30):
        self.lint, self.lint_all, self.skip_cli, self.timeout = lint, lint_all, skip_cli, timeout


def _rec():
    return {"name": "alpha", "findings": [], "commands": {}, "metrics": {}}


def _lint_result(rc, body=""):
    return ocjson.interpret("doctor --lint", rc, body, "", argv=["doctor", "--lint"])


class LintInvocationTest(unittest.TestCase):
    """The exit code is only comparable between versions when the threshold is explicit."""

    def test_the_default_run_pins_the_lowest_threshold(self):
        argv = healthcheck.lint_argv(_LintOpts())
        self.assertEqual(argv, ["doctor", "--lint", "--json", "--severity-min", "info"])

    def test_the_audit_run_adds_the_opt_in_checks_in_the_same_call(self):
        argv = healthcheck.lint_argv(_LintOpts(lint_all=True))
        self.assertEqual(argv, ["doctor", "--lint", "--all", "--json", "--severity-min", "info"])

    def test_both_forms_stay_inside_the_read_only_class(self):
        # oc_read asserts R0 before it runs anything; a flag that tipped the class would
        # silently turn the whole lint check into "refused"
        for lint_all in (False, True):
            with self.subTest(lint_all=lint_all):
                argv = healthcheck.lint_argv(_LintOpts(lint_all=lint_all))
                self.assertEqual(ocexec.classify_argv(argv)[0], "R0")
                self.assertEqual(ocexec.derive_command_key(argv), "doctor --lint")

    def test_lint_all_implies_lint(self):
        args = healthcheck.build_parser().parse_args(["--lint-all"])
        self.assertTrue(healthcheck.Options(args).lint)
        self.assertTrue(healthcheck.Options(args).lint_all)


class LintFailureTest(unittest.TestCase):
    """Exit 2 is a command failure. It used to be read as "warnings only" and filed as clean."""

    def run_lint(self, result, opts=None):
        rec = _rec()
        with mock.patch.object(healthcheck, "oc_read", return_value=(result, "ok")) as read:
            healthcheck.check_lint(rec, {}, opts or _LintOpts())
        self.read = read
        return rec

    def test_a_failure_with_no_document_is_a_finding_not_a_pass(self):
        rec = self.run_lint(_lint_result(2, ""))
        self.assertEqual(rec["metrics"]["lint"], "failed")
        self.assertEqual(rec["commands"]["doctor_lint"], "failed")
        ids = [f["id"] for f in rec["findings"]]
        self.assertEqual(ids, ["fleet.lint.run-failed"])
        self.assertEqual(rec["findings"][0]["severity"], "high")

    def test_a_failure_document_is_passed_through_and_not_doubled(self):
        body = json.dumps({"ok": False, "checksRun": 0, "findings": [
            {"checkId": "core/doctor/lint-inspection", "severity": "error",
             "message": "inspection failed", "path": "state"}]})
        rec = self.run_lint(_lint_result(2, body))
        self.assertEqual(rec["metrics"]["lint"], "failed")
        self.assertEqual([f["id"] for f in rec["findings"]], ["core/doctor/lint-inspection"])
        self.assertEqual(rec["findings"][0]["severity"], "high")

    def test_threshold_findings_keep_their_verbatim_id_and_mapped_severity(self):
        body = json.dumps({"ok": False, "checksRun": 5, "findings": [
            {"checkId": "core/doctor/gateway-config", "severity": "warning",
             "message": "gateway.mode is unset", "path": "gateway.mode", "fixHint": "set it"},
            {"checkId": "memory-core/managed-local-embedding-setup", "severity": "info",
             "message": "not set up", "path": "memory.search"}]})
        rec = self.run_lint(_lint_result(1, body))
        self.assertEqual(rec["metrics"]["lint"], "findings")
        self.assertEqual([(f["id"], f["severity"]) for f in rec["findings"]],
                         [("core/doctor/gateway-config", "warn"),
                          ("memory-core/managed-local-embedding-setup", "info")])
        self.assertEqual(rec["findings"][0]["evidence"], "gateway.mode")

    def test_a_clean_run_records_clean_and_no_finding(self):
        rec = self.run_lint(_lint_result(0, json.dumps({"ok": True, "findings": []})))
        self.assertEqual(rec["metrics"]["lint"], "clean")
        self.assertEqual(rec["findings"], [])

    def test_the_lint_check_asks_for_the_documented_argv(self):
        self.run_lint(_lint_result(0, "{}"), _LintOpts(lint_all=True))
        self.assertEqual(self.read.call_args[0][1],
                         ["doctor", "--lint", "--all", "--json", "--severity-min", "info"])

    def test_without_the_switch_nothing_runs(self):
        rec = _rec()
        with mock.patch.object(healthcheck, "oc_read") as read:
            healthcheck.check_lint(rec, {}, _LintOpts(lint=False))
        read.assert_not_called()
        self.assertEqual(rec["metrics"], {})
