import contextlib
import importlib.util
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import SCRIPTS_DIR, Repo  # noqa: E402

spec = importlib.util.spec_from_file_location("plugin_test_issue", os.path.join(SCRIPTS_DIR, "plugin_test_issue.py"))
issue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issue)


def report(fail=0, infra=0, warn=0):
    findings = [{"plugin": "p", "check": "skill-links", "level": "fail", "message": "m", "file": "plugins/p/a.md",
                 "line": 1, "fix": "", "original": ""}] * fail
    return {"version": 1, "mode": "server", "repo": "claude-public-plugins", "started": "2026-10-05T03:00:00Z",
            "plugins": ["p"], "summary": {"fail": fail, "warn": warn, "infra": infra, "skipped": 0, "info": 0,
                                          "suppressed": 0}, "findings": findings}


class FakeGh:
    def __init__(self, issues):
        self.issues = issues
        self.calls = []

    def __call__(self, args, input_text=None):
        self.calls.append((args[:2], input_text))
        if args[:2] == ["issue", "list"]:
            return json.dumps(self.issues)
        return ""

    def verbs(self):
        return [" ".join(a) for a, _ in self.calls if a != ["issue", "list"]]


class SyncTest(unittest.TestCase):
    def test_create_when_failing_and_absent(self):
        gh = FakeGh([{"number": 9, "state": "OPEN", "title": "Other"}])
        self.assertEqual(issue.sync("o/r", report(fail=1), gh), ["created"])
        self.assertEqual(gh.verbs(), ["label create", "issue create"])
        self.assertIn("Nightly plugin tests", gh.calls[-1][1])

    def test_update_and_reopen(self):
        gh = FakeGh([{"number": 5, "state": "CLOSED", "title": issue.TITLE},
                     {"number": 7, "state": "OPEN", "title": issue.TITLE}])
        self.assertEqual(issue.sync("o/r", report(infra=1), gh), ["updated", "reopened"])
        self.assertEqual(gh.verbs(), ["issue edit", "issue reopen"])

    def test_close_when_clean(self):
        gh = FakeGh([{"number": 5, "state": "OPEN", "title": issue.TITLE}])
        self.assertEqual(issue.sync("o/r", report(warn=3), gh), ["closed"])
        self.assertEqual(gh.verbs(), ["issue comment", "issue close"])

    def test_clean_and_closed_does_nothing(self):
        gh = FakeGh([{"number": 5, "state": "CLOSED", "title": issue.TITLE}])
        self.assertEqual(issue.sync("o/r", report(), gh), [])
        self.assertEqual(gh.verbs(), [])


class CliTest(unittest.TestCase):
    def test_render(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        path = repo.write("r.json", json.dumps(report(fail=1)))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = issue.main(["render", path])
        self.assertEqual(code, 0)
        self.assertIn("### Провалы (1)", out.getvalue())

    def test_unreadable_report(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(issue.main(["render", "/nonexistent/report.json"]), 1)


if __name__ == "__main__":
    unittest.main()
