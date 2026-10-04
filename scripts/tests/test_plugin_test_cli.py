import contextlib
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo  # noqa: E402

from plugin_test import checks, cli  # noqa: E402
from plugin_test.model import ADVISORY, FAIL, WARN, Finding  # noqa: E402


def fake_check(plugin, ctx, manifest):
    """Находит FAIL в каждом файле BROKEN.md плагина."""
    path = os.path.join(plugin.dir, "BROKEN.md")
    if os.path.exists(path):
        return [Finding(plugin.name, "skill-links", FAIL, "broken", plugin.rel(path), 1)]
    return []


def exploding_check(plugin, ctx, manifest):
    raise RuntimeError("boom")


def none_check(plugin, ctx, manifest):
    return None


class CliTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.init_git()
        self.repo.plugin("good-dev")
        self.repo.plugin("bad-dev", files={"BROKEN.md": "x"})
        self.base = self.repo.commit_all("base")
        patcher = mock.patch.dict(checks.REGISTRY, {"skill-links": fake_check}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Эти тесты проверяют механику CLI, а не политику статусов (она в
        # StatusPolicyTest): статус проверок-заглушек закреплён, а не берётся из STATUS.
        pin = mock.patch.dict("plugin_test.model.STATUS", {"skill-links": ADVISORY, "skill-snippets": ADVISORY})
        pin.start()
        self.addCleanup(pin.stop)

    def run_cli(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(["--repo", self.repo.root, *args])
        self.err = err.getvalue()
        return code, out.getvalue()

    def test_advisory_fail_is_warn_exit_2(self):
        code, out = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("WARN bad-dev [skill-links] plugins/bad-dev/BROKEN.md:1 — broken", out)

    def test_blocking_fail_exit_1(self):
        with mock.patch.dict("plugin_test.model.STATUS", {"skill-links": "blocking"}):
            code, _ = self.run_cli()
        self.assertEqual(code, 1)

    def test_plugin_filter_and_unknown(self):
        self.assertEqual(self.run_cli("--plugin", "good-dev")[0], 0)
        self.assertEqual(self.run_cli("--plugin", "ghost")[0], 1)

    def test_json_report(self):
        out = os.path.join(self.repo.root, "out", "report.json")
        self.run_cli("--json", out)
        with open(out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["plugins"], ["bad-dev", "good-dev"])
        self.assertEqual(data["findings"][0]["level"], WARN)
        self.assertEqual(data["findings"][0]["original"], FAIL)

    def test_changed_selects(self):
        self.repo.write("plugins/good-dev/skills/s/SKILL.md", "new")
        self.repo.commit_all("touch good")
        code, out = self.run_cli("--changed", self.base)
        self.assertEqual(code, 0)
        self.assertIn("plugin-test: 1 plugins", out)

    def test_changed_bad_base_falls_back(self):
        code, out = self.run_cli("--changed", "0" * 40)
        self.assertIn("--changed", out)
        self.assertIn("plugin-test: 2 plugins", out)
        self.assertEqual(code, 2)

    def test_skip_glob_suppresses(self):
        self.repo.tests("bad-dev", {"plugin-test.toml": '[skip]\n"skill-links" = ["BROKEN.md"]  # fixture\n'})
        out = os.path.join(self.repo.root, "r.json")
        code, _ = self.run_cli("--json", out)
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["summary"]["suppressed"], 1)

    def test_crashing_check_is_infra_and_run_continues(self):
        with mock.patch.dict(checks.REGISTRY, {"skill-snippets": exploding_check}):
            code, out = self.run_cli()
        self.assertIn("INFRA good-dev [skill-snippets]", out)
        self.assertIn("RuntimeError: boom", out)
        self.assertIn("WARN bad-dev [skill-links]", out)
        self.assertEqual(code, 2)

    def test_check_returning_none_is_infra_and_run_continues(self):
        with mock.patch.dict(checks.REGISTRY, {"skill-snippets": none_check}):
            code, out = self.run_cli()
        self.assertIn("INFRA good-dev [skill-snippets]", out)
        self.assertIn("WARN bad-dev [skill-links]", out)
        self.assertEqual(code, 2)

    def test_usage_errors_exit_1_not_2(self):
        self.assertEqual(self.run_cli("--check", "no-such-check")[0], 1)
        self.assertEqual(self.run_cli("--no-such-flag")[0], 1)
        self.assertIn("usage:", self.err)

    def test_help_exits_0(self):
        self.assertEqual(self.run_cli("--help")[0], 0)

    def test_env_file_missing(self):
        self.assertEqual(self.run_cli("--mode", "server", "--env-file", "/nonexistent/.env")[0], 1)

    def test_env_file_not_utf8(self):
        path = os.path.join(self.repo.root, "bad.env")
        with open(path, "wb") as fh:
            fh.write(b"A=\xff\n")
        code, _ = self.run_cli("--mode", "server", "--env-file", path)
        self.assertEqual(code, 1)
        self.assertIn("env-файл не читается: не UTF-8", self.err)
        self.assertNotIn("Traceback", self.err)


if __name__ == "__main__":
    unittest.main()
