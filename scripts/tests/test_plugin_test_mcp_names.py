import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, load_plugin, run_check  # noqa: E402

from plugin_test import mcp_config, snapshots  # noqa: E402
from plugin_test.checks import REGISTRY, mcp_names  # noqa: E402
from plugin_test.model import FAIL, SKIPPED  # noqa: E402

SNAPSHOT = {"tools": [
    {"name": "queryRecords", "description": "q", "inputSchema": {"type": "object", "required": ["table"]}},
    {"name": "getTableSchema", "description": "s", "inputSchema": {"type": "object"}},
]}
NOCODB = {"nocodb": {"type": "http", "url": "${NOCODB_MCP_URL}"}}

GOOD = """---
allowed-tools: mcp__plugin_db-ops_nocodb__queryRecords, mcp__plugin_db-ops_nocodb__*
---
Call `mcp__plugin_db-ops_nocodb__getTableSchema`. Prefix: `mcp__plugin_db-ops_nocodb__`.
Placeholder `mcp__plugin_db-ops_nocodb__<tool>`, mask `mcp__plugin_db-ops_nocodb__get*`.
Dependency tool: mcp__plugin_base-dev_store__ping.
"""

BROKEN = """Typo mcp__plugin_db-ops_nocodb__queryRecord here.
Wrong server mcp__plugin_db-ops_nocdb__queryRecords.
Not a dependency mcp__plugin_stranger-dev_x__y.
No snapshot mcp__plugin_db-ops_other__anything and again mcp__plugin_db-ops_other__more.
"""


class SnapshotsTest(unittest.TestCase):
    def test_normalize_sorts_and_strips(self):
        got = snapshots.normalize_tools([
            {"name": "b", "inputSchema": {"required": ["y", "x"]}, "annotations": {"readOnlyHint": True}},
            {"name": "a", "description": "A", "title": "T"},
            {"no": "name"},
        ])
        self.assertEqual(got, {"tools": [
            {"name": "a", "description": "A", "inputSchema": {"type": "object"}},
            {"name": "b", "description": "", "inputSchema": {"required": ["x", "y"]}},
        ]})

    def test_names_only(self):
        data = {"tools": [{"name": "q", "description": "rows of table Clients",
                           "inputSchema": {"type": "object", "properties": {"t": {"enum": ["Clients"]}}, "required": ["t"]}}]}
        self.assertEqual(snapshots.names_only(data), {"tools": [
            {"name": "q", "description": "", "inputSchema": {"type": "object", "required": ["t"]}}]})

    def test_diff(self):
        old = {"tools": [{"name": "a", "description": "1", "inputSchema": {"required": ["x"]}},
                         {"name": "gone", "description": "", "inputSchema": {}}]}
        new = {"tools": [{"name": "a", "description": "2", "inputSchema": {"required": ["x", "y"]}},
                         {"name": "fresh", "description": "", "inputSchema": {}}]}
        d = snapshots.diff_tools(old, new)
        self.assertEqual((d.missing, d.extra, d.description_changed), (["gone"], ["fresh"], ["a"]))
        self.assertEqual(d.required_changed, [("a", ["x"], ["x", "y"])])

    def test_load_errors(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        self.assertIsNone(snapshots.load(os.path.join(repo.root, "missing.json")))
        bad = repo.write("bad.json", "{oops")
        with self.assertRaises(snapshots.SnapshotError):
            snapshots.load(bad)
        wrong = repo.write("wrong.json", '{"tools": {}}')
        with self.assertRaises(snapshots.SnapshotError):
            snapshots.load(wrong)


class McpConfigTest(unittest.TestCase):
    def test_both_shapes_and_plugin_json(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        repo.plugin("a-dev", mcp=NOCODB)
        repo.plugin("b-dev", files={".mcp.json": '{"flat": {"command": "npx"}}'})
        repo.plugin("c-dev", plugin_json={"name": "c-dev", "mcpServers": {"inline": {"command": "x"}}})
        repo.plugin("d-dev")
        self.assertEqual(list(mcp_config.servers(load_plugin(repo.root, "a-dev"))), ["nocodb"])
        self.assertEqual(list(mcp_config.servers(load_plugin(repo.root, "b-dev"))), ["flat"])
        self.assertEqual(list(mcp_config.servers(load_plugin(repo.root, "c-dev"))), ["inline"])
        self.assertEqual(mcp_config.servers(load_plugin(repo.root, "d-dev")), {})

    def test_unreadable_config_raises_mcp_config_error(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        repo.plugin("a-dev", files={".mcp.json": "{not json"})
        repo.plugin("b-dev", plugin_json={"name": "b-dev", "mcpServers": "extra.json"},
                    files={"extra.json": "[1, 2"})
        for name, rel in (("a-dev", ".mcp.json"), ("b-dev", "extra.json")):
            with self.subTest(plugin=name):
                with self.assertRaises(mcp_config.McpConfigError) as cm:
                    mcp_config.servers(load_plugin(repo.root, name))
                self.assertTrue(cm.exception.path.endswith(os.path.join("plugins", name, rel)))
                self.assertTrue(cm.exception.msg)


class McpNamesTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("base-dev", mcp={"store": {"command": "npx"}})
        self.repo.tests("base-dev", {"snapshots/mcp/store.tools.json": {"tools": [{"name": "ping"}]}})

    def test_registered(self):
        self.assertIs(REGISTRY["mcp-names"], mcp_names.run)

    def test_good(self):
        self.repo.plugin("db-ops", deps=["base-dev"], mcp=NOCODB, files={"commands/q.md": GOOD})
        self.repo.tests("db-ops", {"snapshots/mcp/nocodb.tools.json": SNAPSHOT})
        self.assertEqual(run_check(mcp_names, self.repo.root, "db-ops"), [])

    def test_broken(self):
        mcp = dict(NOCODB, other={"command": "npx"})
        self.repo.plugin("db-ops", mcp=mcp, files={"skills/s/SKILL.md": BROKEN})
        self.repo.tests("db-ops", {"snapshots/mcp/nocodb.tools.json": SNAPSHOT})
        found = run_check(mcp_names, self.repo.root, "db-ops")
        self.assertEqual([(f.line, f.level) for f in found], [(1, FAIL), (2, FAIL), (3, FAIL), (0, SKIPPED)])
        self.assertIn("queryRecords", found[0].fix)

    def test_ellipsis_after_a_prefix_is_a_mask(self):
        # `…` (U+2026) прямо за префиксом — такая же маска, как `*`: «ai-…» не значит инструмент «ai».
        self.repo.plugin("db-ops", mcp=NOCODB, files={"skills/s/SKILL.md":
                         "Prefix `mcp__plugin_db-ops_nocodb__get…` and mcp__plugin_db-ops_nocodb__query\u2026 only.\n"
                         "A real typo still fails: mcp__plugin_db-ops_nocodb__queryRecord here\n"})
        self.repo.tests("db-ops", {"snapshots/mcp/nocodb.tools.json": SNAPSHOT})
        found = run_check(mcp_names, self.repo.root, "db-ops")
        self.assertEqual([(f.line, f.level) for f in found], [(2, FAIL)])
        self.assertIn("queryRecord", found[0].message)

    def test_bad_snapshot_is_a_finding(self):
        self.repo.plugin("db-ops", mcp=NOCODB, files={"a.md": "mcp__plugin_db-ops_nocodb__x\nmcp__plugin_db-ops_nocodb__y"})
        self.repo.tests("db-ops", {"snapshots/mcp/nocodb.tools.json": "{not json"})
        found = run_check(mcp_names, self.repo.root, "db-ops")
        self.assertEqual([(f.level, f.file) for f in found],
                         [(FAIL, "tests/plugins/db-ops/snapshots/mcp/nocodb.tools.json")])

    def test_bad_mcp_json_is_a_finding(self):
        self.repo.plugin("db-ops", files={
            ".mcp.json": "{not json",
            "a.md": "mcp__plugin_db-ops_nocodb__x\nmcp__plugin_db-ops_other__y\nmcp__plugin_db-ops_nocodb__z"})
        found = run_check(mcp_names, self.repo.root, "db-ops")
        self.assertEqual([(f.plugin, f.level, f.file) for f in found],
                         [("db-ops", FAIL, "plugins/db-ops/.mcp.json")])
        self.assertIn("MCP-конфиг не читается", found[0].message)
        self.assertIn(".mcp.json", found[0].fix)

    def test_bad_mcp_json_of_a_dependency_is_reported_on_the_owner(self):
        self.repo.plugin("broken-dev")
        with open(os.path.join(self.repo.root, "plugins", "broken-dev", ".mcp.json"), "wb") as fh:
            fh.write(b"\xff\xfe\x00 not utf8")
        self.repo.plugin("db-ops", deps=["broken-dev"], files={"a.md": "mcp__plugin_broken-dev_s__x"})
        found = run_check(mcp_names, self.repo.root, "db-ops")
        self.assertEqual([(f.plugin, f.level, f.file) for f in found],
                         [("broken-dev", FAIL, "plugins/broken-dev/.mcp.json")])


if __name__ == "__main__":
    unittest.main()
