"""report — the canonical render, the delta against the last run, and the vocabulary.

A health run answers "what is wrong now", which is the less useful half. What an
operator acts on is comparative: is this new, did the thing we fixed stay fixed,
has anyone touched this in six weeks. So the delta is tested as carefully as the
render.

The severity vocabulary is tested as a contract rather than as a label. A value
outside it used to be dropped silently — a critical finding could disappear from
the document with no message at all — so an unknown severity must now abort the
render loudly.
"""

import contextlib
import io
import json
import os
import tempfile
import unittest

import _support                                  # noqa: F401  (path bootstrap)
import report


def finding(instance, fid, severity, message="something happened"):
    return {
        "id": fid,
        "finding_id": "%s/%s" % (instance, fid),
        "instance": instance,
        "severity": severity,
        "message": message,
        "source": "cli:doctor --lint --json",
        "fix": "documented in the findings catalog",
        "evidence": None,
    }


def instance(name, findings, state="ok", health="ok", liveness="working",
             divergence=False, metrics=None):
    return {
        "name": name,
        "state": state,
        "health": health,
        "liveness": liveness,
        "divergence": divergence,
        "metrics": metrics or {"version": "2026.6.10", "credentials": "ok",
                               "log_age_hours": 1.5},
        "findings": findings,
    }


def snapshot(generated_at, instances):
    all_findings = [f for inst in instances for f in inst["findings"]]
    counts = {"instances": len(instances),
              "diverging": sum(1 for i in instances if i["divergence"])}
    for severity in ("info", "warn", "high", "critical"):
        counts[severity] = sum(1 for f in all_findings if f["severity"] == severity)
    return {
        "schema": report.HEALTH_SCHEMA,
        "generated_at": generated_at,
        "selector": "managed",
        "host": {"label": "acme-lab", "fingerprint": "0123456789abcdef"},
        "counts": counts,
        "instances": instances,
    }


BEFORE = "2026-08-01T06:00:00Z"
NOW = "2026-08-31T06:00:00Z"


def previous_run():
    return snapshot(BEFORE, [instance("alpha", [
        finding("alpha", "fleet.auth.expired", "high", "credentials expired"),
        finding("alpha", "fleet.cron.duplicates-after-upgrade", "warn", "two entries fire the same job"),
    ])])


def current_run():
    return snapshot(NOW, [
        instance("alpha", [
            finding("alpha", "fleet.auth.expired", "high", "credentials expired"),
            finding("alpha", "fleet.config.literal-secret", "critical",
                    "a channel token is stored inline"),
        ], state="degraded", health="degraded"),
        instance("beta", [], liveness="idle"),
    ])


class SeverityVocabularyTest(unittest.TestCase):
    """One vocabulary. A fifth spelling is a bug, not a synonym."""

    def test_the_vocabulary_is_ascending_and_declared_once(self):
        self.assertEqual(report.SEVERITIES, ("info", "warn", "high", "critical"))
        self.assertEqual(report.SEVERITY_RANK["critical"],
                         max(report.SEVERITY_RANK.values()))

    def test_a_known_severity_ranks_without_complaint(self):
        self.assertEqual(report.severity_rank("warn", "a test"), 1)

    def test_an_unknown_severity_raises_rather_than_ranking_zero(self):
        with self.assertRaises(report.SchemaError) as caught:
            report.severity_rank("error", "a test")
        self.assertIn("unknown severity", str(caught.exception))
        self.assertIn("critical", str(caught.exception))

    def test_a_missing_severity_raises_too(self):
        with self.assertRaises(report.SchemaError):
            report.severity_rank(None, "a test")

    def test_the_render_aborts_on_an_unknown_severity_instead_of_dropping_it(self):
        doc = snapshot(NOW, [instance("alpha", [finding("alpha", "x", "fatal")])])
        with self.assertRaises(report.SchemaError):
            report.render_markdown(doc, report.compute_delta(doc, None, []))

    def test_an_incomplete_instance_record_names_the_missing_field(self):
        doc = snapshot(NOW, [instance("alpha", [])])
        doc["instances"][0].pop("liveness")
        with self.assertRaisesRegex(report.SchemaError, "liveness"):
            report.render_markdown(doc, report.compute_delta(doc, None, []))


class DeltaTest(unittest.TestCase):
    """New, resolved, persisting — and how old the persisting ones are."""

    def setUp(self):
        self.previous = previous_run()
        self.current = current_run()
        self.delta = report.compute_delta(self.current, self.previous, [self.previous])

    def test_the_baseline_is_named(self):
        self.assertEqual(self.delta["baseline"], BEFORE)

    def test_a_finding_absent_from_the_baseline_is_new(self):
        self.assertEqual([f["finding_id"] for f in self.delta["new"]],
                         ["alpha/fleet.config.literal-secret"])

    def test_a_finding_gone_from_the_current_run_is_resolved(self):
        self.assertEqual([f["finding_id"] for f in self.delta["resolved"]],
                         ["alpha/fleet.cron.duplicates-after-upgrade"])

    def test_a_finding_in_both_runs_persists(self):
        self.assertEqual([f["finding_id"] for f in self.delta["persisting"]],
                         ["alpha/fleet.auth.expired"])

    def test_age_is_measured_from_the_first_snapshot_that_carried_the_id(self):
        persisting = self.delta["persisting"][0]
        self.assertEqual(persisting["first_seen"], BEFORE)
        self.assertEqual(persisting["age_days"], 30.0)

    def test_a_new_finding_is_first_seen_now(self):
        self.assertEqual(self.delta["new"][0]["first_seen"], NOW)
        self.assertEqual(self.delta["new"][0]["age_days"], 0.0)

    def test_a_changed_state_is_a_transition(self):
        fields = {(t["instance"], t["field"]): (t["from"], t["to"])
                  for t in self.delta["transitions"]}
        self.assertEqual(fields[("alpha", "state")], ("ok", "degraded"))

    def test_an_instance_that_appeared_is_a_transition_too(self):
        fields = {(t["instance"], t["field"]) for t in self.delta["transitions"]}
        self.assertIn(("beta", "presence"), fields)

    def test_findings_nobody_has_moved_on_are_listed_separately(self):
        stale = report.stale_findings(self.delta, min_age_days=14.0)
        self.assertEqual([f["finding_id"] for f in stale], ["alpha/fleet.auth.expired"])
        self.assertEqual(report.stale_findings(self.delta, min_age_days=60.0), [])

    def test_a_first_run_has_no_baseline_rather_than_a_fake_one(self):
        delta = report.compute_delta(current_run(), None, [])
        self.assertIsNone(delta["baseline"])
        self.assertEqual(len(delta["new"]), 2)
        self.assertEqual(delta["resolved"], [])


class RenderTest(unittest.TestCase):
    """The same input renders the same document, section for section."""

    def setUp(self):
        self.current = current_run()
        self.delta = report.compute_delta(self.current, previous_run(), [previous_run()])
        self.text = report.render_markdown(self.current, self.delta)

    def test_the_canonical_sections_are_present_and_in_order(self):
        positions = [self.text.index(section) for section in
                     ("## Fleet", "## Change since", "## Not moving", "## Findings")]
        self.assertEqual(positions, sorted(positions))

    def test_every_instance_has_a_row(self):
        self.assertIn("| alpha |", self.text)
        self.assertIn("| beta |", self.text)

    def test_the_header_reports_the_counts_the_snapshot_carries(self):
        self.assertIn("1 critical, 1 high, 0 warn, 0 info", self.text)

    def test_the_delta_is_rendered_with_its_baseline(self):
        self.assertIn("## Change since %s" % BEFORE, self.text)
        self.assertIn("**New (1)**", self.text)
        self.assertIn("**Resolved (1)**", self.text)

    def test_a_finding_carries_its_repair_command(self):
        self.assertIn("/openclaw-ops:repair alpha --issue fleet.config.literal-secret", self.text)

    def test_the_render_is_deterministic(self):
        again = report.render_markdown(self.current,
                                       report.compute_delta(current_run(), previous_run(),
                                                            [previous_run()]))
        self.assertEqual(self.text, again)

    def test_severity_min_filters_the_findings_section(self):
        doc = snapshot(NOW, [instance("alpha", [
            finding("alpha", "fleet.cron.duplicates-after-upgrade", "warn"),
            finding("alpha", "fleet.config.literal-secret", "critical"),
        ])])
        text = report.render_markdown(doc, report.compute_delta(doc, None, []),
                                      severity_min="critical")
        self.assertIn("### critical (1)", text)
        self.assertNotIn("### warn", text)

    def test_a_first_run_says_so_instead_of_printing_an_empty_delta(self):
        doc = current_run()
        text = report.render_markdown(doc, report.compute_delta(doc, None, []))
        self.assertIn("No earlier snapshot to compare against", text)


class MainTest(unittest.TestCase):
    """End to end, over a snapshot directory, including the exit codes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = os.path.join(self.tmp.name, "health")
        os.makedirs(self.state)
        self.absent_config = os.path.join(self.tmp.name, "no-fleet-config.json")

    def write(self, doc, name):
        path = os.path.join(self.state, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return path

    def run_report(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = report.main(["--state-dir", self.state,
                              "--config", self.absent_config] + list(args))
        return rc, out.getvalue(), err.getvalue()

    def test_the_newest_snapshot_is_rendered_against_the_one_before_it(self):
        self.write(previous_run(), "health-20260801T060000Z.json")
        self.write(current_run(), "health-20260831T060000Z.json")
        rc, text, _err = self.run_report()
        self.assertEqual(rc, report.EXIT_BLOCKING_FINDINGS)
        self.assertIn("## Change since %s" % BEFORE, text)
        self.assertIn("alpha/fleet.config.literal-secret", text)

    def test_warn_only_findings_exit_with_the_warn_code(self):
        doc = snapshot(NOW, [instance("alpha", [finding("alpha", "fleet.cron.duplicates-after-upgrade", "warn")])])
        path = self.write(doc, "health-20260831T060000Z.json")
        rc, _text, _err = self.run_report("--input", path)
        self.assertEqual(rc, report.EXIT_WARN_FINDINGS)

    def test_a_clean_fleet_exits_zero(self):
        doc = snapshot(NOW, [instance("alpha", [])])
        path = self.write(doc, "health-20260831T060000Z.json")
        rc, _text, _err = self.run_report("--input", path)
        self.assertEqual(rc, report.EXIT_OK)

    def test_an_unknown_severity_is_a_named_runtime_error_not_a_quiet_omission(self):
        doc = snapshot(NOW, [instance("alpha", [finding("alpha", "fleet.health.not-ok", "error")])])
        path = self.write(doc, "health-20260831T060000Z.json")
        rc, text, err = self.run_report("--input", path)
        self.assertEqual(rc, report.EXIT_RUNTIME)
        self.assertIn("unknown severity", err)
        self.assertEqual(text, "")

    def test_a_foreign_schema_is_refused(self):
        doc = snapshot(NOW, [instance("alpha", [])])
        doc["schema"] = "something/else/9"
        path = self.write(doc, "health-20260831T060000Z.json")
        rc, _text, err = self.run_report("--input", path)
        self.assertEqual(rc, report.EXIT_RUNTIME)
        self.assertIn("expected", err)

    def test_no_snapshot_at_all_says_how_to_make_one(self):
        rc, _text, err = self.run_report()
        self.assertEqual(rc, report.EXIT_RUNTIME)
        self.assertIn("healthcheck.py --snapshot", err)

    def test_the_json_format_carries_the_delta_as_data(self):
        self.write(previous_run(), "health-20260801T060000Z.json")
        path = self.write(current_run(), "health-20260831T060000Z.json")
        rc, text, _err = self.run_report("--input", path, "--format", "json")
        self.assertEqual(rc, report.EXIT_BLOCKING_FINDINGS)
        payload = json.loads(text)
        self.assertEqual(payload["schema"], report.REPORT_SCHEMA)
        self.assertEqual(payload["delta"]["new"], ["alpha/fleet.config.literal-secret"])
        self.assertEqual(payload["delta"]["resolved"], ["alpha/fleet.cron.duplicates-after-upgrade"])

    def test_the_rendered_document_passes_the_redactor_before_it_is_printed(self):
        doc = snapshot(NOW, [instance("alpha", [
            finding("alpha", "fleet.config.literal-secret", "critical",
                    "inline token sk-ant-api03-EXAMPLE-fixture-0000000000000000000000000000"),
        ])])
        path = self.write(doc, "health-20260831T060000Z.json")
        rc, text, err = self.run_report("--input", path)
        self.assertEqual(rc, report.EXIT_BLOCKING_FINDINGS)
        self.assertNotIn("sk-ant-api03-EXAMPLE-fixture", text)
        self.assertIn("[REDACTED:", text)
        self.assertIn("scrubbed:", err)


if __name__ == "__main__":
    unittest.main()
