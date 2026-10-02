# scripts/tests/test_plugin_lint_mcp_prefix.py
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import plugin_lint  # noqa: E402


def make_plugin(files, mcp=None, name="demo-ops"):
    root = tempfile.mkdtemp()
    pdir = os.path.join(root, name)
    os.makedirs(pdir)
    if mcp is not None:
        with open(os.path.join(pdir, ".mcp.json"), "w") as fh:
            json.dump(mcp, fh)
    for rel, text in files.items():
        path = os.path.join(pdir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
    return pdir


class McpPrefixTest(unittest.TestCase):
    def test_bare_name_of_own_server_fails_with_line(self):
        pdir = make_plugin({"skills/a/SKILL.md": "x\ncall mcp__nocodb__queryRecords\n"},
                           mcp={"mcpServers": {"nocodb": {"type": "http", "url": "${U}"}}})
        found = plugin_lint.check_mcp_prefix(pdir, strict=False)
        self.assertEqual([(f.rule, f.severity, f.line) for f in found], [("mcp-prefix", "fail", 2)])
        self.assertIn("mcp__plugin_demo-ops_nocodb__", found[0].message)

    def test_prefixed_name_passes(self):
        pdir = make_plugin({"agents/x.md": "tools: mcp__plugin_demo-ops_nocodb__queryRecords\n"},
                           mcp={"mcpServers": {"nocodb": {"type": "http", "url": "${U}"}}})
        self.assertEqual(plugin_lint.check_mcp_prefix(pdir, strict=True), [])

    def test_user_configured_server_may_stay_bare(self):
        pdir = make_plugin({"skills/a/SKILL.md": "mcp__n8n-mcp-external__search_nodes\n"},
                           mcp={"mcpServers": {"nocodb": {"type": "http", "url": "${U}"}}})
        self.assertEqual(plugin_lint.check_mcp_prefix(pdir, strict=True), [])

    def test_top_level_map_without_mcpServers_key(self):
        pdir = make_plugin({"commands/c.md": "allowed-tools: mcp__exa__web_search_exa\n"},
                           mcp={"exa": {"command": "npx", "args": ["-y", "exa-mcp-server"]}})
        self.assertEqual(len(plugin_lint.check_mcp_prefix(pdir, strict=False)), 1)

    def test_learnings_and_mcp_json_are_history_not_findings(self):
        pdir = make_plugin({"LEARNINGS.md": "was mcp__nocodb__x\n"},
                           mcp={"mcpServers": {"nocodb": {"type": "http", "url": "${U}"}}})
        self.assertEqual(plugin_lint.check_mcp_prefix(pdir, strict=True), [])

    def test_no_mcp_json_no_findings(self):
        pdir = make_plugin({"skills/a/SKILL.md": "mcp__nocodb__x\n"})
        self.assertEqual(plugin_lint.check_mcp_prefix(pdir, strict=True), [])

    def test_prefix_uses_manifest_name_not_directory(self):
        pdir = make_plugin({".claude-plugin/plugin.json": '{"name": "tg-client"}',
                            "skills/a/SKILL.md": "mcp__tg-client__send\n"},
                           mcp={"mcpServers": {"tg-client": {"type": "http", "url": "${U}"}}},
                           name="tg-client-plugin")
        found = plugin_lint.check_mcp_prefix(pdir, strict=False)
        self.assertIn("mcp__plugin_tg-client_tg-client__", found[0].message)


if __name__ == "__main__":
    unittest.main()
