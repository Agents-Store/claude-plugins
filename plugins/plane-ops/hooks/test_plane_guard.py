"""Tests for plane_guard.py: run with
python3 -W error::ResourceWarning -m unittest discover -s plugins/plane-ops/hooks -v
"""

import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "plane_guard.py")
HOOKS_JSON = os.path.join(HERE, "hooks.json")

# Every resource tool of Plane MCP 0.3.x that has a destructive "delete" action.
DELETABLE_RESOURCES = (
    "project",
    "cycle",
    "module",
    "milestone",
    "initiative",
    "state",
    "label",
    "workitem",
    "workitem_type",
    "workitem_property",
    "workitem_comment",
    "workitem_link",
    "workitem_relation",
    "workitem_attachment",
    "work_log",
    "intake",
    "page",
    "project_estimate",
    "release",
    "release_tag",
    "release_label",
    "customer",
    "customer_property",
    "customer_request",
    "collection",
    "template",
)
# Resource tools that have a manage_workitems action taking add_ids / remove_ids.
MANAGE_WORKITEMS_RESOURCES = ("cycle", "module", "milestone", "initiative", "release", "customer")


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


    def test_workitem_delete_asks_and_names_what_is_lost(self):
        out = self.decision(
            call("mcp__plane__workitem", action="delete", project_id="p-1", workitem_id="w-7", name="Fix login")
        )
        self.assertEqual(out["permissionDecision"], "ask")
        reason = out["permissionDecisionReason"]
        self.assertIn("workitem(action=delete)", reason)
        self.assertIn("workitem_id=w-7", reason)
        self.assertIn("comments", reason)

    def test_delete_asks_on_every_resource_tool(self):
        for tool in DELETABLE_RESOURCES:
            with self.subTest(tool=tool):
                out = self.decision(call("mcp__my-plane-cloud__" + tool, action="delete", project_id="p"))
                self.assertEqual(out["permissionDecision"], "ask")
                self.assertIn("%s(action=delete)" % tool, out["permissionDecisionReason"])
                self.assertNotIn("the addressed Plane object", out["permissionDecisionReason"])

    def test_removing_work_items_from_a_container_asks(self):
        for tool in MANAGE_WORKITEMS_RESOURCES:
            with self.subTest(tool=tool):
                out = self.decision(
                    call("mcp__plane__" + tool, action="manage_workitems", project_id="p", remove_ids=["w-1", "w-2"])
                )
                self.assertEqual(out["permissionDecision"], "ask")
                reason = out["permissionDecisionReason"]
                self.assertIn("%s(action=manage_workitems)" % tool, reason)
                self.assertIn("remove_ids=w-1, w-2", reason)
                self.assertIn("kept", reason)

    def test_remove_ids_in_the_same_call_as_add_ids_still_asks(self):
        out = self.decision(
            call("mcp__plane__cycle", action="manage_workitems", cycle_id="c", add_ids=["a"], remove_ids=["b"])
        )
        self.assertEqual(out["permissionDecision"], "ask")

    def test_remove_ids_sent_as_a_json_string_still_asks(self):
        out = self.decision(call("mcp__plane__module", action="manage_workitems", module_id="m", remove_ids='["w-1"]'))
        self.assertEqual(out["permissionDecision"], "ask")

    def test_adding_work_items_is_silent(self):
        self.assertSilent(call("mcp__plane__cycle", action="manage_workitems", project_id="p", add_ids=["w-1"]))
        for empty in ([], "", "[]", None):
            with self.subTest(remove_ids=empty):
                self.assertSilent(
                    call("mcp__plane__cycle", action="manage_workitems", project_id="p", add_ids=["w-1"], remove_ids=empty)
                )

    def test_label_and_assignee_removal_are_silent(self):
        self.assertSilent(call("mcp__plane__workitem", action="manage_label", workitem_id="w", remove_label_id="l"))
        self.assertSilent(call("mcp__plane__workitem", action="manage_assignee", workitem_id="w", remove_user_id="u"))

    def test_remove_ids_on_another_action_does_not_ask(self):
        self.assertSilent(call("mcp__plane__cycle", action="list_workitems", cycle_id="c", remove_ids=["w"]))

    def test_destructive_action_list_matches_the_server(self):
        # destructive=True actions of plane-mcp-server 0.3.x (plane_mcp/tools/*.py)
        server = {
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
        }
        sys.path.insert(0, HERE)
        try:
            import plane_guard
        finally:
            sys.path.remove(HERE)
        self.assertEqual(set(plane_guard.DESTRUCTIVE_ACTIONS), server)

    def test_matcher_in_hooks_json_reaches_every_guarded_tool(self):
        with open(HOOKS_JSON, encoding="utf-8") as handle:
            hooks = json.load(handle)
        entry = hooks["hooks"]["PreToolUse"][0]
        self.assertIn("plane_guard.py", entry["hooks"][0]["command"])
        matcher = re.compile(entry["matcher"])
        for tool in DELETABLE_RESOURCES:
            with self.subTest(tool=tool):
                self.assertIsNotNone(matcher.search("mcp__plane__" + tool))
                self.assertIsNotNone(matcher.search("mcp__plugin_x_my-plane-cloud__" + tool))
        # read-only tools have no destructive action: the hook does not need to start for them
        for read_only in ("member", "workspace", "workitem_activity", "get_pql_reference"):
            with self.subTest(read_only=read_only):
                self.assertIsNone(matcher.search("mcp__plane__" + read_only))
        for legacy in ("delete_cycle", "remove_work_item_relation", "detach_page_from_work_item", "archive_cycle"):
            with self.subTest(legacy=legacy):
                self.assertIsNotNone(matcher.search("mcp__plane__" + legacy))
        for other in ("mcp__notion__page", "mcp__github__delete_branch", "Bash"):
            with self.subTest(other=other):
                self.assertIsNone(matcher.search(other))


if __name__ == "__main__":
    unittest.main()
