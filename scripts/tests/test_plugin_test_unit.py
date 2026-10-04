import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, context, load_plugin, run_check  # noqa: E402

from plugin_test import manifest as manifest_mod  # noqa: E402
from plugin_test.checks import REGISTRY, unit  # noqa: E402
from plugin_test.model import CHECK_IDS, FAIL, INFRA, WARN  # noqa: E402


class UnitTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("u-dev", files={"tests/test_ok.py": "import unittest\n\nclass T(unittest.TestCase):\n"
                                                             "    def test_ok(self):\n        self.assertTrue(True)\n"})

    def check(self, toml):
        self.repo.tests("u-dev", {"plugin-test.toml": toml})
        return run_check(unit, self.repo.root, "u-dev")

    def test_registered(self):
        self.assertIs(REGISTRY["unit"], unit.run)

    def test_passing_suite_in_plugin_dir(self):
        self.assertEqual(self.check('[[unit]]\nrun = "python3 -m unittest discover -s tests"\nneeds = ["python3"]\n'), [])

    def test_cwd_from_repo_root(self):
        self.assertEqual(self.check('[[unit]]\nrun = "test -f .claude-plugin/plugin.json"\ncwd = "plugins/u-dev"\n'), [])

    def test_failure_tail_and_env_isolation(self):
        found = self.check('[[unit]]\nname = "noisy"\nrun = "for i in $(seq 1 30); do echo line$i; done; '
                           'echo home=$HOME; exit 4"\n')
        self.assertEqual([f.level for f in found], [FAIL])
        self.assertIn("noisy: код 4", found[0].message)
        self.assertIn("line30", found[0].message)
        self.assertNotIn("line5\n", found[0].message)
        self.assertNotIn("home=%s" % os.environ.get("HOME", "/nonexistent"), found[0].message)

    def test_missing_tool_and_dir(self):
        found = self.check('[[unit]]\nrun = "x"\nneeds = ["no-such-tool-xyz"]\n[[unit]]\nrun = "true"\ncwd = "nope"\n')
        self.assertEqual([f.level for f in found], [INFRA, FAIL])

    def test_timeout_is_fail(self):
        started = time.monotonic()
        found = self.check('[[unit]]\nrun = "sleep 30 & sleep 30"\ntimeout = 1\n')
        self.assertEqual([f.level for f in found], [FAIL])
        self.assertLess(time.monotonic() - started, 10)

    def test_invalid_utf8_output_is_a_fail_not_an_exception(self):
        found = self.check("[[unit]]\nrun = \"printf '\\\\377\\\\n'; exit 1\"\n")
        self.assertEqual([f.level for f in found], [FAIL])
        self.assertIn("код 1", found[0].message)


class BarePluginTest(unittest.TestCase):
    def test_all_checks_on_bare_plugin(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        repo.plugin("bare-dev")
        plugin = load_plugin(repo.root, "bare-dev")
        loaded, findings = manifest_mod.load(plugin)
        ctx = context(repo.root)
        self.assertEqual(set(REGISTRY), set(CHECK_IDS) - {"manifest"})
        for cid in CHECK_IDS:
            if cid in REGISTRY:
                findings += REGISTRY[cid](plugin, ctx, loaded)
        self.assertEqual([f for f in findings if f.level in (FAIL, WARN)], [])


if __name__ == "__main__":
    unittest.main()
