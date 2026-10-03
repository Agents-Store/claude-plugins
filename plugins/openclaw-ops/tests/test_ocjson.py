"""ocjson — the exit-code contracts, and the rule that only stdout is parsed.

Two invariants, both of which have cost real incidents elsewhere:

* a non-zero exit from a contract command is the ANSWER, not a failure — treat
  ``rc != 0`` as an error and the finding is thrown away;
* the CLI writes banners to stderr, so a ``2>&1`` glues a banner onto the
  document. stderr is kept for diagnosis and never fed to the parser.
"""

import json
import unittest

import _support                                  # noqa: F401  (path bootstrap)
import ocjson


BANNER = "update available: a newer runtime has been published\n"


class ExitContractTest(unittest.TestCase):
    """A documented exit code carries a verdict; an undocumented one carries none."""

    def test_doctor_lint_exit_code_is_a_threshold_contract(self):
        # 0 = nothing at or above --severity-min, 1 = at least one finding at or above it,
        # 2 = the command failed before the checks completed. 2 is NOT "warnings only".
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 0)[0], "clean")
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 1)[0], "findings")
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 2)[0], "failed")

    def test_a_lint_command_failure_is_failed_and_never_warn(self):
        for body in ("", '{"ok": false, "error": {"type": "cli_error", "message": "x"}}'):
            with self.subTest(body=body):
                result = ocjson.interpret("doctor --lint", 2, body, "")
                self.assertEqual(result.label, "failed")
                self.assertNotEqual(result.label, "warn")
                self.assertFalse(result.ok)
                self.assertIn("before", result.explanation)

    def test_a_threshold_hit_is_not_called_an_error(self):
        # with --severity-min info the exit code is 1 for a lone info finding
        self.assertNotEqual(ocjson.exit_meaning("doctor --lint", 1)[0], "error")
        self.assertIn("threshold", ocjson.exit_meaning("doctor --lint", 1)[1])

    def test_post_upgrade_exits_one_only_for_an_error_level_finding(self):
        self.assertEqual(ocjson.exit_meaning("doctor --post-upgrade", 0)[0], "clean")
        self.assertEqual(ocjson.exit_meaning("doctor --post-upgrade", 1)[0], "error")
        # two is not part of the documented contract: it is an ordinary failure
        label, explanation = ocjson.exit_meaning("doctor --post-upgrade", 2)
        self.assertEqual(label, "failed")
        self.assertIn("no documented contract", explanation)

    def test_security_audit_has_no_contract_until_a_canary_confirms_one(self):
        # upstream documents no exit-code table for `security audit`; asserting one
        # reads a failure as "warnings only"
        self.assertNotIn("security audit", ocjson.EXIT_CONTRACTS)
        label, explanation = ocjson.exit_meaning("security audit", 2)
        self.assertEqual(label, "failed")
        self.assertIn("no documented contract", explanation)
        self.assertEqual(ocjson.exit_meaning("security audit", 1)[0], "failed")

    def test_secrets_audit_check_is_the_documented_gate_contract(self):
        self.assertEqual(ocjson.exit_meaning("secrets audit --check", 0)[0], "clean")
        self.assertEqual(ocjson.exit_meaning("secrets audit --check", 1)[0], "findings")
        self.assertEqual(ocjson.exit_meaning("secrets audit --check", 2)[0], "unresolved")

    def test_models_status_check_encodes_credential_state(self):
        self.assertEqual(ocjson.exit_meaning("models status --check", 0)[0], "healthy")
        self.assertEqual(ocjson.exit_meaning("models status --check", 1)[0], "expired")
        self.assertEqual(ocjson.exit_meaning("models status --check", 2)[0], "expiring")

    def test_every_declared_contract_has_a_clean_zero_and_a_finding_one(self):
        for key, table in ocjson.EXIT_CONTRACTS.items():
            with self.subTest(command=key):
                self.assertIn(0, table)
                self.assertIn(1, table)
                self.assertTrue(set(table) <= {0, 1, 2})

    def test_two_is_declared_only_where_upstream_documents_it(self):
        with_two = sorted(k for k, t in ocjson.EXIT_CONTRACTS.items() if 2 in t)
        self.assertEqual(with_two, ["doctor --lint", "models status --check",
                                    "secrets audit --check"])

    def test_an_undocumented_command_never_has_severity_read_into_its_exit_code(self):
        label, explanation = ocjson.exit_meaning("plugins list --json", 2)
        self.assertEqual(label, "failed")
        self.assertIn("no documented contract", explanation)

    def test_zero_is_success_for_a_command_with_no_contract(self):
        self.assertEqual(ocjson.exit_meaning(None, 0)[0], "ok")

    def test_a_missing_binary_and_a_kill_are_told_apart(self):
        self.assertEqual(ocjson.exit_meaning(None, 127)[0], "missing")
        for rc in (124, 137, 143):
            with self.subTest(rc=rc):
                self.assertEqual(ocjson.exit_meaning(None, rc)[0], "timeout")

    def test_ok_is_false_when_the_contract_reports_findings(self):
        lint = _support.load_text("doctor-lint.json")
        self.assertFalse(ocjson.interpret("doctor --lint", 1, lint, "").ok)
        self.assertTrue(ocjson.interpret("doctor --lint", 0, '{"findings": []}', "").ok)


class StdoutOnlyTest(unittest.TestCase):
    """The document is read from stdout. stderr is diagnosis, never input."""

    def setUp(self):
        self.lint = _support.load_text("doctor-lint.json")

    def test_a_banner_on_stderr_does_not_reach_the_parser(self):
        result = ocjson.interpret("doctor --lint", 1, self.lint, BANNER)
        self.assertIsNone(result.parse_error)
        self.assertEqual(len(result.findings()), 4)
        self.assertIn("update available", result.stderr)

    def test_a_document_delivered_on_stderr_is_not_parsed(self):
        result = ocjson.interpret("doctor --lint", 1, "", self.lint)
        self.assertIsNone(result.json)
        self.assertEqual(result.parse_error, "empty stdout")
        self.assertEqual(result.findings(), [])

    def test_a_banner_printed_onto_stdout_is_survivable(self):
        result = ocjson.interpret("doctor --lint", 1, BANNER + self.lint, "")
        self.assertIsNone(result.parse_error)
        self.assertEqual(len(result.findings()), 4)

    def test_newline_delimited_json_is_accepted_as_a_list(self):
        rows = '{"checkId": "a", "severity": "warn"}\n{"checkId": "b", "severity": "info"}'
        value, error = ocjson.parse_json(rows)
        self.assertIsNone(error)
        self.assertEqual(len(value), 2)

    def test_prose_is_reported_as_unparseable_rather_than_guessed_at(self):
        value, error = ocjson.parse_json("no findings today")
        self.assertIsNone(value)
        self.assertIn("not JSON", error)

    def test_the_raw_streams_are_kept_for_diagnosis(self):
        result = ocjson.interpret("doctor --lint", 1, self.lint, BANNER, argv=["doctor", "--lint"])
        payload = result.as_dict()
        self.assertEqual(payload["rc"], 1)
        self.assertEqual(payload["stderr"], BANNER)
        self.assertEqual(payload["argv"], ["doctor", "--lint"])


class FindingsTest(unittest.TestCase):
    """The lint finding shape is the contract between diagnostics and /repair."""

    def setUp(self):
        self.doc = _support.load_json("doctor-lint.json")
        self.items = ocjson.findings(self.doc)

    def test_findings_are_extracted_from_the_wrapper(self):
        self.assertEqual(len(self.items), 4)

    def test_every_finding_carries_a_check_id_and_a_fix_hint(self):
        for item in self.items:
            with self.subTest(check=item.get("checkId")):
                self.assertTrue(item.get("checkId"))
                self.assertTrue(item.get("fixHint"))

    def test_the_worst_severity_present_is_the_verdict(self):
        self.assertEqual(ocjson.worst_severity(self.items), "critical")

    def test_a_lower_wrapper_key_is_also_understood(self):
        self.assertEqual(len(ocjson.findings({"issues": self.items})), 4)

    def test_a_bare_finding_document_is_a_finding(self):
        self.assertEqual(len(ocjson.findings({"checkId": "x", "severity": "warn"})), 1)

    def test_an_empty_document_yields_no_findings_and_no_exception(self):
        self.assertEqual(ocjson.findings(None), [])
        self.assertEqual(ocjson.worst_severity([]), None)

    def test_severities_present_in_the_fixture_span_the_upstream_vocabulary(self):
        severities = sorted({f["severity"] for f in self.items})
        self.assertEqual(severities, ["critical", "error", "info", "warn"])

    def test_the_fixture_is_the_documented_finding_shape(self):
        for item in self.items:
            for key in ocjson.FINDING_KEYS:
                with self.subTest(check=item["checkId"], key=key):
                    self.assertIn(key, item)


class PostUpgradeEnvelopeTest(unittest.TestCase):
    """`doctor --post-upgrade --json` is `{probesRun, findings}` and names its level `level`."""

    ENVELOPE = {"probesRun": 3, "findings": [
        {"id": "plugin.version_drift", "level": "warn", "message": "drift"},
        {"id": "plugin.index_unavailable", "level": "error", "message": "no index"}]}

    def test_findings_are_read_out_of_the_probe_envelope(self):
        self.assertEqual(len(ocjson.findings(self.ENVELOPE)), 2)

    def test_the_worst_level_is_read_when_there_is_no_severity_field(self):
        self.assertEqual(ocjson.worst_severity(ocjson.findings(self.ENVELOPE)), "error")

    def test_a_warning_only_envelope_does_not_read_as_an_error(self):
        warn_only = {"probesRun": 1, "findings": [self.ENVELOPE["findings"][0]]}
        self.assertEqual(ocjson.worst_severity(ocjson.findings(warn_only)), "warn")

    def test_an_error_level_finding_exits_one_and_a_warning_exits_zero(self):
        body = json.dumps(self.ENVELOPE)
        self.assertEqual(ocjson.interpret("doctor --post-upgrade", 1, body, "").label, "error")
        quiet = json.dumps({"probesRun": 1, "findings": [self.ENVELOPE["findings"][0]]})
        result = ocjson.interpret("doctor --post-upgrade", 0, quiet, "")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.findings()), 1)


class LintEnvelopeTest(unittest.TestCase):
    """The lint document carries `ok`, `checksRun` and `checksSkipped`; rc 2 still carries a finding."""

    FAILED = {"ok": False, "checksRun": 0, "checksSkipped": 0,
              "error": {"type": "cli_error", "message": "inspection failed"},
              "findings": [{"checkId": "core/doctor/lint-inspection", "severity": "error",
                            "message": "inspection failed", "path": "state"}]}

    def test_the_failure_document_is_a_finding_and_the_run_is_still_failed(self):
        result = ocjson.interpret("doctor --lint", 2, json.dumps(self.FAILED), "")
        self.assertEqual(result.label, "failed")
        self.assertFalse(result.ok)
        self.assertEqual(result.findings()[0]["checkId"], "core/doctor/lint-inspection")

    def test_a_warning_finding_under_the_documented_spelling_is_ranked(self):
        doc = {"ok": False, "findings": [{"checkId": "core/doctor/gateway-config",
                                          "severity": "warning"}]}
        self.assertEqual(ocjson.worst_severity(ocjson.findings(doc)), "warning")


class ContractDocumentTest(unittest.TestCase):
    """The exit code carries the verdict; the document carries the detail.

    These also pin the fixtures: a captured document that gets "tidied up" into
    a healthy one stops exercising the trap it was captured for, and no test
    would notice.
    """

    def test_the_credential_verdict_comes_from_the_exit_code_not_the_body(self):
        body = _support.load_text("models-status.json")
        self.assertEqual(ocjson.interpret("models status --check", 1, body, "").label, "expired")
        self.assertEqual(ocjson.interpret("models status --check", 2, body, "").label, "expiring")
        self.assertEqual(ocjson.interpret("models status --check", 0, body, "").label, "healthy")

    def test_the_credential_document_still_names_each_profile_state(self):
        doc = ocjson.interpret("models status --check", 1,
                               _support.load_text("models-status.json"), "").json
        self.assertEqual([p["status"] for p in doc["profiles"]],
                         ["expired", "expiring", "ok"])

    def test_a_green_health_verdict_can_sit_on_top_of_undrained_queues(self):
        doc, error = ocjson.parse_json(_support.load_text("health.json"))
        self.assertIsNone(error)
        self.assertTrue(doc["ok"])
        self.assertGreater(doc["ingressPressure"], 0)
        self.assertGreater(doc["deliveryQueues"]["depth"], 0)


if __name__ == "__main__":
    unittest.main()
