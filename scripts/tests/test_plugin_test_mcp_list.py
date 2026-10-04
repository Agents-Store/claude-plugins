import contextlib
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import FIXTURES, Repo, run_check  # noqa: E402

from plugin_test import cli, snapshots  # noqa: E402
from plugin_test.checks import REGISTRY, mcp_list  # noqa: E402
from plugin_test.model import FAIL, INFO, INFRA, SKIPPED, WARN  # noqa: E402

STUB = os.path.join(FIXTURES, "stub_mcp_server.py")
# Значение собирается из кусков, чтобы scrub_check не принял сам тест за утечку.
SECRET = "very" + "-secret-" + "a1b2c3d4e5"
EXPECTED = {"tools": [
    {"name": "alpha", "description": "first",
     "inputSchema": {"type": "object", "properties": {"y": {}, "x": {}}, "required": ["x", "y"]}},
    {"name": "beta", "description": "second",
     "inputSchema": {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]}},
]}


def stub_server(mode="ok", extra_env=None):
    return {"stub": {"command": sys.executable, "args": ["${CLAUDE_PLUGIN_ROOT}/../../stub.py"],
                     "env": {"STUB_MODE": mode, **(extra_env or {})}}}


class McpListTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        with open(STUB, encoding="utf-8") as fh:
            self.repo.write("stub.py", fh.read())

    def make(self, mode="ok", start="ci", extra_env=None, snapshot=None, manifest_env=""):
        self.repo.plugin("s-dev", mcp=stub_server(mode, extra_env))
        files = {"plugin-test.toml": '[mcp.stub]\nstart = "%s"\n%s' % (start, manifest_env)}
        if snapshot is not None:
            files["snapshots/mcp/stub.tools.json"] = snapshot
        self.repo.tests("s-dev", files)

    def test_registered(self):
        self.assertIs(REGISTRY["mcp-list"], mcp_list.run)

    def test_update_then_clean(self):
        self.make()
        found = run_check(mcp_list, self.repo.root, "s-dev", update_snapshots=True)
        self.assertEqual([f.level for f in found], [INFO])
        path = os.path.join(self.repo.root, "tests/plugins/s-dev/snapshots/mcp/stub.tools.json")
        self.assertEqual(snapshots.load(path), EXPECTED)
        self.assertEqual(run_check(mcp_list, self.repo.root, "s-dev"), [])

    def test_names_only_snapshot(self):
        self.make(manifest_env='snapshot = "names"\n')
        run_check(mcp_list, self.repo.root, "s-dev", update_snapshots=True)
        path = os.path.join(self.repo.root, "tests/plugins/s-dev/snapshots/mcp/stub.tools.json")
        self.assertEqual(snapshots.load(path)["tools"][0], {"name": "alpha", "description": "",
                                                           "inputSchema": {"type": "object", "required": ["x", "y"]}})
        self.assertEqual(run_check(mcp_list, self.repo.root, "s-dev"), [])

    def test_drift(self):
        old = json.loads(json.dumps(EXPECTED))
        old["tools"][0]["inputSchema"]["required"] = ["x"]
        old["tools"][1]["description"] = "old text"
        old["tools"].append({"name": "gone", "description": "", "inputSchema": {}})
        self.make(snapshot=old)
        found = run_check(mcp_list, self.repo.root, "s-dev")
        self.assertEqual(sorted(f.level for f in found), [FAIL, FAIL, WARN])

    def test_no_snapshot_is_warn(self):
        self.make()
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [WARN])

    def test_bad_snapshot_file(self):
        self.make(snapshot="{oops")
        found = run_check(mcp_list, self.repo.root, "s-dev")
        self.assertEqual([(f.level, f.file) for f in found],
                         [(FAIL, "tests/plugins/s-dev/snapshots/mcp/stub.tools.json")])

    def test_ci_skips_server_only_and_never(self):
        self.make(start="server")
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [SKIPPED])
        self.make(start="never")
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev", mode="server")], [SKIPPED])

    def test_missing_var(self):
        self.make(extra_env={"TOKEN": "${STUB_TOKEN}"})
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [WARN])
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev", mode="server")], [INFRA])
        self.make(extra_env={"TOKEN": "${STUB_TOKEN}"}, manifest_env='env = { STUB_TOKEN = "dummy" }\n')
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [WARN])  # снимка нет

    def test_protocol_error_is_fail_and_crash_is_infra(self):
        self.make(mode="error")
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [FAIL])
        self.make(mode="crash")
        self.assertEqual([f.level for f in run_check(mcp_list, self.repo.root, "s-dev")], [INFRA])

    def test_bad_mcp_json_is_one_fail(self):
        self.repo.plugin("s-dev")
        self.repo.write("plugins/s-dev/.mcp.json", "{not json")
        found = run_check(mcp_list, self.repo.root, "s-dev")
        self.assertEqual([(f.level, f.file) for f in found], [(FAIL, "plugins/s-dev/.mcp.json")])

    def test_secret_echoed_by_server_is_redacted(self):
        self.make(mode="crash", start="server", extra_env={"STUB_SECRET": "${STUB_SECRET}"})
        env_file = self.repo.write("secrets.env", "STUB_SECRET=%s\n" % SECRET)
        report = os.path.join(self.repo.root, "report.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--repo", self.repo.root, "--mode", "server", "--env-file", env_file,
                             "--check", "mcp-list", "--json", report])
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(code, 2)
        self.assertNotIn(SECRET, out.getvalue())
        self.assertNotIn(SECRET, text)
        self.assertIn("${STUB_SECRET}", text)


if __name__ == "__main__":
    unittest.main()
