"""Tests for plane_guard.py: run with
python3 -W error::ResourceWarning -m unittest discover -s plugins/plane-ops/hooks -v
"""

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "plane_guard.py")


def run_guard(stdin_text):
    """Run the guard as the hook runner does; return (exit code, stdout, stderr)."""
    done = subprocess.run(
        [sys.executable, GUARD],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def call(tool_name, **tool_input):
    return json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool_name, "tool_input": tool_input})


class PlaneGuardTest(unittest.TestCase):
    def assertSilent(self, stdin_text):
        code, out, err = run_guard(stdin_text)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def decision(self, stdin_text):
        code, out, _ = run_guard(stdin_text)
        self.assertEqual(code, 0)
        return json.loads(out)["hookSpecificOutput"]

    def test_delete_asks_through_permission_dialog(self):
        out = self.decision(call("mcp__plane__cycle", action="delete", project_id="p-1", cycle_id="c-9"))
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        reason = out["permissionDecisionReason"]
        self.assertIn("cycle(action=delete)", reason)
        self.assertIn("cycle_id=c-9", reason)
        self.assertIn("unlinked but kept", reason)

    def test_every_destructive_action_asks(self):
        for action in (
            "delete",
            "remove_projects",
            "remove_page",
            "remove_member",
            "detach",
            "detach_from_workitem",
            "delete_point",
            "delete_option",
            "delete_value",
            "delete_definition",
        ):
            with self.subTest(action=action):
                out = self.decision(call("mcp__my-plane-cloud__workitem", action=action, project_id="p"))
                self.assertEqual(out["permissionDecision"], "ask")

    def test_archive_adds_context_without_a_decision(self):
        out = self.decision(call("mcp__plane__cycle", action="archive", project_id="p", cycle_id="c"))
        self.assertNotIn("permissionDecision", out)
        self.assertIn("additionalContext", out)
        self.assertIn("unarchive", out["additionalContext"])
        self.assertIn("ends it first", out["additionalContext"])

    def test_unarchive_through_archive_false_is_silent(self):
        self.assertSilent(call("mcp__plane__workitem", action="archive", archive=False, project_id="p"))

    def test_read_and_write_actions_are_silent(self):
        for action in ("list", "retrieve", "create", "update", "complete", "transfer_workitems", "manage_workitems"):
            with self.subTest(action=action):
                self.assertSilent(call("mcp__plane__cycle", action=action, project_id="p"))

    def test_foreign_server_is_silent(self):
        self.assertSilent(call("mcp__notion__delete_page", page_id="x"))
        self.assertSilent(call("mcp__notion__page", action="delete", page_id="x"))

    def test_non_mcp_tool_is_silent(self):
        self.assertSilent(call("Bash", command="rm -rf /tmp/x"))

    def test_legacy_delete_asks(self):
        out = self.decision(call("mcp__plane__delete_cycle", project_id="p", cycle_id="c"))
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("delete_cycle", out["permissionDecisionReason"])

    def test_legacy_remove_and_detach_ask_and_archive_warns(self):
        self.assertEqual(self.decision(call("mcp__plane__remove_work_item_relation"))["permissionDecision"], "ask")
        self.assertEqual(self.decision(call("mcp__plane__detach_page_from_work_item"))["permissionDecision"], "ask")
        out = self.decision(call("mcp__plane__archive_cycle", project_id="p", cycle_id="c"))
        self.assertNotIn("permissionDecision", out)
        self.assertIn("additionalContext", out)

    def test_body_fields_are_not_echoed(self):
        out = self.decision(
            call("mcp__plane__page", action="delete", page_id="pg-1", description_html="<p>secret body</p>")
        )
        self.assertNotIn("secret body", out["permissionDecisionReason"])
        self.assertIn("page_id=pg-1", out["permissionDecisionReason"])

    def test_malformed_input_fails_open(self):
        for text in ("", "not json", "[]", "null", '{"tool_name": 5}', '{"tool_name": "mcp__plane__cycle"}',
                     '{"tool_name": "mcp__plane__cycle", "tool_input": "x"}', "{"):
            with self.subTest(stdin=text):
                self.assertSilent(text)


if __name__ == "__main__":
    unittest.main()
