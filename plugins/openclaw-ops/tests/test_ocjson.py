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

    def test_doctor_lint_encodes_severity_in_its_exit_code(self):
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 0)[0], "clean")
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 1)[0], "error")
        self.assertEqual(ocjson.exit_meaning("doctor --lint", 2)[0], "warn")

    def test_models_status_check_encodes_credential_state(self):
        self.assertEqual(ocjson.exit_meaning("models status --check", 0)[0], "healthy")
        self.assertEqual(ocjson.exit_meaning("models status --check", 1)[0], "expired")
        self.assertEqual(ocjson.exit_meaning("models status --check", 2)[0], "expiring")

    def test_every_declared_contract_covers_zero_one_and_two(self):
        for key, table in ocjson.EXIT_CONTRACTS.items():
            with self.subTest(command=key):
                self.assertEqual(sorted(table), [0, 1, 2])

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
