import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo  # noqa: E402

from plugin_test import checks, cli, model  # noqa: E402
from plugin_test.model import ADVISORY, BLOCKING  # noqa: E402


class CliL2Test(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("c-dev")
        self.seen = []

        def fake(plugin, ctx, manifest):
            self.seen.append(ctx)
            return []

        patcher = mock.patch.dict(checks.REGISTRY, {"eval-files": fake}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, *args, status=BLOCKING):
        out = io.StringIO()
        with mock.patch.dict("plugin_test.model.STATUS", {"eval-files": status}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["--repo", self.repo.root, *args])
        return code, out.getvalue()

    def test_default_checks_exclude_opt_in(self):
        self.assertEqual(set(model.DEFAULT_CHECKS), set(model.CHECK_IDS) - set(model.OPT_IN_CHECKS))
        self.assertEqual(model.OPT_IN_CHECKS, ("behavior",))
        with mock.patch.object(cli, "DEFAULT_CHECKS", ("eval-files",)):
            code, _ = self.run_cli()
        self.assertEqual((code, len(self.seen)), (0, 1))

    def test_state_dir_and_deadline_reach_context(self):
        state = os.path.join(self.repo.root, "state")
        code, _ = self.run_cli("--check", "eval-files", "--state-dir", state, "--deadline", "1791208800.5")
        self.assertEqual(code, 0)
        ctx = self.seen[0]
        self.assertEqual((ctx.state_dir, ctx.deadline, ctx.l2_stop), (os.path.abspath(state), 1791208800.5, ""))

    def test_defaults_without_flags(self):
        self.run_cli("--check", "eval-files")
        self.assertEqual((self.seen[0].state_dir, self.seen[0].deadline), ("", 0.0))

    def test_if_blocking_skips_advisory(self):
        code, out = self.run_cli("--check", "eval-files", "--if-blocking", status=ADVISORY)
        self.assertEqual((code, self.seen), (0, []))
        self.assertIn("advisory", out)

    def test_if_blocking_runs_blocking(self):
        code, _ = self.run_cli("--check", "eval-files", "--if-blocking", status=BLOCKING)
        self.assertEqual((code, len(self.seen)), (0, 1))


if __name__ == "__main__":
    unittest.main()
