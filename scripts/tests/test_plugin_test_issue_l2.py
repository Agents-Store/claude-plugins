import contextlib
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, SCRIPTS_DIR  # noqa: E402

sys.path.insert(0, SCRIPTS_DIR)
import plugin_test_issue  # noqa: E402
from plugin_test.report import render_markdown  # noqa: E402


def finding(check, level, message, plugin="p-dev", file="plugins/p-dev/skills/web/evals/triggers.json"):
    return {"plugin": plugin, "check": check, "level": level, "message": message, "file": file, "line": 0,
            "fix": "", "original": ""}


def report(findings, plugins=("p-dev",)):
    summary = {k: 0 for k in ("fail", "warn", "infra", "skipped", "info")}
    for f in findings:
        summary[f["level"]] += 1
    summary["suppressed"] = 0
    return {"version": 1, "mode": "server", "repo": "claude-public-plugins", "started": "2026-10-06T03:00:00Z",
            "plugins": list(plugins), "summary": summary, "findings": findings}


L1_WARN = finding("skill-budget", "warn", "SKILL.md — 600 строк", file="plugins/p-dev/skills/web/SKILL.md")
MISFIRE = finding("behavior", "warn", "промах срабатывания: web «grab it» — ожидалось: сработать; промах в 2 из 3\nдетали")
UNHELPFUL = finding("behavior", "info", "не помогает: q-web-1 — с плагином 0.90, без 0.95",
                    file="plugins/p-dev/skills/web/evals/evals.json")


class Recorder:
    def __init__(self, issues=()):
        self.calls = []
        self.issues = list(issues)

    def __call__(self, args, input_text=None):
        self.calls.append((args, input_text))
        if args[:2] == ["issue", "list"]:
            return json.dumps(self.issues)
        return ""


class IssueL2Test(unittest.TestCase):
    def test_merge(self):
        a = report([L1_WARN], plugins=("p-dev", "q-dev"))
        b = report([MISFIRE, UNHELPFUL], plugins=("p-dev",))
        m = plugin_test_issue.merge([a, b])
        self.assertEqual(m["plugins"], ["p-dev", "q-dev"])
        self.assertEqual((m["summary"]["warn"], m["summary"]["info"]), (2, 1))
        self.assertEqual(len(m["findings"]), 3)
        self.assertEqual((m["repo"], m["started"]), ("claude-public-plugins", "2026-10-06T03:00:00Z"))

    def test_has_problems(self):
        self.assertFalse(plugin_test_issue.has_problems(report([L1_WARN])))
        self.assertTrue(plugin_test_issue.has_problems(report([MISFIRE])))
        self.assertFalse(plugin_test_issue.has_problems(report([UNHELPFUL])))
        self.assertTrue(plugin_test_issue.has_problems(report([finding("unit", "infra", "нет node")])))

    def test_markdown_l2_section(self):
        text = render_markdown(plugin_test_issue.merge([report([L1_WARN]), report([MISFIRE, UNHELPFUL])]))
        l1, _, l2 = text.partition("### L2 Поведение")
        self.assertIn("skill-budget", l1)
        self.assertNotIn("промах срабатывания", l1)
        self.assertIn("#### Промахи срабатывания (1)", l2)
        self.assertIn("«grab it»", l2)
        self.assertNotIn("детали", l2)
        self.assertIn("claude-sonnet-5-5", l2)
        info = l2.partition("#### Не помогает")[2]
        self.assertIn("<details>", info)

    def test_unprefixed_behavior_finding_is_not_dropped(self):
        crashed = finding("behavior", "infra", "проверка упала: KeyError: 'x'", file="")
        text = render_markdown(plugin_test_issue.merge([report([crashed])]))
        self.assertIn("#### Прочее (1)", text)
        self.assertIn("проверка упала", text)

    def test_sync_opens_issue_for_l2_warn(self):
        rec = Recorder()
        actions = plugin_test_issue.sync("o/r", plugin_test_issue.merge([report([]), report([MISFIRE])]), rec)
        self.assertEqual(actions, ["created"])
        body = next(t for a, t in rec.calls if a[:2] == ["issue", "create"])
        self.assertIn("### L2 Поведение", body)

    def test_sync_closes_when_only_info(self):
        rec = Recorder(issues=[{"number": 7, "state": "OPEN", "title": plugin_test_issue.TITLE}])
        actions = plugin_test_issue.sync("o/r", report([UNHELPFUL]), rec)
        self.assertEqual(actions, ["closed"])

    def test_cli_render_many(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        a = repo.write("a.json", json.dumps(report([L1_WARN])))
        b = repo.write("b.json", json.dumps(report([MISFIRE])))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = plugin_test_issue.main(["render", a, b])
        self.assertEqual(code, 0)
        self.assertIn("### L2 Поведение", out.getvalue())
        self.assertIn("skill-budget", out.getvalue())

    def test_cli_unreadable_report(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = plugin_test_issue.main(["render", "/nonexistent/x.json"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
