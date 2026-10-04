import json
import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test import proc  # noqa: E402
from plugin_test.checks import REGISTRY, hook_fixtures  # noqa: E402
from plugin_test.model import FAIL, SKIPPED  # noqa: E402

GUARD = '''import json, sys
data = json.load(sys.stdin)
if data.get("tool_input", {}).get("action") == "delete":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask"}}))
'''

HOOKS = {"hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": 'echo "plugin loaded from $CLAUDE_PLUGIN_ROOT"'}]}],
    "PreToolUse": [
        {"matcher": "mcp__.*guard.*__.*", "hooks": [
            {"type": "command", "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"', "timeout": 10}]},
        {"matcher": "Bash", "hooks": [{"type": "prompt", "prompt": "check"}]},
    ],
    "Stop": [{"hooks": [{"type": "command", "command": "sleep 30 & sleep 30", "timeout": 1}]}],
}}


def fixture(event, expect, matcher=None, stdin=None, index=None):
    fx = {"event": event, "stdin": stdin or {"hook_event_name": event}, "expect": expect}
    if matcher is not None:
        fx["matcher"] = matcher
    if index is not None:
        fx["index"] = index
    return fx


class HookFixturesTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("h-ops", files={"hooks/hooks.json": json.dumps(HOOKS), "hooks/guard.py": GUARD})

    def check(self, **fixtures):
        self.repo.tests("h-ops", {"hooks/%s.json" % k: v for k, v in fixtures.items()})
        return run_check(hook_fixtures, self.repo.root, "h-ops")

    def test_registered(self):
        self.assertIs(REGISTRY["hook-fixtures"], hook_fixtures.run)

    def test_no_fixtures_no_findings(self):
        self.assertEqual(run_check(hook_fixtures, self.repo.root, "h-ops"), [])

    def test_passing_fixtures(self):
        delete = {"hook_event_name": "PreToolUse", "tool_name": "mcp__x_guard__item", "tool_input": {"action": "delete"}}
        found = self.check(
            start=fixture("SessionStart", {"exit": 0, "stdout_contains": "plugin loaded from /"}),
            ask=fixture("PreToolUse", {"json": {"hookSpecificOutput.permissionDecision": "ask"}},
                        matcher="mcp__.*guard.*__.*", stdin=delete),
            quiet=fixture("PreToolUse", {"stdout_empty": True}, matcher="mcp__.*guard.*__.*",
                          stdin={"hook_event_name": "PreToolUse", "tool_input": {"action": "list"}}))
        self.assertEqual(found, [])

    def test_wrong_expectation(self):
        found = self.check(bad=fixture("PreToolUse", {"exit": 2, "json": {"hookSpecificOutput.permissionDecision": "deny"}},
                                       matcher="mcp__.*guard.*__.*",
                                       stdin={"tool_input": {"action": "delete"}}))
        self.assertEqual(len(found), 2)
        self.assertTrue(all(f.level == FAIL and f.file == "tests/plugins/h-ops/hooks/bad.json" for f in found))

    def test_selection_errors(self):
        found = self.check(
            a=fixture("PreToolUse", {}),                       # две записи — нужен matcher
            b=fixture("PreToolUse", {}, matcher="nope"),       # нет такой записи
            c=fixture("Notification", {}),                     # нет события
            d=fixture("SessionStart", {}, index=3))            # нет hook-а с таким index
        self.assertEqual([f.level for f in found], [FAIL] * 4)

    def test_prompt_hook_skipped_and_timeout_fails(self):
        started = time.monotonic()
        found = self.check(p=fixture("PreToolUse", {}, matcher="Bash"), s=fixture("Stop", {}))
        self.assertEqual([f.level for f in found], [SKIPPED, FAIL])
        self.assertIn("не завершился", found[1].message)
        self.assertLess(time.monotonic() - started, 10, "фоновый sleep пережил тайм-аут hook-а")

    def test_fixture_not_json(self):
        found = self.check(broken="{oops")
        self.assertEqual([(f.level, f.file) for f in found], [(FAIL, "tests/plugins/h-ops/hooks/broken.json")])


class ProcTest(unittest.TestCase):
    def test_run_group(self):
        done = proc.run_group(["bash", "-c", "cat; echo err >&2; exit 3"], input="in", env={"PATH": os.environ["PATH"]},
                              cwd="/", timeout=10)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (3, "in", "err\n"))

    def test_timeout_kills_whole_group(self):
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            proc.run_group(["bash", "-c", "sleep 30 & sleep 30"], env={"PATH": os.environ["PATH"]}, cwd="/", timeout=1)
        self.assertLess(time.monotonic() - started, 10)


if __name__ == "__main__":
    unittest.main()
